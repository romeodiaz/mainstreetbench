#!/usr/bin/env python3
"""Reproducible, synthetic retail-reconciliation fixture for Main Street Bench.

The September packet is solver-visible. The answer keys are evaluator-only.
All expectations follow information supplied in the packet; there are no
corrections that require knowledge of hidden intent.

v0.2 design goals: the bookkeeper's notes describe the exports and reporting
definitions but do not enumerate edge cases; edge cases recur several times at
random positions among ~1,000 orders, with harmless noise in the notes columns,
so the solver must build general, robust logic rather than follow a checklist.
Each keyed instance is scored separately.

Python standard library only. By default writes beneath the repository root.
Use --output-root /tmp/retail-fixture-check to regenerate without changing it.
"""

from __future__ import annotations

import argparse
import calendar
import copy
import csv
import datetime as dt
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


DEFAULT_SEED = 20260930
DEFAULT_ORDERS = 1000
CLOSE_MONTH = "2026-09"
VERSION = "0.2"
TASK_ID = "retail-reconciliation"
BANK_HOLIDAYS = {"2026-09-07", "2026-10-12"}
ORDER_COLUMNS = [
    "line_id", "order_id", "record_version", "ordered_at", "customer_id",
    "customer_name", "customer_email", "customer_phone", "sku", "product_name",
    "quantity", "unit_price", "discount_amount", "tax_amount", "line_total", "notes",
]
PAYMENT_COLUMNS = [
    "payment_id", "order_id", "payment_at", "tender", "status", "amount", "fee",
    "settled_at", "reference", "notes",
]
REFUND_COLUMNS = [
    "refund_id", "order_id", "line_id", "requested_at", "completed_at", "status",
    "quantity", "refund_sales", "refund_tax", "refund_total", "tender",
    "fee_adjustment", "settled_at", "notes",
]
CUSTOMER_COLUMNS = ["customer_id", "customer_name", "email", "phone", "loyalty_reference"]
PRODUCT_COLUMNS = ["sku", "product_name", "catalog_price", "category", "tax_rate"]
PRODUCTS = [
    {"sku": "BREAD9", "product_name": "Sourdough Loaf", "price": 900, "category": "merchandise"},
    {"sku": "BAGUETTE5", "product_name": "Baguette", "price": 500, "category": "merchandise"},
    {"sku": "CROISSANT21", "product_name": "Croissant Box (6)", "price": 2100, "category": "merchandise"},
    {"sku": "MUFFIN15", "product_name": "Muffin Box (4)", "price": 1500, "category": "merchandise"},
    {"sku": "CAKE48", "product_name": "Birthday Cake", "price": 4800, "category": "merchandise"},
    {"sku": "PIE32", "product_name": "Seasonal Pie", "price": 3200, "category": "merchandise"},
    {"sku": "COFFEE18", "product_name": "Coffee Beans 1lb", "price": 1800, "category": "merchandise"},
    {"sku": "CATER120", "product_name": "Catering Tray", "price": 12000, "category": "merchandise"},
    {"sku": "COOKIE12", "product_name": "Cookie Box (12)", "price": 1200, "category": "merchandise"},
    {"sku": "GRANOLA11", "product_name": "Granola Jar", "price": 1100, "category": "merchandise"},
    {"sku": "GIFT25", "product_name": "$25 Gift Card", "price": 2500, "category": "gift_card"},
]
BY_SKU = {p["sku"]: p for p in PRODUCTS}
MERCHANDISE = [p["sku"] for p in PRODUCTS if p["category"] == "merchandise"]
LARGE_ITEMS = {"CAKE48", "PIE32", "CATER120"}
FIRST_NAMES = [
    "Maria", "James", "Priya", "Daniel", "Aisha", "Tom", "Keiko", "Luis", "Grace", "Omar",
    "Hannah", "Victor", "Nina", "Ravi", "Elena", "Marcus", "Sofia", "Ben", "Fatima", "Leo",
    "Ivy", "Carlos", "Megan", "Theo", "Zara", "Noah", "Lily", "Jonah", "Rosa", "Ethan",
    "Mei", "Diego", "Chloe", "Samir", "Ada", "Felix", "Yara", "Owen", "Lucia", "Kofi",
]
LAST_NAMES = [
    "Lopez", "Chen", "Patel", "Okafor", "Rahman", "Walsh", "Tanaka", "Garcia", "Kim", "Haddad",
    "Brooks", "Nguyen", "Petrov", "Iyer", "Rossi", "Bell", "Costa", "Fischer", "Ali", "Moreau",
    "Reed", "Silva", "Hughes", "Park", "Khan", "Evans", "Dubois", "Grant", "Mendes", "Wright",
    "Liu", "Ramos", "Martin", "Shah", "Novak", "Larsen", "Mensah", "Byrne", "Sato", "Quinn",
]
# Households share an email and phone; explicit loyalty IDs still identify each person.
HOUSEHOLDS = {
    ("C014", "C015"): ("Alex Morgan", "Alex Morgan", "morgan.household@example.com", "555-010-1400"),
    ("C041", "C042"): ("Sam Ortiz", "Dana Ortiz", "ortiz.family@example.com", "555-010-4100"),
    ("C063", "C064"): ("Kim Nguyen", "Lee Nguyen", "nguyen.home@example.com", "555-010-6300"),
}
SAME_NAME = ("C027", "C058", "Chris Lee")
ORDER_NOTES = [
    "Birthday pickup", "Call on arrival", "No nuts please", "Slice the loaf", "Gift wrap",
    "Pre-order", "Pickup after 3pm", "Write 'Happy 40th'", "Staff to box separately", "Repeat weekly order",
]
CARD_NOTES = ["", "", "", "contactless", "chip", "swipe"]
DECLINE_NOTES = ["Do not honor", "Insufficient funds", "Card expired"]
REFUND_NOTES = ["Customer return", "Damaged item", "Wrong item packed", "Quality complaint"]
ORDER_FIELDS = ("customer_id", "sales_before_refunds", "amount_due", "captured_tenders")


def cents(value: object) -> int:
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def money(value: int) -> str:
    return f"{value / 100:.2f}"


def dollars(value: int) -> float:
    return float(Decimal(value) / 100)


