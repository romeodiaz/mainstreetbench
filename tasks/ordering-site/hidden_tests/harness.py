"""Black-box harness: run a submitted site and use it like customers, staff and strangers would.

The tickets give no field names or endpoints, so tests act through a real browser and find
controls by their visible labels. Amounts are read from the admin orders API, which existed
before the tickets. SITE_ROOT points at the site under test. The legacy database is always
built with the original starter code, never the submission.

Requires Playwright for Python and a Chromium build. Set CHROMIUM_PATH to use a specific binary.
"""

import datetime as dt
import glob
import os
import re
import shutil
import tempfile
import time
import unittest
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from sitectl import (FRIDAY, LEGACY_NOW, MONDAY, NOW, PASSWORD, SATURDAY, SITE, STARTER, SUNDAY, TASK, TODAY,  # noqa: F401
                     WAIT_MS, Site, build_legacy_db, free_port)


# --- reading times and money the way a person would ---------------------------------------------
TIME_PATTERN = re.compile(r"(?<![\d:])(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?(?![\d:])", re.I)


def times_in(text: str) -> list[str]:
    """Clock times written in text, as HH:MM, in order. A bare hour needs am/pm; 1:00–6:59 without
    am/pm is afternoon."""
    found = []
    for hour, minute, meridiem in TIME_PATTERN.findall(text or ""):
        hour = int(hour)
        if not minute and not meridiem:
            continue
        minute = int(minute or 0)
        if meridiem:
            if hour > 12:
                continue
            hour = hour % 12 + (12 if meridiem.lower().startswith("p") else 0)
        elif hour < 7:
            hour += 12
        if hour < 24 and minute < 60:
            found.append(f"{hour:02d}:{minute:02d}")
    return found


def slot_named(text: str, wanted: str) -> bool:
    """A slot is named by its start: the first time in its label ("7:00–7:30" is the 7:00 slot)."""
    times = times_in(text)
    return bool(times) and times[0] == wanted


def date_forms(iso: str) -> list[str]:
    day = dt.date.fromisoformat(iso)
    return [iso, day.strftime("%m/%d/%Y"), f"{day.month}/{day.day}", day.strftime("%B %-d"), day.strftime("%b %-d")]


@dataclass
class Attempt:
    placed: bool
    order_id: int | None = None
    url: str = ""
    text: str = ""
    reason: str = ""
    page: object = None
    context: object = field(default=None, repr=False)
    checkout_text: str = ""


