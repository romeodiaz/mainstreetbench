"""Ticket 2: half-hour pickup times while open, 4 per slot, notice periods, admin order, old orders."""

import re

from harness import FRIDAY, MONDAY, SATURDAY, SUNDAY, TODAY, LegacyCase, SiteCase


class PickupTimes(SiteCase):
    def test_times_cover_opening_hours_only(self):
        self.placed(slot="07:00", require_time=True)
        self.placed(slot="14:30", require_time=True)
        self.placed(slot="12:30", require_time=True)
        for slot in ("06:30", "15:00", "07:15"):
            with self.subTest(slot=slot):
                self.refused(slot=slot, require_time=True)
        self.assertEqual([o["pickup_date"] for o in self.admin_orders()], [SATURDAY] * 3)

    def test_closed_on_mondays(self):
        self.refused(date=MONDAY, slot="10:00", require_time=True)
        self.placed(date=SUNDAY, slot="10:00", require_time=True)

    def test_two_hours_notice(self):
        # It is Thursday 9:10.
        self.refused(date=TODAY, slot="11:00", require_time=True)
        self.placed(date=TODAY, slot="11:30", require_time=True)

    def test_four_orders_per_half_hour(self):
        for n in range(4):
            self.placed(slot="09:00", name=f"Customer {n}", require_time=True)
        self.refused(slot="09:00", require_time=True)
        self.placed(slot="09:30", require_time=True)
        self.placed(date=SUNDAY, slot="09:00", require_time=True)

    def test_cakes_and_catering_need_two_days(self):
        # Two days from Thursday 9:10 is Saturday 9:10.
        for sku in ("CAKE48", "CATER120"):
            with self.subTest(sku=sku):
                self.refused([(sku, 1)], slot="09:00", require_time=True)
                self.refused([(sku, 1), ("BREAD9", 1)], date=FRIDAY, slot="13:00", require_time=True)
                self.placed([(sku, 1)], slot="09:30", require_time=True)
        self.placed([("PIE32", 1)], date=FRIDAY, slot="09:00", require_time=True)

    def test_orders_page_lists_pickup_order_with_times(self):
        plan = [(SUNDAY, "08:00"), (SATURDAY, "13:00"), (SATURDAY, "07:30"), (SATURDAY, "13:00"), (FRIDAY, "14:00")]
        ids = [self.placed(date=d, slot=s, name=f"Customer {n}", require_time=True).order_id
               for n, (d, s) in enumerate(plan)]
        expected = [ids[4], ids[2], ids[1], ids[3], ids[0]]
        status, page = self.call("GET", "/admin", admin=True)
        positions = [page.index(f'data-order-id="{i}"') for i in expected]
        self.assertEqual(positions, sorted(positions), "Orders should be listed in pickup order")
        for order_id, (_, slot) in zip(ids, plan):
            row = re.search(rf'data-order-id="{order_id}".*?</tr>', page, re.S).group(0)
            from harness import times_in
            self.assertIn(slot, times_in(re.sub(r"<[^>]+>", " ", row)), f"Row for order {order_id} lacks its time")


    def test_confirmation_shows_the_pickup_time(self):
        from harness import times_in
        attempt = self.placed(slot="13:30", require_time=True)
        self.assertIn("13:30", times_in(attempt.text))


class ExistingOrdersKeepWorking(LegacyCase):
    def test_existing_orders_survive_and_new_ones_work(self):
        saved = {o["id"]: o for o in self.admin_orders()}
        for old in self.legacy_orders:
            with self.subTest(order=old["id"]):
                self.assertIn(old["id"], saved)
                self.assertEqual(saved[old["id"]]["status"], old["status"])
                self.assertEqual([(i["sku"], i["qty"]) for i in saved[old["id"]]["items"]],
                                 [(i["sku"], i["qty"]) for i in old["items"]])
        attempt = self.placed([("BREAD9", 1)], date=SUNDAY, slot="07:00", require_time=True)
        self.assertGreater(attempt.order_id, max(o["id"] for o in self.legacy_orders))
        self.assertEqual(self.call("GET", "/admin", admin=True)[0], 200)