def rounded_ratio(value: int, numerator: int, denominator: int) -> int:
    return int((Decimal(value) * numerator / denominator).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def card_fee(amount: int) -> int:
    return rounded_ratio(amount, 29, 1000) + 30


def stamp(moment: dt.datetime) -> str:
    # These are local store timestamps; no timezone conversion is required.
    return moment.strftime("%Y-%m-%dT%H:%M:%S")


def next_business_day(day: dt.date) -> dt.date:
    day += dt.timedelta(days=1)
    while day.weekday() >= 5 or day.isoformat() in BANK_HOLIDAYS:
        day += dt.timedelta(days=1)
    return day


def next_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{year + (number == 12):04d}-{number % 12 + 1:02d}"


def previous_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{year - (number == 1):04d}-{(number - 2) % 12 + 1:02d}"


def days_in(month: str) -> int:
    return calendar.monthrange(*map(int, month.split("-")))[1]


def digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def customers() -> list[dict[str, str]]:
    result = []
    for index in range(80):
        first = FIRST_NAMES[index % 40]
        last = LAST_NAMES[index % 40] if index < 40 else LAST_NAMES[(index + 7) % 40]
        number = index + 1
        result.append({
            "customer_id": f"C{number:03d}", "customer_name": f"{first} {last}",
            "email": f"{first}.{last}{number}@example.com".lower(),
            "phone": f"555-010-{number:04d}", "loyalty_reference": f"CL-{number:04d}",
        })
    by_id = {c["customer_id"]: c for c in result}
    for (first_id, second_id), (first_name, second_name, email, phone) in HOUSEHOLDS.items():
        for cid, name in ((first_id, first_name), (second_id, second_name)):
            by_id[cid].update(customer_name=name, email=email, phone=phone)
    for cid in SAME_NAME[:2]:
        number = int(cid[1:])
        by_id[cid].update(customer_name=SAME_NAME[2], email=f"chris.lee{number}@example.com")
    assert len({(c["email"], c["phone"]) for c in result}) == len(result) - len(HOUSEHOLDS)
    return result


def line_fields(sku: str, quantity: int, discount: int, price: int) -> dict[str, str]:
    net = price * quantity - discount
    tax = rounded_ratio(net, 8, 100) if BY_SKU[sku]["category"] == "merchandise" else 0
    return {"sku": sku, "product_name": BY_SKU[sku]["product_name"], "quantity": str(quantity),
            "unit_price": money(price), "discount_amount": money(discount),
            "tax_amount": money(tax), "line_total": money(net + tax)}


def bookkeeping_notes(month: str) -> str:
    month_name = dt.date.fromisoformat(month + "-01").strftime("%B %Y")
    prior_name = dt.date.fromisoformat(previous_month(month) + "-01").strftime("%B")
    return f"""# Corner Loaf Bakery — bookkeeper's notes

Close month: {month} ({month_name}, {month}-01 through {month}-{days_in(month):02d}).
All amounts are USD. All dates and times are store local time.
These are fictional training records, not real customers or financial data.

## The exports

- `orders.csv` is the register export, one row per order line. Every order in
  it was handed over to the customer. Staff can edit a line after ringing it
  up; the line keeps its `line_id` and the edit is exported again with a higher
  `record_version`. Our register exports overlap, so some rows appear more than
  once. Loyalty members are normally rung up with their customer ID, but staff
  sometimes skip it and type whatever contact details the customer gives, or
  note the loyalty card number. Walk-in customers usually give no details.
  The export also contains late-{prior_name} orders whose card charges paid out
  in {month_name}, and a few older {prior_name} orders that customers returned
  items from in {month_name}.
- `payments.csv` has register tenders (cash and gift card) and card terminal
  transactions, including attempts, with the status the terminal reported.
  Each transaction has its own `payment_id`; these exports overlap too.
  When the terminal is linked to the register, a charge carries the order
  number in `order_id` and `reference`; sometimes only the reference came
  through. Charges keyed on the standalone terminal show a `terminal:`
  reference and no order. `fee` is what the processor charged us. The
  processor pays card charges out on `settled_at`, the next business day.
- `refunds.csv` has refund requests from the register and processor, one per
  order line, with their outcome. Each request has its own `refund_id`; these
  exports overlap too. Amounts are what was approved for that line.
  `fee_adjustment` is any fee the processor gave back. Card refunds come out of
  the processor payout on `settled_at`.
- `customers.csv` is our loyalty register. Some households share an email and
  phone number.
- `products.csv` is today's catalog. Prices change and we run promotions; the
  price on the order is what the customer was charged. Product names typed at
  the register vary; the SKU is reliable.

## How we report a month

- **Sales** are merchandise quantity times the price charged, less line
  discounts, for orders placed in the month. Returns reduce sales in the month
  the refund is completed. **Net sales** are sales after discounts minus those
  returns. Sales exclude sales tax and gift-card sales.
- Sales tax is 8% of each discounted merchandise line, rounded to the cent per
  line. Gift cards carry no tax.
- Gift cards are stored value. Selling one creates a liability, not a sale;
  redeeming one pays for merchandise. We don't have the opening gift-card
  balance.
- **Card processing fees** are the fees on card charges accepted in the month.
- **Refunds** are card and cash refunds completed in the month.
- **Net external receipts** are the card and cash money we actually took in the
  month (by payment date), less card and cash refunds completed in the month.
  Gift-card redemptions are not new money.
- **Expected card payout** is what the processor should have deposited in the
  month: card charges that settled in the month less their fees, less card
  refunds that settled in the month plus any fee given back on them. There is
  no bank statement here, so this is an expectation, not a confirmed deposit.
- Product and customer rankings use net sales. Each order counts once.

## What I need flagged

Anything where the money taken doesn't match what was ordered, refunds that
didn't go through, and sales we can't tie to a customer. Use the order,
payment, or refund numbers. If the records don't show which order or customer
something belongs to, don't guess: keep the amount, show it separately, and
flag it.
"""


def build_packet(month: str, seed: int, count: int) -> dict:
    rng = random.Random(seed)
    roster = customers()
    by_id = {c["customer_id"]: c for c in roster}
    prefix = month.replace("-", "")
    prior = previous_month(month)
    future = next_month(month)
    last_day = days_in(month)
    prior_last = days_in(prior)
    orders: list[dict] = []
    payments: list[dict] = []
    refunds: list[dict] = []
    instances: list[dict] = []
    amendments: list[tuple[dict, list[tuple]]] = []
    duplicates: list[dict] = []
    filler: list[list[dict]] = []
    counter: Counter = Counter()

    def moment(day: int, of: str = month, start: int = 7, end: int = 17) -> dt.datetime:
        date = dt.date.fromisoformat(f"{of}-{day:02d}")
        return dt.datetime.combine(date, dt.time(rng.randint(start, end), rng.randint(0, 59)))

    def later(when: dt.datetime, low: int = 1, high: int = 4) -> dt.datetime:
        return when + dt.timedelta(minutes=rng.randint(low, high))

    def regular(*, exclude: set[str] = frozenset()) -> str:
        weights = [8 if n < 5 else 4 if n < 15 else 1 for n in range(len(roster))]
        while True:
            cid = rng.choices(roster, weights=weights)[0]["customer_id"]
            if cid not in exclude and cid not in {c for pair in HOUSEHOLDS for c in pair} | set(SAME_NAME[:2]):
                return cid

    def identity(cid: str | None, *, keep_id: bool = True, name: str | None = None,
                 email: str | None = None, phone: str | None = None) -> dict[str, str]:
        if cid is None:
            return {"customer_id": "", "customer_name": name or "", "customer_email": email or "",
                    "customer_phone": phone or ""}
        known = by_id[cid]
        return {"customer_id": cid if keep_id else "",
                "customer_name": known["customer_name"] if name is None else name,
                "customer_email": known["email"] if email is None else email,
                "customer_phone": known["phone"] if phone is None else phone}

    def random_specs(lines: int | None = None) -> list[tuple]:
        lines = lines or rng.choices([1, 2, 3, 4], weights=[4, 8, 4, 1])[0]
        specs = []
        for sku in rng.sample(MERCHANDISE, lines):
            quantity = rng.randint(1, 2) if sku in LARGE_ITEMS else rng.randint(1, 4)
            percentage = rng.choice([0] * 6 + [5, 10, 15])
            specs.append((sku, quantity, rounded_ratio(BY_SKU[sku]["price"] * quantity, percentage, 100), None))
        return specs

    def add_order(when: dt.datetime, ident: dict[str, str], specs: list[tuple]) -> list[dict]:
        counter["order"] += 1
        temp = f"T{counter['order']:05d}"
        rows = []
        for index, (sku, quantity, discount, price) in enumerate(specs, start=1):
            row = {"line_id": f"{temp}-L{index:02d}", "order_id": temp, "record_version": "1",
                   "ordered_at": stamp(when), **ident,
                   **line_fields(sku, quantity, discount, BY_SKU[sku]["price"] if price is None else price),
                   "notes": rng.choice(ORDER_NOTES) if rng.random() < 0.06 else ""}
            rows.append(row)
        if ident["customer_id"] and rng.random() < 0.05:
            rows[0]["notes"] = f"Loyalty card {by_id[ident['customer_id']]['loyalty_reference']} scanned"
        orders.extend(rows)
        return rows

    def due(rows: list[dict]) -> int:
        return sum(cents(r["line_total"]) for r in rows)

    def add_payment(rows: list[dict] | None, amount: int, when: dt.datetime, *, tender: str = "card",
                    status: str = "captured", link: str = "order", reference: str | None = None) -> dict:
        counter["payment"] += 1
        order_id = rows[0]["order_id"] if rows else ""
        card = tender == "card" and status == "captured"
        if status == "declined":
            notes = rng.choice(DECLINE_NOTES)
        else:
            notes = rng.choice(CARD_NOTES) if tender == "card" else ""
        payment = {
            "payment_id": f"PT{counter['payment']:05d}", "order_id": order_id if link == "order" else "",
            "payment_at": stamp(when), "tender": tender, "status": status, "amount": money(amount),
            "fee": money(card_fee(amount) if card else 0),
            "settled_at": next_business_day(when.date()).isoformat() if card else "",
            "reference": reference if reference is not None else (f"order:{order_id}" if order_id else ""),
            "notes": notes,
        }
        payments.append(payment)
        return payment

    def pay(rows: list[dict], when: dt.datetime, tender: str | None = None) -> dict:
        tender = tender or ("cash" if rng.random() < 0.22 else "card")
        return add_payment(rows, due(rows), later(when), tender=tender)

    def add_refund(row: dict, quantity: int, requested: dt.datetime, *, status: str = "succeeded",
                   completed: dt.datetime | None = None, tender: str = "card", adjustment: int = 0) -> dict:
        counter["refund"] += 1
        line_quantity = int(row["quantity"])
        sales = cents(row["unit_price"]) * line_quantity - cents(row["discount_amount"])
        refund_sales = rounded_ratio(sales, quantity, line_quantity)
        refund_tax = rounded_ratio(cents(row["tax_amount"]), quantity, line_quantity)
        if status == "succeeded" and completed is None:
            completed = requested + dt.timedelta(hours=rng.randint(1, 3))
        refund = {
            "refund_id": f"RT{counter['refund']:04d}", "order_id": row["order_id"], "line_id": row["line_id"],
            "requested_at": stamp(requested), "completed_at": stamp(completed) if status == "succeeded" else "",
            "status": status, "quantity": str(quantity), "refund_sales": money(refund_sales),
            "refund_tax": money(refund_tax), "refund_total": money(refund_sales + refund_tax), "tender": tender,
            "fee_adjustment": money(adjustment),
            "settled_at": next_business_day(completed.date()).isoformat()
            if status == "succeeded" and tender == "card" else "",
            "notes": rng.choice(REFUND_NOTES),
        }
        refunds.append(refund)
        return refund

    def instance(type_: str, kind: str, title: str, behavior: str, records: list, *,
                 check_orders: list[list[dict]] = (), check_refunds: list[dict] = (),
                 flag: bool = False, expect: list[tuple] = ()) -> None:
        instances.append({"type": type_, "kind": kind, "title": title, "behavior": behavior,
                          "records": records, "check_orders": list(check_orders),
                          "check_refunds": list(check_refunds), "flag": flag, "expect": list(expect)})

    def early_day() -> int:
        return rng.randint(1, last_day - 8)

    # --- Order-line edits and identity labels -------------------------------------------------
    for variant in ("quantity", "quantity", "sku", "discount", "void", "void", "three", "three"):
        cid = regular()
        when = moment(early_day())
        specs = random_specs(rng.randint(2, 3))
        sku, quantity, discount, price = specs[0]
        if variant == "quantity":
            older = [(sku, quantity + rng.randint(1, 2), 0, price)]
        elif variant == "sku":
            older = [(rng.choice([s for s in MERCHANDISE if s not in {x[0] for x in specs}]), quantity, 0, None)]
        elif variant == "discount":
            specs[0] = (sku, quantity, rounded_ratio(BY_SKU[sku]["price"] * quantity, 20, 100), price)
            older = [(sku, quantity, 0, price)]
        elif variant == "void":
            specs[0] = (sku, 0, 0, price)
            older = [(sku, quantity, discount, price)]
        else:
            older = [(sku, quantity + 2, 0, price), (sku, quantity + 1, 0, price)]
        rows = add_order(when, identity(cid), specs)
        amendments.append((rows[0], [(s, q, d, BY_SKU[s]["price"] if p is None else p) for s, q, d, p in older]))
        pay(rows, when)
        instance("line-edit", "resolve", "Edited order line",
                 f"Use only the latest version (v{len(older) + 1}) of the edited line; older versions are replaced, "
                 "not additional sales.", [rows[0]], check_orders=[rows])

    for _ in range(5):
        cid = regular()
        known = by_id[cid]
        first, last = known["customer_name"].split(" ", 1)
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(cid, name=rng.choice([f"{last}, {first}", f"{first[0]}. {last}",
                                                              known["customer_name"].upper()])), random_specs())
        rows[0]["product_name"] = rng.choice([rows[0]["product_name"].lower(), rows[0]["product_name"].upper(),
                                              rows[0]["product_name"] + " *"])
        pay(rows, when)
        instance("label-variant", "resolve", "Checkout and product label variants",
                 f"Aggregate under {cid} and {rows[0]['sku']} despite display-label variants; no new customer or product.",
                 [rows[0], cid], check_orders=[rows], expect=[(rows, "customer_id", cid)])

    for _ in range(5):
        when = moment(rng.randint(1, last_day))
        specs = random_specs(rng.randint(1, 2))
        sku, quantity = specs[0][:2]
        promo = BY_SKU[sku]["price"] - rounded_ratio(BY_SKU[sku]["price"], rng.choice([10, 15, 20, 25]), 100)
        promo -= promo % 5
        specs[0] = (sku, quantity, 0, promo)
        rows = add_order(when, identity(regular()), specs)
        pay(rows, when)
        instance("promotional-price", "preserve", "Recorded promotional price",
                 f"Keep the recorded {sku} price of ${money(promo)}; do not replace it with the catalog price.",
                 [rows[0]], check_orders=[rows])

    # --- Gift cards ---------------------------------------------------------------------------
    for variant in ("only", "only", "only", "mixed", "mixed", "mixed"):
        when = moment(rng.randint(1, last_day))
        cards = rng.randint(1, 4)
        specs = [("GIFT25", cards, 0, None)] + (random_specs(rng.randint(1, 2)) if variant == "mixed" else [])
        rows = add_order(when, identity(regular() if rng.random() < 0.7 else None), specs)
        pay(rows, when)
        instance("gift-card-sale", "resolve", "Gift-card sale",
                 f"Record ${money(cards * 2500)} as gift-card issuance with no sales or tax; it is still money received "
                 "and part of the amount due.", [rows[0]], check_orders=[rows])

    for variant in ("card", "card", "card", "cash", "card"):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular()), random_specs(rng.randint(2, 3)))
        redeemed = min(due(rows) - 100, rng.choice([1000, 1500, 2500, 2500]))
        add_payment(rows, redeemed, later(when), tender="gift_card")
        add_payment(rows, due(rows) - redeemed, later(when), tender=variant)
        instance("gift-card-redemption", "resolve", "Gift card plus another tender",
                 f"The ${money(redeemed)} gift-card redemption pays for merchandise; it is not new external money. "
                 "Order is fully paid.", [rows[0]], check_orders=[rows])

    # --- Payments -----------------------------------------------------------------------------
    for variant in ("same", "same", "twice", "same", "same"):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular() if rng.random() < 0.8 else None), random_specs())
        attempt = later(when)
        declined = [add_payment(rows, due(rows), attempt, status="declined")]
        if variant == "twice":
            declined.append(add_payment(rows, due(rows), later(attempt), status="declined"))
        captured = add_payment(rows, due(rows), later(attempt, 2, 6))
        instance("declined-then-captured", "resolve", "Declined attempt before an accepted charge",
                 "Declined attempts take no money and carry no fee; the accepted charge pays the order once.",
                 [rows[0], *declined, captured], check_orders=[rows], expect=[(rows, "captured_tenders", due(rows))])

    for variant in ("minutes", "minutes", "minutes", "next-day"):
        when = moment(rng.randint(1, last_day - 2))
        rows = add_order(when, identity(regular() if rng.random() < 0.8 else None), random_specs())
        first_at = later(when)
        first = add_payment(rows, due(rows), first_at)
        second_at = later(first_at, 1, 5) if variant == "minutes" \
            else first_at + dt.timedelta(days=1, minutes=rng.randint(5, 50))
        second = add_payment(rows, due(rows), second_at)
        instance("double-charge", "review", "Order charged twice",
                 f"Keep both accepted charges in receipts and payout and count the sale once; flag the ${money(due(rows))} "
                 "overpayment for the owner. Do not delete or invent a refund.",
                 [rows[0], first, second], check_orders=[rows], flag=True,
                 expect=[(rows, "captured_tenders", 2 * due(rows))])

    for _ in range(3):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular()), random_specs(rng.randint(2, 3)))
        split = rng.randint(30, 70) * due(rows) // 100
        first = add_payment(rows, split, later(when))
        second = add_payment(rows, due(rows) - split, later(when))
        instance("two-card-split", "preserve", "One order paid on two cards",
                 "Two accepted charges add up to the amount due; the order is paid exactly, not double-charged.",
                 [rows[0], first, second], check_orders=[rows], expect=[(rows, "captured_tenders", due(rows))])

    for variant in ("none", "none", "declined", "declined"):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular() if rng.random() < 0.8 else None), random_specs())
        records = [rows[0]]
        if variant == "declined":
            records.append(add_payment(rows, due(rows), later(when), status="declined"))
        instance("missing-payment", "review", "Fulfilled order with no accepted payment",
                 f"Keep the sale and flag the ${money(due(rows))} amount due as unpaid; do not invent a payment.",
                 records, check_orders=[rows], flag=True, expect=[(rows, "captured_tenders", 0)])

    for _ in range(3):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular() if rng.random() < 0.6 else None), random_specs(rng.randint(2, 3)))
        short = rng.randint(1, 10) * 100
        tender = add_payment(rows, due(rows) - short, later(when), tender="cash")
        instance("short-payment", "review", "Order paid less than the amount due",
                 f"Keep the sale and flag the ${money(short)} unpaid balance.",
                 [rows[0], tender], check_orders=[rows], flag=True, expect=[(rows, "captured_tenders", due(rows) - short)])

    for _ in range(5):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular() if rng.random() < 0.8 else None), random_specs())
        linked = add_payment(rows, due(rows), later(when), link="reference")
        instance("reference-link", "resolve", "Charge linked only through its reference",
                 "Link the charge to the order through its order:<order_id> reference; it is not unmatched.",
                 [rows[0], linked], check_orders=[rows], expect=[(rows, "captured_tenders", due(rows))])

    for _ in range(3):
        amount = rng.randint(1500, 9000)
        charge = add_payment(None, amount, moment(rng.randint(1, last_day)),
                             reference=f"terminal:{rng.randrange(16 ** 6):06x}")
        instance("unlinked-charge", "review", "Accepted charge without an order",
                 f"Keep the ${money(amount)} charge and its fee in card receipts and payout, create no sale, and flag it.",
                 [charge], flag=True)

    for _ in range(2):
        day = rng.randint(1, last_day - 6)
        rows = add_order(moment(day), identity(regular() if rng.random() < 0.5 else None), random_specs())
        charge = add_payment(None, due(rows), moment(day + rng.randint(2, 5)),
                             reference=f"terminal:{rng.randrange(16 ** 6):06x}")
        instance("coincidental-amount", "review", "Unlinked charge equal to an unpaid order",
                 "The amounts match but nothing links the charge to the order. Keep the order unpaid and the charge "
                 "unmatched, and flag both for the owner to confirm.",
                 [rows[0], charge], check_orders=[rows], flag=True, expect=[(rows, "captured_tenders", 0)])

    # --- Refunds ------------------------------------------------------------------------------
    def refundable(tender: str = "card", identity_: dict | None = None, day: int | None = None,
                   lines: int | None = None) -> tuple[list[dict], dt.datetime]:
        when = moment(day or early_day())
        specs = random_specs(lines or rng.randint(2, 3))
        sku = rng.choice([s for s in MERCHANDISE if s not in LARGE_ITEMS and s not in {x[0] for x in specs}])
        quantity = rng.randint(2, 4)
        specs[0] = (sku, quantity, rounded_ratio(BY_SKU[sku]["price"] * quantity, rng.choice([0, 10, 15]), 100), None)
        rows = add_order(when, identity_ or identity(regular()), specs)
        pay(rows, when, tender)
        return rows, when

    def after(when: dt.datetime, low: int = 1, high: int = 6) -> dt.datetime:
        target = min(when.date() + dt.timedelta(days=rng.randint(low, high)),
                     dt.date.fromisoformat(f"{month}-{last_day:02d}"))
        return dt.datetime.combine(target, dt.time(rng.randint(9, 16), rng.randint(0, 59)))

    for _ in range(5):
        tender = rng.choice(["card", "card", "cash"])
        rows, when = refundable(tender)
        refund = add_refund(rows[0], rng.randint(1, int(rows[0]["quantity"]) - 1), after(when), tender=tender,
                            adjustment=30 if tender == "card" and rng.random() < 0.4 else 0)
        instance("partial-refund", "resolve", "Partial return of a discounted line",
                 f"Deduct only the returned quantity: ${refund['refund_sales']} sales and ${refund['refund_tax']} tax; "
                 "the rest of the order stays sold.", [rows[0], refund], check_orders=[rows], check_refunds=[refund])

    for _ in range(3):
        rows, when = refundable("cash")
        refund = add_refund(rows[0], int(rows[0]["quantity"]), after(when), tender="cash")
        instance("cash-refund", "resolve", "Cash return",
                 f"Deduct ${refund['refund_sales']} sales; the ${refund['refund_total']} cash refund reduces cash, "
                 "not the card payout.", [rows[0], refund], check_orders=[rows], check_refunds=[refund])

    for status in ("failed", "failed", "failed", "pending", "pending"):
        rows, when = refundable()
        refund = add_refund(rows[0], rng.randint(1, int(rows[0]["quantity"])), after(when), status=status)
        instance("refund-not-paid", "review", f"Refund request {status}",
                 f"The {status} ${refund['refund_total']} refund moved no money and does not reduce sales or units; "
                 "flag it for follow-up.", [rows[0], refund], check_orders=[rows], check_refunds=[refund], flag=True)

    for variant in ("settles-later", "settles-later", "completes-later", "completes-later"):
        rows, when = refundable(day=rng.randint(last_day - 9, last_day - 3))
        requested = dt.datetime.combine(dt.date.fromisoformat(f"{month}-{last_day:02d}"), dt.time(rng.randint(9, 12)))
        completed = requested + dt.timedelta(hours=2) if variant == "settles-later" \
            else dt.datetime.combine(dt.date.fromisoformat(f"{future}-01"), dt.time(10, rng.randint(0, 59)))
        refund = add_refund(rows[0], 1, requested, completed=completed)
        behavior = (f"Completed in {month}: deduct ${refund['refund_sales']} sales and count the refund as paid out, "
                    f"but it settles {refund['settled_at']} so it is outside {month}'s expected payout."
                    if variant == "settles-later" else
                    f"Completed in {future}: no {month} sales deduction, refund paid out or payout effect.")
        instance("refund-timing", "resolve", "Month-end refund timing", behavior, [rows[0], refund],
                 check_orders=[rows], check_refunds=[refund])

    for _ in range(3):
        when = moment(rng.randint(8, prior_last - 6), of=prior)
        specs = random_specs(rng.randint(1, 3))
        rows = add_order(when, identity(regular()), specs)
        pay(rows, when, "card")
        refund = add_refund(rows[0], rng.randint(1, int(rows[0]["quantity"])), moment(early_day(), start=9, end=16))
        instance("prior-month-return", "resolve", f"Return of a {prior} sale",
                 f"The original {prior} sale and charge are not {month} activity, but the ${refund['refund_sales']} "
                 f"return completed in {month} reduces {month} net sales.", [rows[0], refund], check_refunds=[refund])

    for _ in range(2):
        rows, when = refundable()
        sku, quantity = rows[0]["sku"], int(rows[0]["quantity"])
        amendments.append((rows[0], [(sku, quantity - 1, 0, cents(rows[0]["unit_price"]))]))
        refund = add_refund(rows[0], 1, after(when))
        instance("refund-on-edited-line", "resolve", "Return against an edited line",
                 f"The refund applies to the latest line version; deduct ${refund['refund_sales']} sales once.",
                 [rows[0], refund], check_orders=[rows], check_refunds=[refund])

    for _ in range(2):
        rows, when = refundable()
        refund = add_refund(rows[0], 1, after(when))
        duplicates.append(refund)
        instance("duplicate-export", "resolve", "Refund exported twice",
                 f"Count the refund ID once: ${refund['refund_sales']} sales.",
                 [rows[0], refund], check_orders=[rows], check_refunds=[refund])

    # --- Customer identity --------------------------------------------------------------------
    for variant in ("email", "email", "email-upper", "email-upper"):
        cid = regular()
        known = by_id[cid]
        email = known["email"].upper() if variant == "email-upper" else known["email"]
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(cid, keep_id=False, name=known["customer_name"].split()[0], email=email, phone=""),
                         random_specs())
        pay(rows, when)
        instance("id-from-email", "resolve", "Missing ID recovered from a unique email",
                 f"The email matches exactly one loyalty member; attribute the order to {cid}.", [rows[0], cid],
                 check_orders=[rows], expect=[(rows, "customer_id", cid)])

    for _ in range(3):
        cid = regular()
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(cid, keep_id=False, name="", email="", phone=""), random_specs())
        for row in rows:
            row["notes"] = f"Loyalty card {by_id[cid]['loyalty_reference']} scanned"
        pay(rows, when)
        instance("id-from-loyalty-card", "resolve", "Missing ID recovered from a loyalty card note",
                 f"The noted loyalty card identifies {cid}.", [rows[0], cid], check_orders=[rows],
                 expect=[(rows, "customer_id", cid)])

    for _ in range(2):
        cid = regular()
        known = by_id[cid]
        typo = known["email"].replace("@example.com", "@exmaple.com")
        area, exchange, line = known["phone"].split("-")
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(cid, keep_id=False, email=typo, phone=f"({area}) {exchange}-{line}"),
                         random_specs())
        pay(rows, when)
        instance("id-from-phone", "resolve", "Mistyped email, unique phone",
                 f"The email matches no one; the phone number uniquely identifies {cid}.", [rows[0], cid],
                 check_orders=[rows], expect=[(rows, "customer_id", cid)])

    households = list(HOUSEHOLDS.items())
    for (first_id, second_id), (first_name, second_name, email, phone) in households:
        when = moment(rng.randint(1, last_day))
        surname = first_name.split()[-1]
        # Any name shown must fit both members, or it would identify one of them.
        names = [surname] + ([first_name, f"{first_name[0]}. {surname}"] if first_name == second_name else [])
        rows = add_order(when, identity(None, name=rng.choice(names), email=email, phone=phone), random_specs())
        pay(rows, when)
        instance("ambiguous-household", "review", "Missing ID with shared household contacts",
                 f"The contacts fit both {first_id} and {second_id}. Keep the sale but leave it unassigned and flag it.",
                 [rows[0], first_id, second_id], check_orders=[rows], flag=True,
                 expect=[(rows, "customer_id", "NONE")])

    for _ in range(2):
        first_id = regular()
        second_id = regular(exclude={first_id})
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(None, email=by_id[first_id]["email"], phone=by_id[second_id]["phone"]),
                         random_specs())
        pay(rows, when)
        instance("conflicting-contacts", "review", "Email and phone point to different members",
                 f"The email matches {first_id} but the phone matches {second_id}. Leave it unassigned and flag it.",
                 [rows[0], first_id, second_id], check_orders=[rows], flag=True,
                 expect=[(rows, "customer_id", "NONE")])

    for (first_id, second_id), _ in households:
        pair = []
        for cid in (first_id, second_id):
            when = moment(rng.randint(1, last_day))
            rows = add_order(when, identity(cid), random_specs())
            pay(rows, when)
            pair.append(rows)
        instance("household-members", "preserve", "Household members with explicit IDs",
                 f"Explicit IDs keep {first_id} and {second_id} separate despite shared contacts.",
                 [pair[0][0], pair[1][0], first_id, second_id], check_orders=pair,
                 expect=[(pair[0], "customer_id", first_id), (pair[1], "customer_id", second_id)])

    pair = []
    for cid in SAME_NAME[:2]:
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(cid), random_specs())
        pay(rows, when)
        pair.append(rows)
    instance("same-name", "preserve", "Two members with the same name",
             f"{SAME_NAME[0]} and {SAME_NAME[1]} are different people with different contacts; do not merge.",
             [pair[0][0], pair[1][0], *SAME_NAME[:2]], check_orders=pair,
             expect=[(pair[0], "customer_id", SAME_NAME[0]), (pair[1], "customer_id", SAME_NAME[1])])

    for _ in range(4):
        cid = regular()
        day = rng.randint(1, last_day)
        specs = random_specs()
        tender = rng.choice(["card", "cash"])
        pair = []
        first_at = moment(day, start=8, end=15)
        for when in (first_at, first_at + dt.timedelta(minutes=rng.randint(4, 40))):
            rows = add_order(when, identity(cid), specs)
            pay(rows, when, tender)
            pair.append(rows)
        instance("repeat-purchase", "preserve", "Identical repeat purchases",
                 "Two order numbers, each separately paid: two real purchases. Keep both.",
                 [pair[0][0], pair[1][0]], check_orders=pair)

    # --- Ordinary activity ----------------------------------------------------------------------
    for day in range(prior_last - 2, prior_last + 1):
        for _ in range(rng.randint(8, 12)):
            when = moment(day, of=prior)
            rows = add_order(when, identity(regular() if rng.random() < 0.75 else None), random_specs())
            pay(rows, when)
    current = len({r["order_id"] for r in orders if r["ordered_at"].startswith(month)})
    for _ in range(count - current):
        when = moment(rng.randint(1, last_day))
        rows = add_order(when, identity(regular() if rng.random() < 0.8 else None), random_specs())
        filler.append(rows)
        filler_payment = pay(rows, when)
        rows[0]["_payment"] = filler_payment
    rng.shuffle(filler)

    # --- Repeated exports -----------------------------------------------------------------------
    for whole in (False,) * 6 + (True,) * 2:
        rows = filler.pop()
        repeated = rows if whole else [rng.choice(rows)]
        duplicates.extend(repeated)
        instance("duplicate-export", "resolve", "Order rows exported twice",
                 "Count each line once; the repeated rows are the same line, not more sales.",
                 [rows[0]], check_orders=[rows])
    for _ in range(6):
        rows = filler.pop()
        duplicates.append(rows[0]["_payment"])
        instance("duplicate-export", "resolve", "Payment exported twice",
                 "Count the payment ID once; it is a repeated export, not a second charge.",
                 [rows[0], rows[0]["_payment"]], check_orders=[rows],
                 expect=[(rows, "captured_tenders", due(rows))])
    for row in orders:
        row.pop("_payment", None)

    # --- Assign final IDs in time order ---------------------------------------------------------
    order_map = {}
    first_rows = {}
    for row in orders:
        first_rows.setdefault(row["order_id"], row)
    for period, label in ((month, prefix), (prior, prior.replace("-", ""))):
        chosen = sorted((r for r in first_rows.values() if r["ordered_at"].startswith(period)),
                        key=lambda r: (r["ordered_at"], rng.random()))
        number = 0
        for row in chosen:
            if period == prior:
                # Prior-month orders keep plausible register numbers for their date.
                moment_ = dt.datetime.fromisoformat(row["ordered_at"])
                number = max(number + 1, int(((moment_.day - 1) * 1440 + moment_.hour * 60 + moment_.minute)
                                             / (prior_last * 1440) * count))
            else:
                number += 1
            order_map[row["order_id"]] = f"O-{label}-{number:04d}"
    payment_map = {}
    for period in (month, prior):
        label = period.replace("-", "")
        chosen = sorted((p for p in payments if p["payment_at"].startswith(period)),
                        key=lambda p: (p["payment_at"], rng.random()))
        offset = 0 if period == month else int(count * 1.1) - len(chosen)
        for number, payment in enumerate(chosen, start=1 + offset):
            payment_map[payment["payment_id"]] = f"P-{label}-{number:04d}"
    refund_map = {r["refund_id"]: f"R-{prefix}-{number:03d}" for number, r in
                  enumerate(sorted(refunds, key=lambda r: (r["requested_at"], rng.random())), start=1)}

    def renamed_order(value: str) -> str:
        return order_map[value] if value else value

    for row in orders:
        line_suffix = row["line_id"].rsplit("-", 1)[1]
        row["order_id"] = renamed_order(row["order_id"])
        row["line_id"] = f"{row['order_id']}-{line_suffix}"
    for payment in payments:
        payment["payment_id"] = payment_map[payment["payment_id"]]
        payment["order_id"] = renamed_order(payment["order_id"])
        if payment["reference"].startswith("order:"):
            payment["reference"] = "order:" + order_map[payment["reference"].split(":", 1)[1]]
    for refund in refunds:
        refund["refund_id"] = refund_map[refund["refund_id"]]
        refund["line_id"] = f"{order_map[refund['order_id']]}-{refund['line_id'].rsplit('-', 1)[1]}"
        refund["order_id"] = order_map[refund["order_id"]]

    for row, older in amendments:
        row["record_version"] = str(len(older) + 1)

    # Save the canonical, source-supported ledger before export noise is added.
    # Expected figures come from this ledger, never from a model's output.
    ledger = {"orders": copy.deepcopy(orders), "payments": copy.deepcopy(payments),
              "refunds": copy.deepcopy(refunds), "customers": roster, "month": month}

    export_orders = sorted(copy.deepcopy(orders), key=lambda r: (r["ordered_at"], r["line_id"]))
    export_payments = sorted(copy.deepcopy(payments), key=lambda p: (p["payment_at"], p["payment_id"]))
    export_refunds = sorted(copy.deepcopy(refunds), key=lambda r: (r["requested_at"], r["refund_id"]))
    for row, older in amendments:
        for version, spec in enumerate(older, start=1):
            previous = copy.deepcopy(row)
            previous.update(record_version=str(version), **line_fields(*spec))
            previous["notes"] = ""
            export_orders.insert(rng.randrange(len(export_orders) + 1), previous)
    for row in duplicates:
        # Refund rows also carry line_id, so test the most specific key first.
        target = {"refund_id": export_refunds, "payment_id": export_payments, "line_id": export_orders}
        for key, rows in target.items():
            if key in row:
                rows.insert(rng.randrange(len(rows) + 1), copy.deepcopy(row))
                break

    return {"orders": export_orders, "payments": export_payments, "refunds": export_refunds,
            "customers": roster, "ledger": ledger, "month": month, "instances": instances,
            "notes": bookkeeping_notes(month)}