class Shopper:
    """Drives the site in a browser. Each call to order() uses a fresh browser session."""

    def __init__(self, browser, site: Site):
        self.browser = browser
        self.site = site
        self.contexts = []

    def close(self):
        for context in self.contexts:
            try:
                context.close()
            except PlaywrightError:
                pass

    def new_page(self):
        context = self.browser.new_context(timezone_id="UTC", base_url=self.site.base)
        context.set_default_timeout(WAIT_MS)
        context.clock.set_fixed_time(dt.datetime.fromisoformat(NOW).replace(tzinfo=dt.timezone.utc))
        self.contexts.append(context)
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        return context, page

    @staticmethod
    def control(page, label: re.Pattern, exclude: re.Pattern | None = None):
        controls = page.get_by_label(label)
        for index in range(controls.count()):
            candidate = controls.nth(index)
            try:
                if not candidate.is_visible():
                    continue
                name = candidate.evaluate("e => (e.labels && e.labels[0] ? e.labels[0].innerText : '') + ' ' + "
                                          "(e.getAttribute('aria-label') || '') + ' ' + (e.name || '')")
            except PlaywrightError:
                continue
            if exclude is None or not exclude.search(name):
                return candidate
        return None

    def choose_date(self, page, iso: str) -> bool:
        control = self.control(page, re.compile(r"\b(date|day)\b", re.I), exclude=re.compile(r"time|quantity", re.I))
        if control is None:
            return False
        tag = control.evaluate("e => e.tagName.toLowerCase()")
        if tag == "select":
            for option in control.locator("option").all():
                value, text = option.get_attribute("value") or "", option.inner_text()
                if value == iso or any(form in text for form in date_forms(iso)):
                    control.select_option(value=value)
                    return True
            return False
        control.fill(iso)
        control.dispatch_event("change")
        control.blur()
        return True

    def choose_time(self, page, wanted: str, required: bool) -> bool | None:
        """True if chosen, False if the site offers no way to choose it, None if there's no time picker."""
        label = re.compile(r"time", re.I)
        deadline = time.time() + 3
        while True:
            control = self.control(page, label)
            radios = page.get_by_role("radio")
            if control is not None or radios.count():
                break
            if time.time() > deadline:
                return False if required else None
            page.wait_for_timeout(100)
        if control is not None:
            tag = control.evaluate("e => e.tagName.toLowerCase()")
            kind = control.evaluate("e => (e.type || '').toLowerCase()")
            if tag == "input" and kind == "time":
                control.fill(wanted)
                return True
            if tag == "select":
                deadline = time.time() + 3
                while time.time() < deadline:
                    for option in control.locator("option").all():
                        # Playwright's is_disabled() ignores <option disabled>; ask the DOM.
                        if option.evaluate("o => o.disabled || (o.parentElement && o.parentElement.disabled)"):
                            continue
                        value, text = option.get_attribute("value") or "", option.inner_text()
                        if slot_named(text, wanted) or slot_named(value, wanted) or value == wanted:
                            control.select_option(value=value)
                            return control.input_value() == value
                    page.wait_for_timeout(150)
                return False
        for index in range(radios.count()):
            radio = radios.nth(index)
            name = radio.evaluate("e => (e.labels && e.labels[0] ? e.labels[0].innerText : '') + ' ' + e.value")
            if slot_named(name, wanted) and radio.is_enabled():
                radio.check()
                return True
        for button in page.get_by_role("button").all():
            if slot_named(button.inner_text(), wanted) and button.is_enabled():
                button.click()
                return True
        return False

    @staticmethod
    def settle(page, ms: int = 600) -> None:
        page.wait_for_timeout(ms)
        page.wait_for_load_state("networkidle")

    def edit_line(self, page, product_name: str, qty: int) -> bool:
        """Change a cart line at checkout the way a customer would: a quantity box, +/- buttons,
        or a remove button. Returns False if the page offers no way to do it."""
        name = re.compile(re.escape(product_name), re.I)
        box = page.get_by_role("spinbutton", name=name)
        rows = page.locator("tr, li, [role=row], .line, .cart-line").filter(has_text=name)
        row = rows.last if rows.count() else None
        if not box.count() and row is not None:
            box = row.get_by_role("spinbutton")
        if box.count():
            box.first.fill(str(qty))
            box.first.dispatch_event("change")   # the cart may re-render, detaching this box
            self.settle(page)
            return True
        if row is None:
            return False
        if qty == 0:
            remove = row.get_by_role("button", name=re.compile(r"remove|delete|×|✕|trash", re.I))
            if remove.count():
                remove.first.click()
                self.settle(page)
                return True
        current = re.search(r"(\d+)\s*×|×\s*(\d+)|qty:?\s*(\d+)", row.inner_text(), re.I)
        count = next((int(g) for g in current.groups() if g), None) if current else None
        if count is None:
            return False
        step = re.compile(r"^\s*(\+|plus|increase|more|add one)\s*$" if qty > count else
                          r"^\s*(−|-|–|minus|decrease|less|fewer|remove one)\s*$", re.I)
        button = row.get_by_role("button", name=step)
        if not button.count():
            return False
        for _ in range(abs(qty - count)):
            button.first.click()
            page.wait_for_timeout(100)
        self.settle(page)
        return True

    def menu_for_day(self, iso: str):
        """Open the menu and choose the pickup day there, as a customer planning an order would."""
        context, page = self.new_page()
        page.goto("/")
        before = page.url
        if not self.choose_date(page, iso):
            return None
        self.settle(page, 300)
        if page.url == before:
            go = page.get_by_role("button", name=re.compile(r"show|check|update|see|go|apply|view", re.I))
            if go.count():
                go.first.click()
        self.settle(page)
        return page

    def order(self, items, date=SATURDAY, slot="10:00", promo=None, gift=None, name="Ana Lopez",
              require_time=False, edits=(), inspect=False) -> Attempt:
        """Place an order through the site. `edits` are (product name, new quantity) changes made at
        checkout; with `inspect`, the checkout page text just before ordering is kept."""
        context, page = self.new_page()
        page.goto("/")
        for sku, qty in items:
            row = page.locator(f'[data-sku="{sku}"]').first
            button = row.get_by_role("button", name=re.compile(r"add", re.I))
            if not row.count() or not button.count() or not button.first.is_enabled():
                return Attempt(False, reason=f"could not add {sku}", context=context, page=page,
                               text=page.inner_text("body"))
            for _ in range(qty):
                button.first.click()
        page.goto("/checkout")
        self.settle(page, 300)
        for product_name, qty in edits:
            if not self.edit_line(page, product_name, qty):
                return Attempt(False, reason=f"could not change {product_name} in the cart", context=context, page=page)
        filled = {
            re.compile(r"^\s*(your\s+|full\s+)?name", re.I): name,
            re.compile(r"e-?mail", re.I): "ana@example.com",
            re.compile(r"phone", re.I): "555-0100",
        }
        for label, value in filled.items():
            control = self.control(page, label, exclude=re.compile(r"gift|promo|coupon", re.I))
            if control is not None:
                control.fill(value)
        if not self.choose_date(page, date):
            return Attempt(False, reason="no pickup date control", context=context, page=page)
        chosen = self.choose_time(page, slot, require_time)
        if chosen is False:
            return Attempt(False, reason=f"pickup time {slot} not offered", context=context, page=page,
                           text=page.inner_text("body"))
        for value, label in ((promo, r"promo|coupon|discount"), (gift, r"gift")):
            if value:
                control = self.control(page, re.compile(label, re.I))
                if control is None:
                    return Attempt(False, reason=f"no field for {label}", context=context, page=page)
                control.fill(value)
                control.dispatch_event("change")
                apply = page.get_by_role("button", name=re.compile(r"^\s*apply", re.I))
                if apply.count() == 1 and apply.first.is_enabled():
                    apply.first.click()
        checkout_text = ""
        if inspect:
            self.settle(page, 1000)
            checkout_text = page.inner_text("body")
        submit = page.get_by_role("button", name=re.compile(r"place|order|submit|checkout|pay|confirm", re.I))
        if not submit.count():
            return Attempt(False, reason="no submit button", context=context, page=page)
        submit.last.click()
        try:
            page.wait_for_url(re.compile(r"/order/\d+"), timeout=WAIT_MS)
        except PlaywrightTimeout:
            return Attempt(False, reason="order not placed", context=context, page=page,
                           text=page.inner_text("body"), checkout_text=checkout_text)
        page.wait_for_load_state("networkidle")
        order_id = int(re.search(r"/order/(\d+)", page.url).group(1))
        return Attempt(True, order_id, page.url, page.inner_text("body"), page=page, context=context,
                       checkout_text=checkout_text)

    def cancel(self, page, url: str) -> None:
        """Try to cancel from an order page; does nothing if the page offers no way to cancel."""
        page.goto(url)
        page.wait_for_load_state("networkidle")
        for _ in range(2):
            control = page.get_by_role("button", name=re.compile(r"cancel", re.I))
            if not control.count():
                control = page.get_by_role("link", name=re.compile(r"cancel", re.I))
            if not control.count() or not control.first.is_enabled():
                break
            control.first.click()
            page.wait_for_timeout(300)
            page.wait_for_load_state("networkidle")
            confirm = page.get_by_role("button", name=re.compile(r"yes|confirm", re.I))
            if confirm.count() and confirm.first.is_enabled():
                confirm.first.click()
                page.wait_for_load_state("networkidle")
            break

    def stranger_cancel(self, order_id: int) -> None:
        context, page = self.new_page()
        self.cancel(page, f"/order/{order_id}")


