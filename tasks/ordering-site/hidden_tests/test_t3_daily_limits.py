"""Ticket 3: 6 cakes, 4 catering trays and 8 pies per pickup day; sold-out orders are refused whole."""

from harness import SATURDAY, SUNDAY, LegacyCase, SiteCase


class DailyLimits(SiteCase):
    def test_six_cakes_a_day(self):
        self.placed([("CAKE48", 2)], slot="10:00")
        self.placed([("CAKE48", 4)], slot="10:30")
        attempt = self.refused([("CAKE48", 1)], slot="11:00")
        self.assertRegex(attempt.text, r"(?i)sold out|no more|only \d+|none left|0 left")

    def test_limits_are_per_pickup_day(self):
        self.placed([("CAKE48", 6)], slot="10:00")
        self.placed([("CAKE48", 6)], date=SUNDAY, slot="10:00")
        self.refused([("CAKE48", 1)], date=SUNDAY, slot="11:00")

    def test_trays_and_pies(self):
        self.refused([("CATER120", 5)], slot="10:00")
        self.placed([("CATER120", 4)], slot="10:00")
        self.refused([("PIE32", 9)], slot="10:30")
        self.placed([("PIE32", 8)], slot="10:30")
        self.placed([("BREAD9", 30)], slot="11:00")

    def test_over_limit_order_is_refused_whole(self):
        self.placed([("CAKE48", 5)], slot="10:00")
        self.refused([("BREAD9", 3), ("CAKE48", 2)], slot="10:30")
        self.placed([("CAKE48", 1)], slot="10:30")

    def test_refused_order_does_not_take_a_pickup_time(self):
        self.placed([("CAKE48", 6)], slot="09:30", require_time=True)
        for n in range(3):
            self.placed([("BREAD9", 1)], slot="10:00", name=f"C{n}", require_time=True)
        self.refused([("CAKE48", 1)], slot="10:00", require_time=True)
        self.placed([("BREAD9", 1)], slot="10:00", require_time=True)


class LimitsWithExistingOrders(LegacyCase):
    def test_existing_orders_count_toward_the_day(self):
        # Saturday already has 3 + 2 cakes from before the change; the cancelled 4-cake order doesn't count.
        self.refused([("CAKE48", 2)], slot="10:00")
        self.placed([("CAKE48", 1)], slot="10:00")