def payment_order(payment: dict) -> str:
    if payment["order_id"]:
        return payment["order_id"]
    return payment["reference"].split(":", 1)[1] if payment["reference"].startswith("order:") else ""


def attribute(rows: list[dict], roster: list[dict]) -> str:
    """Return a customer ID, WALK_IN for no customer details, or UNASSIGNED when ambiguous."""
    first = rows[0]
    if first["customer_id"]:
        return first["customer_id"]
    email = first["customer_email"].strip().lower()
    phone = digits(first["customer_phone"])
    cards = set(re.findall(r"CL-\d{4}", " ".join(r["notes"] for r in rows)))
    evidence = []
    if email:
        evidence.append({c["customer_id"] for c in roster if c["email"].lower() == email})
    if phone:
        evidence.append({c["customer_id"] for c in roster if digits(c["phone"]) == phone})
    if cards:
        evidence.append({c["customer_id"] for c in roster if c["loyalty_reference"] in cards})
    if not (email or phone or cards):
        return "WALK_IN"
    matches = [found for found in evidence if found]
    common = set.intersection(*matches) if matches else set()
    return next(iter(common)) if len(common) == 1 else "UNASSIGNED"


def expected(ledger: dict) -> dict:
    """Account from the canonical ledger using the reporting definitions in the notes."""
    month = ledger["month"]
    roster = ledger["customers"]
    by_line = {r["line_id"]: r for r in ledger["orders"]}
    grouped = defaultdict(list)
    for row in ledger["orders"]:
        grouped[row["order_id"]].append(row)
    client = {order_id: attribute(rows, roster) for order_id, rows in grouped.items()}
    period_orders = {order_id: rows for order_id, rows in grouped.items() if rows[0]["ordered_at"].startswith(month)}
    active_refunds = [r for r in ledger["refunds"] if r["status"] == "succeeded" and r["completed_at"].startswith(month)]
    accepted = [p for p in ledger["payments"] if p["status"] == "captured" and p["payment_at"].startswith(month)]
    product_units = defaultdict(int)
    product_sales = defaultdict(int)
    customer_sales = defaultdict(int)
    customer_orders = defaultdict(set)
    order_rows = {}

    gross = discounts = tax = gift_issued = 0
    for order_id, rows in period_orders.items():
        customer_orders[client[order_id]].add(order_id)
        order_sales = 0
        for row in rows:
            quantity = int(row["quantity"])
            if BY_SKU[row["sku"]]["category"] == "gift_card":
                gift_issued += quantity * cents(row["unit_price"])
                continue
            sales = quantity * cents(row["unit_price"]) - cents(row["discount_amount"])
            gross += quantity * cents(row["unit_price"])
            discounts += cents(row["discount_amount"])
            tax += cents(row["tax_amount"])
            product_units[row["sku"]] += quantity
            product_sales[row["sku"]] += sales
            customer_sales[client[order_id]] += sales
            order_sales += sales
        order_rows[order_id] = {"order_id": order_id,
                                "customer_id": client[order_id] if client[order_id].startswith("C") else "NONE",
                                "sales_before_refunds": order_sales,
                                "amount_due": sum(cents(r["line_total"]) for r in rows), "captured_tenders": 0}
    for refund in active_refunds:
        source = by_line[refund["line_id"]]
        product_units[source["sku"]] -= int(refund["quantity"])
        product_sales[source["sku"]] -= cents(refund["refund_sales"])
        customer_sales[client[source["order_id"]]] -= cents(refund["refund_sales"])

    unmatched = 0
    for payment in ledger["payments"]:
        if payment["status"] != "captured":
            continue
        order_id = payment_order(payment)
        if order_id in order_rows:
            order_rows[order_id]["captured_tenders"] += cents(payment["amount"])
        elif not order_id and payment in accepted and payment["tender"] == "card":
            unmatched += cents(payment["amount"])
    unpaid = sum(max(r["amount_due"] - r["captured_tenders"], 0) for r in order_rows.values())
    overpaid = sum(max(r["captured_tenders"] - r["amount_due"], 0) for r in order_rows.values())
    captured = {t: sum(cents(p["amount"]) for p in accepted if p["tender"] == t) for t in ("card", "cash", "gift_card")}
    returned = {t: sum(cents(r["refund_total"]) for r in active_refunds if r["tender"] == t) for t in ("card", "cash")}
    fees = sum(cents(p["fee"]) for p in accepted if p["tender"] == "card")
    adjustments = sum(cents(r["fee_adjustment"]) for r in active_refunds)
    settled_charges = [p for p in ledger["payments"] if p["status"] == "captured"
                       and p["tender"] == "card" and p["settled_at"].startswith(month)]
    settled_returns = [r for r in ledger["refunds"] if r["status"] == "succeeded"
                       and r["tender"] == "card" and r["settled_at"].startswith(month)]
    payout = (sum(cents(p["amount"]) - cents(p["fee"]) for p in settled_charges)
              - sum(cents(r["refund_total"]) - cents(r["fee_adjustment"]) for r in settled_returns))
    refund_sales = sum(cents(r["refund_sales"]) for r in active_refunds)
    refund_tax = sum(cents(r["refund_tax"]) for r in active_refunds)
    external = captured["card"] + captured["cash"] - sum(returned.values())
    values = {
        "merchandise_gross_sales": gross, "discounts": discounts,
        "merchandise_sales_before_refunds": gross - discounts,
        "successful_refund_sales": refund_sales, "net_sales": gross - discounts - refund_sales,
        "sales_tax_charged": tax, "successful_refund_tax": refund_tax, "net_sales_tax": tax - refund_tax,
        "gift_card_issued": gift_issued, "gift_card_redeemed": captured["gift_card"],
        "gift_card_liability_change": gift_issued - captured["gift_card"],
        "customer_amount_due": sum(r["amount_due"] for r in order_rows.values()),
        "captured_card_payments": captured["card"], "captured_cash_payments": captured["cash"],
        "captured_gift_card_payments": captured["gift_card"], "total_captured_payments": sum(captured.values()),
        "successful_card_refunds": returned["card"], "successful_cash_refunds": returned["cash"],
        "total_successful_refunds": sum(returned.values()), "card_processing_fees": fees,
        "refund_fee_adjustments": adjustments, "expected_card_payout": payout,
        "prior_month_charges_settled": sum(cents(p["amount"]) for p in settled_charges if p["payment_at"] < month),
        "card_captures_settling_later": sum(cents(p["amount"]) for p in accepted
                                             if p["tender"] == "card" and p["settled_at"][:7] > month),
        "card_refunds_settling_later": sum(cents(r["refund_total"]) for r in active_refunds
                                            if r["tender"] == "card" and r["settled_at"][:7] > month),
        "unpaid_order_balance": unpaid, "overpaid_order_balance": overpaid,
        "unmatched_card_payments": unmatched, "unassigned_customer_net_sales": customer_sales["UNASSIGNED"],
        "walk_in_net_sales": customer_sales["WALK_IN"],
        "cash_after_refunds": captured["cash"] - returned["cash"],
        "net_external_receipts": external, "net_receipts_after_fees": external - fees + adjustments,
    }
    metrics = {name: dollars(value) for name, value in values.items()}
    metrics["order_count"] = len(order_rows)
    product_rows = [{"sku": p["sku"], "product_name": p["product_name"],
                     "net_units": product_units[p["sku"]], "net_sales": dollars(product_sales[p["sku"]])}
                    for p in PRODUCTS if p["category"] == "merchandise"]
    product_rows.sort(key=lambda r: (-r["net_sales"], r["sku"]))
    # Include inactive loyalty records too: keeping a legitimate roster row
    # must never look like a false merge or an invented sale to a reviewer.
    names = {c["customer_id"]: c["customer_name"] for c in roster}
    names.update(UNASSIGNED="Unassigned (needs review)", WALK_IN="Walk-in customers")
    customer_ids = set(names) - ({"UNASSIGNED", "WALK_IN"} - set(customer_orders) - set(customer_sales))
    customer_rows = [{"customer_id": cid, "customer_name": names[cid], "order_count": len(customer_orders[cid]),
                      "net_sales": dollars(customer_sales[cid])} for cid in customer_ids]
    customer_rows.sort(key=lambda r: (-r["net_sales"], r["customer_id"]))
    known_customer_rows = [row for row in customer_rows if row["customer_id"] not in {"UNASSIGNED", "WALK_IN"}]
    orders_table = [{**row, **{k: dollars(row[k]) for k in ("sales_before_refunds", "amount_due", "captured_tenders")}}
                    for row in sorted(order_rows.values(), key=lambda r: r["order_id"])]
    refunds_table = [{"refund_id": r["refund_id"],
                      "deducted_sales": dollars(cents(r["refund_sales"]) if r in active_refunds else 0)}
                     for r in sorted(ledger["refunds"], key=lambda r: r["refund_id"])]
    return {"metrics": metrics, "products": product_rows, "customers": customer_rows,
            "top_customers": copy.deepcopy(known_customer_rows[:10]), "orders": orders_table, "refunds": refunds_table}