def gift_codes(text: str) -> list[str]:
    """Possible gift card codes on a page, most likely first: tokens of 6+ characters that are
    all capitals/digits or mix letters and digits, then long card numbers. Dates, phone numbers
    and ordinary words are skipped."""
    lettered, numeric = [], []
    for token in re.findall(r"(?<![\w-])[A-Za-z0-9][A-Za-z0-9-]{4,}[A-Za-z0-9](?![\w-])", text):
        bare = token.replace("-", "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}|\d{3}-\d{3}-\d{4}", token) or len(bare) < 6:
            continue
        if bare.isdigit():
            if len(bare) >= 8 and token not in numeric:
                numeric.append(token)
        elif (bare.isupper() or re.search(r"\d", bare)) and token not in lettered:
            lettered.append(token)
    return lettered + numeric


def money_in(text: str) -> set[Decimal]:
    return {Decimal(m.replace(",", "")) for m in re.findall(r"\$\s?(\d[\d,]*\.\d{2})", text)}


class SiteCase(unittest.TestCase):
    """Fresh site, database and browser sessions per test; one browser per class."""

    db_source: Path | None = None

    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        executable = os.environ.get("CHROMIUM_PATH") or next(
            iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))), None)
        options = {"args": ["--disable-background-networking", "--disable-component-update", "--no-first-run"]}
        if executable:
            options["executable_path"] = executable
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db = self.tmp / "bakery.db"
        if self.db_source is not None:
            shutil.copy(self.db_source, self.db)
        self.site = Site(SITE, self.db)
        self.shopper = Shopper(self.browser, self.site)

    def tearDown(self):
        self.shopper.close()
        self.site.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def call(self, *args, **kwargs):
        return self.site.call(*args, **kwargs)

    def order(self, items=(("BREAD9", 2),), **kwargs) -> Attempt:
        return self.shopper.order(items, **kwargs)

    def placed(self, items=(("BREAD9", 2),), **kwargs) -> Attempt:
        attempt = self.order(items, **kwargs)
        self.assertTrue(attempt.placed, f"Order was not placed: {attempt.reason} {attempt.text[-300:]}")
        return attempt

    def refused(self, items=(("BREAD9", 2),), **kwargs) -> Attempt:
        before = len(self.admin_orders())
        attempt = self.order(items, **kwargs)
        self.assertFalse(attempt.placed, "Order should not have been accepted")
        self.assertEqual(len(self.admin_orders()), before, "A refused order was saved anyway")
        return attempt

    def staff_activate(self, order_id: int) -> bool:
        """Do what staff would if a gift card isn't live yet: on the orders page, press the order's
        activate / mark-paid button. Returns False if the site has no such step."""
        context = self.browser.new_context(base_url=self.site.base, timezone_id="UTC",
                                           http_credentials={"username": "staff", "password": PASSWORD})
        try:
            context.set_default_timeout(WAIT_MS)
            context.clock.set_fixed_time(dt.datetime.fromisoformat(NOW).replace(tzinfo=dt.timezone.utc))
            page = context.new_page()
            page.on("dialog", lambda dialog: dialog.accept())
            page.goto("/admin")
            row = page.locator(f'[data-order-id="{order_id}"]').first
            pattern = re.compile(r"activat|paid|payment|collect", re.I)
            control = row.get_by_role("button", name=pattern)
            if not control.count():
                control = row.get_by_role("link", name=pattern)
            if not control.count() or not control.first.is_enabled():
                return False
            control.first.click()
            page.wait_for_timeout(300)
            page.wait_for_load_state("networkidle")
            return True
        finally:
            context.close()

    def spend_gift_card(self, bought: Attempt, items=(("BREAD9", 2),), **kwargs):
        """Pay with the gift card bought in `bought`, trying each code its order page shows. If none
        works yet, let staff activate the card (pay-at-pickup sites may require it) and try again."""
        attempt = None
        for round_ in range(2):
            bought.page.goto(bought.url)
            bought.page.wait_for_load_state("networkidle")
            for code in gift_codes(bought.page.inner_text("body")):
                attempt = self.order(items, gift=code, **kwargs)
                if attempt.placed:
                    return code, attempt
            if round_ == 0 and not self.staff_activate(bought.order_id):
                break
        return None, attempt

    def admin_orders(self) -> list:
        status, data = self.call("GET", "/admin/api/orders", admin=True)
        self.assertEqual(status, 200)
        return data["orders"]

    def saved(self, order_id: int) -> dict:
        return {o["id"]: o for o in self.admin_orders()}[order_id]

    def assertMoney(self, actual, expected: str, label: str = ""):
        self.assertIsInstance(actual, (int, float), label)
        self.assertEqual(Decimal(str(actual)), Decimal(expected), label)


class LegacyCase(SiteCase):
    """Fresh copy of a database created by the original site, with existing orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.legacy_dir = Path(tempfile.mkdtemp())
        cls.db_source = cls.legacy_dir / "legacy.db"
        cls.legacy_orders = build_legacy_db(cls.db_source)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.legacy_dir, ignore_errors=True)
        super().tearDownClass()
