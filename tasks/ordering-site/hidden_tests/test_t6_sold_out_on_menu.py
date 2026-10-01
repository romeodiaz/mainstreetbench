"""Ticket 6: choosing a day on the menu shows what's sold out that day and stops it being added."""

import re

from harness import SATURDAY, SUNDAY, SiteCase


class SoldOutOnMenu(SiteCase):
    def row(self, page, sku):
        return page.locator(f'[data-sku="{sku}"]').first

    def addable(self, page, sku) -> bool:
        add = self.row(page, sku).get_by_role("button", name=re.compile(r"add", re.I))
        return bool(add.count()) and add.first.is_enabled()

    def menu(self, day):
        page = self.shopper.menu_for_day(day)
        self.assertIsNotNone(page, "The menu has no way to choose a pickup day")
        return page

    def test_sold_out_cakes_are_marked_for_that_day(self):
        self.placed([("CAKE48", 6)], slot="10:00")
        page = self.menu(SATURDAY)
        self.assertRegex(self.row(page, "CAKE48").inner_text(), r"(?i)sold out")
        self.assertFalse(self.addable(page, "CAKE48"), "A sold-out cake can still be added")
        self.assertTrue(self.addable(page, "BREAD9"))
        self.assertNotRegex(self.row(page, "BREAD9").inner_text(), r"(?i)sold out")

    def test_other_days_are_not_affected(self):
        self.placed([("CAKE48", 6)], slot="10:00")
        page = self.menu(SUNDAY)
        self.assertTrue(self.addable(page, "CAKE48"))
        self.assertNotRegex(self.row(page, "CAKE48").inner_text(), r"(?i)sold out")

    def test_trays_and_pies_too(self):
        self.placed([("CATER120", 4)], date=SUNDAY, slot="10:00")
        self.placed([("PIE32", 8)], date=SUNDAY, slot="10:30")
        page = self.menu(SUNDAY)
        for sku in ("CATER120", "PIE32"):
            with self.subTest(sku=sku):
                self.assertRegex(self.row(page, sku).inner_text(), r"(?i)sold out")
                self.assertFalse(self.addable(page, sku))

    def test_a_cancelled_order_brings_it_back(self):
        attempt = self.placed([("CAKE48", 6)], slot="10:00")
        self.call("POST", f"/admin/api/orders/{attempt.order_id}/cancel", admin=True)
        page = self.menu(SATURDAY)
        self.assertTrue(self.addable(page, "CAKE48"))
