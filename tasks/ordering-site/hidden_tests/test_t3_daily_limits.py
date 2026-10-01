"""Ticket 3: never more than 6 cakes, 4 catering trays or 8 pies per pickup day.

Sites may refuse an over-limit order or cap the quantity a customer can add; either is fine.
What counts is that no more than the limit is ever booked, and that within-limit orders go through.
"""

from harness import SATURDAY, SUNDAY, LegacyCase, SiteCase


class DailyLimits(SiteCase):
    def test_six_cakes_a_day(self):
        self.placed([("CAKE48", 2)], slot="10:00")
        self.placed([("CAKE48", 4)], slot="10:30")
        attempt = self.order([("CAKE48", 1)], slot="11:00")
        self.assertEqual(self.sold("CAKE48", SATURDAY), 6, "A seventh cake was sold")
        self.assertRegex(attempt.text, r"(?i)sold out|no more|only \d+|none left|0 left")

    def test_limits_are_per_pickup_day(self):
        self.placed([("CAKE48", 6)], slot="10:00")
        self.placed([("CAKE48", 6)], date=SUNDAY, slot="10:00")
        self.order([("CAKE48", 1)], date=SUNDAY, slot="11:00")
        self.assertEqual((self.sold("CAKE48", SATURDAY), self.sold("CAKE48", SUNDAY)), (6, 6))

    def test_trays_and_pies(self):
        self.order([("CATER120", 5)], slot="10:00")
        self.order([("PIE32", 9)], slot="10:30")
        self.assertLessEqual(self.sold("CATER120", SATURDAY), 4, "More than 4 catering trays were sold")
        self.assertLessEqual(self.sold("PIE32", SATURDAY), 8, "More than 8 pies were sold")
        self.placed([("CATER120", 4)], date=SUNDAY, slot="10:00")
        self.placed([("PIE32", 8)], date=SUNDAY, slot="10:30")
        self.placed([("BREAD9", 30)], slot="11:00")

    def test_over_limit_request_never_oversells(self):
        self.placed([("CAKE48", 5)], slot="10:00")
        self.order([("BREAD9", 3), ("CAKE48", 2)], slot="10:30")
        self.assertLessEqual(self.sold("CAKE48", SATURDAY), 6, "Two more cakes were sold when only one was left")

    def test_refused_order_does_not_take_a_pickup_time(self):
        self.placed([("CAKE48", 6)], slot="09:30", require_time=True)
        for n in range(3):
            self.placed([("BREAD9", 1)], slot="10:00", name=f"C{n}", require_time=True)
        self.refused([("CAKE48", 1)], slot="10:00", require_time=True)
        self.placed([("BREAD9", 1)], slot="10:00", require_time=True)


class LimitsWithExistingOrders(LegacyCase):
    def test_existing_orders_count_toward_the_day(self):
        # Saturday already has 3 + 2 cakes from before the change; the cancelled 4-cake order doesn't count.
        self.order([("CAKE48", 2)], slot="10:00")
        self.assertLessEqual(self.sold("CAKE48", SATURDAY), 6, "Existing orders were ignored")
        self.order([("CAKE48", 1)], slot="10:30")
        self.assertEqual(self.sold("CAKE48", SATURDAY), 6, "The last cake should still be orderable")
