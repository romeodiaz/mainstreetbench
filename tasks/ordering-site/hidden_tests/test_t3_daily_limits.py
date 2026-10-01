"""Ticket 3: per-day product limits, sold-out menu, all-or-nothing orders, admin changes."""

import re

from harness import SATURDAY, SUNDAY, LegacyCase, SiteCase


class DailyLimits(SiteCase):
    def menu(self, date=None):
        status, data = self.call("GET", "/api/menu" + (f"?date={date}" if date else ""))
        self.assertEqual(status, 200)
        return {p["sku"]: p for p in data["products"]}

    def set_limit(self, sku, value, admin=True):
        return self.call("PUT", f"/admin/api/products/{sku}", {"daily_limit": value}, admin=admin)

    def test_default_limits(self):
        menu = self.menu()
        self.assertEqual({s: menu[s]["daily_limit"] for s in ("CAKE48", "CATER120", "PIE32", "BREAD9", "GIFT25")},
                         {"CAKE48": 6, "CATER120": 4, "PIE32": 8, "BREAD9": None, "GIFT25": None})
        dated = self.menu(SATURDAY)
        self.assertEqual((dated["CAKE48"]["remaining"], dated["CAKE48"]["sold_out"]), (6, False))
        self.assertEqual((dated["BREAD9"]["remaining"], dated["BREAD9"]["sold_out"]), (None, False))

    def test_orders_use_up_the_day_and_other_days_are_separate(self):
        self.assertEqual(self.place([("CAKE48", 2)])[0], 201)
        self.assertEqual(self.place([("CAKE48", 4)], slot="11:00")[0], 201)
        saturday = self.menu(SATURDAY)["CAKE48"]
        self.assertEqual((saturday["remaining"], saturday["sold_out"]), (0, True))
        sunday = self.menu(SUNDAY)["CAKE48"]
        self.assertEqual((sunday["remaining"], sunday["sold_out"]), (6, False))
        status, data = self.place([("CAKE48", 1)], slot="12:00")
        self.assertEqual(status, 409, data)
        self.assertEqual((data.get("sku"), data.get("remaining")), ("CAKE48", 0))
        self.assertEqual(self.place([("CAKE48", 1)], date=SUNDAY)[0], 201)

    def test_over_limit_order_is_rejected_whole(self):
        self.assertEqual(self.place([("PIE32", 5)])[0], 201)
        status, data = self.place([("BREAD9", 3), ("PIE32", 4)], slot="11:00")
        self.assertEqual(status, 409, data)
        self.assertEqual((data.get("sku"), data.get("remaining")), ("PIE32", 3))
        self.assertIsInstance(data.get("error"), str)
        self.assertEqual(len(self.admin_orders()), 1)
        self.assertEqual(self.menu(SATURDAY)["PIE32"]["remaining"], 3)

    def test_same_item_on_two_lines_counts_together(self):
        self.assertEqual(self.set_limit("CAKE48", 1)[0], 200)
        status, data = self.place([("CAKE48", 1), ("CAKE48", 1)])
        self.assertEqual(status, 409, data)
        self.assertEqual(self.place([("CAKE48", 1)])[0], 201)

    def test_rejected_order_does_not_take_a_pickup_slot(self):
        self.set_limit("CAKE48", 1)
        for n in range(3):
            self.assertEqual(self.place([("BREAD9", 1)], slot="10:00", name=f"C{n}")[0], 201)
        self.assertEqual(self.place([("CAKE48", 2)], slot="10:00")[0], 409)
        self.assertEqual(self.place([("BREAD9", 1)], slot="10:00")[0], 201)

    def test_cancelling_makes_it_available_again(self):
        _, order = self.place([("CATER120", 4)])
        self.assertTrue(self.menu(SATURDAY)["CATER120"]["sold_out"])
        self.call("POST", f"/admin/api/orders/{order['id']}/cancel", admin=True)
        self.assertEqual(self.menu(SATURDAY)["CATER120"]["remaining"], 4)
        self.assertEqual(self.place([("CATER120", 1)], slot="11:00")[0], 201)

    def test_menu_page_shows_sold_out_for_that_date(self):
        self.place([("CATER120", 4)])
        status, page = self.call("GET", f"/?date={SATURDAY}")
        self.assertEqual(status, 200)
        row = re.search(r'<[^>]*data-sku="CATER120"[^>]*>', page)
        self.assertIsNotNone(row)
        self.assertIn('data-sold-out="true"', row.group(0))
        self.assertIn("Sold out", page)
        bread = re.search(r'<[^>]*data-sku="BREAD9"[^>]*>', page).group(0)
        self.assertNotIn('data-sold-out="true"', bread)
        sunday = self.call("GET", f"/?date={SUNDAY}")[1]
        self.assertNotIn('data-sold-out="true"', sunday)

    def test_owner_can_change_limits(self):
        self.assertEqual(self.set_limit("CAKE48", 2, admin=False)[0], 401)
        status, product = self.set_limit("CAKE48", 2)
        self.assertEqual((status, product.get("sku"), product.get("daily_limit")), (200, "CAKE48", 2))
        self.assertEqual(self.menu(SATURDAY)["CAKE48"]["remaining"], 2)
        status, product = self.set_limit("BREAD9", 10)
        self.assertEqual(product.get("daily_limit"), 10)
        status, product = self.set_limit("PIE32", None)
        self.assertEqual((status, product.get("daily_limit")), (200, None))
        self.assertEqual(self.menu(SATURDAY)["PIE32"]["remaining"], None)
        self.assertEqual(self.place([("PIE32", 20)])[0], 201)
        for bad in (-1, 1.5, "six", True):
            with self.subTest(value=bad):
                self.assertEqual(self.set_limit("CAKE48", bad)[0], 400)
        self.assertEqual(self.set_limit("NOPE", 3)[0], 404)
        self.restart()
        menu = self.menu()
        self.assertEqual((menu["CAKE48"]["daily_limit"], menu["BREAD9"]["daily_limit"]), (2, 10))


class LimitsWithExistingOrders(LegacyCase):
    def test_existing_orders_count_toward_limits(self):
        # Legacy Saturday orders hold 3 + 2 cakes; the cancelled 4-cake order does not count.
        status, data = self.call("GET", f"/api/menu?date={SATURDAY}")
        cake = {p["sku"]: p for p in data["products"]}["CAKE48"]
        self.assertEqual((cake["daily_limit"], cake["remaining"]), (6, 1))
        self.assertEqual(self.place([("CAKE48", 2)])[0], 409)
        self.assertEqual(self.place([("CAKE48", 1)])[0], 201)