def finalize_instances(packet: dict, answer: dict) -> list[dict]:
    """Resolve instance records to final IDs and attach machine-checkable expectations."""
    orders = {r["order_id"]: r for r in answer["orders"]}
    refunds = {r["refund_id"]: r for r in answer["refunds"]}
    result = []
    numbering = Counter()

    def record_id(record) -> str:
        if isinstance(record, str):
            return record
        for key in ("refund_id", "payment_id"):
            if key in record:
                return record[key]
        return record["order_id"]

    for entry in packet["instances"]:
        numbering[entry["type"]] += 1
        records = list(dict.fromkeys(record_id(r) for r in entry["records"]))
        checks = []
        for rows in entry["check_orders"]:
            order = orders[rows[0]["order_id"]]
            checks += [{"table": "orders", "id": order["order_id"], "field": field, "expected": order[field]}
                       for field in ORDER_FIELDS]
        for refund in entry["check_refunds"]:
            checks.append({"table": "refunds", "id": refund["refund_id"], "field": "deducted_sales",
                           "expected": refunds[refund["refund_id"]]["deducted_sales"]})
        for rows, field, value in entry["expect"]:
            actual = orders[rows[0]["order_id"]][field]
            wanted = value if field == "customer_id" else dollars(value)
            assert actual == wanted, f"{entry['type']}: {rows[0]['order_id']} {field} {actual} != {wanted}"
        result.append({
            "id": f"{entry['type']}-{numbering[entry['type']]:02d}", "type": entry["type"], "kind": entry["kind"],
            "title": entry["title"], "record_ids": records,
            "anchor_ids": [r for r in records if not re.fullmatch(r"C\d{3}", r)],
            "flag_required": entry["flag"], "expected_behavior": entry["behavior"], "checks": checks,
        })
    return result


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_packet(path: Path, packet: dict) -> dict[str, str]:
    path.mkdir(parents=True, exist_ok=True)
    for name, columns in (("orders", ORDER_COLUMNS), ("payments", PAYMENT_COLUMNS),
                          ("refunds", REFUND_COLUMNS), ("customers", CUSTOMER_COLUMNS)):
        write_csv(path / f"{name}.csv", packet[name], columns)
    catalog = [{"sku": p["sku"], "product_name": p["product_name"], "catalog_price": money(p["price"]),
                "category": p["category"], "tax_rate": "0.08" if p["category"] == "merchandise" else "0.00"}
               for p in PRODUCTS]
    write_csv(path / "products.csv", catalog, PRODUCT_COLUMNS)
    (path / "bookkeeping_notes.md").write_text(packet["notes"], encoding="utf-8")
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.iterdir()) if p.is_file() and p.name in {
                "orders.csv", "payments.csv", "refunds.csv", "customers.csv", "products.csv", "bookkeeping_notes.md"}}


