"""Ticket 1: tax after coupons, untaxed gift cards, coupons only on food, half-cents round up."""

from harness import SiteCase


class TaxAndCoupons(SiteCase):
    def check(self, items, promo, subtotal, discount, tax, total, slot="10:00"):
        attempt = self.placed(items, promo=promo, slot=slot)
        order = self.saved(attempt.order_id)
        for field, expected in (("subtotal", subtotal), ("discount", discount), ("tax", tax), ("total", total)):
            self.assertMoney(order[field], expected, field)
        return attempt

    def test_percent_coupon_taxes_the_discounted_price(self):
        self.check([("BREAD9", 2), ("CROISSANT21", 1)], "WELCOME10", "39.00", "3.90", "2.81", "37.91")

    def test_dollar_coupon_taxes_the_discounted_price(self):
        self.check([("BREAD9", 2)], "FIVEOFF", "18.00", "5.00", "1.04", "14.04")

    def test_gift_cards_are_not_taxed(self):
        self.check([("GIFT25", 2)], None, "50.00", "0", "0", "50.00")

    def test_coupons_do_not_discount_gift_cards(self):
        self.check([("GIFT25", 1), ("BREAD9", 1)], "WELCOME10", "34.00", "0.90", "0.65", "33.75")
        # A dollar coupon can't take more than the food is worth.
        self.check([("GIFT25", 1), ("BAGEL225", 1)], "FIVEOFF", "27.25", "2.25", "0", "25.00", slot="10:30")

    def test_half_cents_round_up(self):
        self.check([("BREAD9", 2), ("SCONE375", 1), ("BAGUETTE5", 1)], "WELCOME10", "26.75", "2.68", "1.93", "26.00")
        self.check([("CINNAMON325", 2)], "FALL15", "6.50", "0.98", "0.44", "5.96", slot="10:30")