def verify_packet(packet: dict, answer: dict, instances: list[dict]) -> None:
    """Check exported keys/arithmetic and independently reconstruct canonical rows."""
    latest = {}
    for row in packet["orders"]:
        known = latest.get(row["line_id"])
        if known is None or int(row["record_version"]) > int(known["record_version"]):
            latest[row["line_id"]] = row
        elif row["record_version"] == known["record_version"]:
            assert row == known, f"Conflicting same-version export {row['line_id']}"
    canonical_orders = sorted(packet["ledger"]["orders"], key=lambda r: r["line_id"])
    assert sorted(latest.values(), key=lambda r: r["line_id"]) == canonical_orders
    for row in latest.values():
        subtotal = int(row["quantity"]) * cents(row["unit_price"]) - cents(row["discount_amount"])
        category = BY_SKU[row["sku"]]["category"]
        assert cents(row["tax_amount"]) == (rounded_ratio(subtotal, 8, 100) if category == "merchandise" else 0)
        assert cents(row["line_total"]) == subtotal + cents(row["tax_amount"])
    for collection, key in (("payments", "payment_id"), ("refunds", "refund_id")):
        deduped = {}
        for row in packet[collection]:
            assert row[key] not in deduped or row == deduped[row[key]], f"Conflicting {key}"
            deduped[row[key]] = row
        assert sorted(deduped.values(), key=lambda r: r[key]) == sorted(packet["ledger"][collection], key=lambda r: r[key])
    for payment in packet["ledger"]["payments"]:
        if payment["status"] == "captured" and payment["tender"] == "card":
            assert cents(payment["fee"]) == card_fee(cents(payment["amount"]))
        target = payment_order(payment)
        assert not target or any(r["order_id"] == target for r in latest.values()), payment["payment_id"]
    for refund in packet["refunds"]:
        assert refund["line_id"] in latest
        assert refund["order_id"] == latest[refund["line_id"]]["order_id"]
        assert cents(refund["refund_total"]) == cents(refund["refund_sales"]) + cents(refund["refund_tax"])
    m = {k: cents(v) for k, v in answer["metrics"].items() if k != "order_count"}
    assert sum(cents(p["net_sales"]) for p in answer["products"]) == m["net_sales"]
    assert sum(cents(c["net_sales"]) for c in answer["customers"]) == m["net_sales"]
    assert sum(c["order_count"] for c in answer["customers"]) == answer["metrics"]["order_count"]
    assert len(answer["orders"]) == answer["metrics"]["order_count"]
    assert sum(cents(o["amount_due"]) for o in answer["orders"]) == m["customer_amount_due"]
    assert m["total_captured_payments"] - m["customer_amount_due"] == \
        m["overpaid_order_balance"] - m["unpaid_order_balance"] + m["unmatched_card_payments"]
    assert m["prior_month_charges_settled"] > 0 and m["card_captures_settling_later"] > 0
    anchors = Counter(a for entry in instances for a in entry["anchor_ids"])
    assert all(n == 1 for n in anchors.values()), [a for a, n in anchors.items() if n > 1]
    assert all(entry["anchor_ids"] for entry in instances)
    order_ids = {o["order_id"] for o in answer["orders"]}
    refund_ids = {r["refund_id"] for r in answer["refunds"]}
    for entry in instances:
        for check in entry["checks"]:
            assert check["id"] in (order_ids if check["table"] == "orders" else refund_ids)
    # No exported note may label a trap: notes come only from the benign vocabularies.
    allowed = set(ORDER_NOTES) | set(CARD_NOTES) | set(DECLINE_NOTES) | set(REFUND_NOTES)
    for collection in ("orders", "payments", "refunds"):
        for row in packet[collection]:
            assert row["notes"] in allowed or re.fullmatch(r"Loyalty card CL-\d{4} scanned", row["notes"]), row["notes"]


def markdown_key(key: dict, packet: dict) -> str:
    types = Counter(entry["type"] for entry in key["instances"])
    review = sum(entry["flag_required"] for entry in key["instances"])
    lines = [
        "# Retail reconciliation — evaluator answer key", "",
        f"Task: {TASK_ID}; version {VERSION}; fixture seed {key['fixture_seed']}.", "",
        "Keep this key and the generator out of the solver workspace.",
        "The task has not yet been calibrated against any model.", "",
        "The JSON beside this file supplies exact cents-rounded expectations, the per-order and per-refund tables, "
        "every keyed instance with its checks, and SHA-256 input manifests. "
        "Expectations are derived from the source-supported canonical ledger; no model produced these answers.", "",
        "## Scope and calculations", "",
        f"Close: {packet['month']}; {key['metrics']['order_count']} current-month orders. Orders export: "
        f"{len(packet['orders'])} rows for {len(packet['ledger']['orders'])} canonical lines, including "
        f"{previous_month(packet['month'])} supporting orders. Payments export: {len(packet['payments'])} rows for "
        f"{len(packet['ledger']['payments'])} payment IDs. Refunds export: {len(packet['refunds'])} rows for "
        f"{len(packet['ledger']['refunds'])} refund IDs.", "",
        "Use the latest version of each line, each payment/refund ID once, and only succeeded refunds completed in the "
        "close month. Recorded unit prices are authoritative; SKU identifies the product.", "",
        "Gross merchandise sales − line discounts − merchandise refunds completed in the close month = net sales. "
        "Sales tax and gift-card issuance are separate. Prior-month orders are not close-month sales or receipts, "
        "but their close-month returns are deducted.", "",
        "Orders without a customer ID are attributed only when every supplied clue (email, phone, loyalty card) points "
        "to the same single member. No details at all = walk-in. Clues that fit several members or conflict = "
        "unassigned and flagged. Explicit IDs are authoritative.", "",
        "Each order's amount due (all latest line totals, including gift cards) is compared with captured tenders linked "
        "by order_id or an order:<id> reference. Amount matches alone are never a link. Distinct accepted charges "
        "all count in receipts and payout.", "",
        "Expected card payout uses settled_at (next business day, skipping weekends and bank holidays): settled card "
        "charges less their fees, minus settled succeeded card refunds plus their fee adjustments.", "",
        "## Metrics", "", "| Metric | Expected |", "| --- | ---: |",
    ]
    for name, value in key["metrics"].items():
        shown = str(value) if name == "order_count" else f"${value:,.2f}"
        lines.append(f"| `{name}` | {shown} |")
    lines += ["", "## Products", "", "Gift-card issuance is excluded from this earned-sales ranking.", "",
              "| SKU | Net units | Net sales |", "| --- | ---: | ---: |"]
    lines += [f"| {p['sku']} | {p['net_units']} | ${p['net_sales']:,.2f} |" for p in key["products"]]
    lines += ["", "## Top customers", "", "| Rank | Customer ID | Name | Orders | Net sales |",
              "| --- | --- | --- | ---: | ---: |"]
    lines += [f"| {i} | {c['customer_id']} | {c['customer_name']} | {c['order_count']} | ${c['net_sales']:,.2f} |"
              for i, c in enumerate(key["top_customers"], start=1)]
    lines += ["", "All customer rows, including the walk-in and unassigned buckets, are in the JSON. "
              "Equal-value ties can be displayed in either order.", "",
              "## Keyed instances", "",
              f"{len(key['instances'])} instances across {len(types)} types; {review} require a flag. "
              "An instance passes when every listed per-order/per-refund value matches and, if a flag is required, "
              "one of its anchor IDs appears in the submitted exception list. `resolve` = enough evidence for a specific "
              "answer; `review` = keep the supported amount visible and flag it; `preserve` = keep valid records as "
              "they are.", "",
              "| Type | Count |", "| --- | ---: |"]
    lines += [f"| `{name}` | {n} |" for name, n in sorted(types.items())]
    lines += ["", "| Instance | Kind | Flag | Records | Expected behavior |", "| --- | --- | --- | --- | --- |"]
    for entry in key["instances"]:
        lines.append(f"| `{entry['id']}` | {entry['kind']} | {'yes' if entry['flag_required'] else ''} | "
                     + ", ".join(f"`{r}`" for r in entry["record_ids"]) + f" | {entry['expected_behavior']} |")
    lines += ["", "## Fixture integrity", "",
              "The generator checks latest versions, exact duplicate IDs, all line, fee and refund arithmetic, "
              "cross-file references, product/customer totals, distinct customer order counts, the tender-to-order "
              "reconciliation bridge, unique instance anchors, each instance's intended outcome, and that no exported "
              "note labels a trap. Regeneration with the same seed is byte-for-byte deterministic. "
              f"Use `python3 tasks/{TASK_ID}/generate.py --output-root /tmp/retail-fixture-check` to regenerate "
              "elsewhere, and `--seed N` for an alternate fixture with its own key.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--orders", type=int, default=DEFAULT_ORDERS,
                        help="Current-month orders, including keyed instances (minimum 300)")
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if args.orders < 300:
        parser.error("--orders must be at least 300 so ordinary activity surrounds the keyed instances")
    root = args.output_root.resolve()
    task_dir = root / "tasks" / TASK_ID
    packet = build_packet(CLOSE_MONTH, args.seed, args.orders)
    answer = expected(packet["ledger"])
    instances = finalize_instances(packet, answer)
    verify_packet(packet, answer, instances)
    input_hashes = write_packet(task_dir / "inputs", packet)
    key = {"task_id": TASK_ID, "version": VERSION, "fixture_seed": args.seed, "currency": "USD",
           "reporting_period": CLOSE_MONTH, "status": "authored_not_calibrated", "input_hashes": input_hashes,
           **answer, "instances": instances}
    key_dir = root / "answer-keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / f"{TASK_ID}.json").write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (key_dir / f"{TASK_ID}.md").write_text(markdown_key(key, packet), encoding="utf-8")
    print(f"Generated {TASK_ID} v{VERSION} (seed {args.seed}) at {root}")
    print(f"{CLOSE_MONTH}: {answer['metrics']['order_count']} orders, {len(packet['orders'])} exported order rows, "
          f"{len(instances)} keyed instances, net sales ${answer['metrics']['net_sales']:,.2f}, "
          f"expected card payout ${answer['metrics']['expected_card_payout']:,.2f}")
    print("Fixture integrity checks passed; no model runs have been performed.")


if __name__ == "__main__":
    main()
