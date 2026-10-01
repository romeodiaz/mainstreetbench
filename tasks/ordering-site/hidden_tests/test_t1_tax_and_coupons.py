"""Ticket 1: tax after coupons, untaxed and undiscounted gift cards, half-up cents."""

from harness import SiteCase


class TaxAndCoupons(SiteCase):
    def check(self, items, promo, subtotal, discount, tax, total):
        status, order = self.place(items, promo=promo)
        self.assertEqual(status, 201, order)
        for field, expected in (("subtotal", subtotal), ("discount", discount), ("tax", tax), ("total", total)):
            self.assertMoney(order[field], expected, field)
        return order

    def test_percent_coupon_taxes_the_discounted_price(self):
        self.check([("BREAD9", 2), ("CROISSANT21", 1)], "WELCOME10", "39.00", "3.90", "2.81", "37.91")

    def test_dollar_coupon_taxes_the_discounted_price(self):
        self.check([("BREAD9", 2)], "FIVEOFF", "18.00", "5.00", "1.04", "14.04")

    def test_gift_card_alone_is_not_taxed(self):
        self.check([("GIFT25", 2)], None, "50.00", "0", "0", "50.00")

    def test_coupon_does_not_discount_gift_cards(self):
        self.check([("GIFT25", 1), ("BREAD9", 1)], "WELCOME10", "34.00", "0.90", "0.65", "33.75")

    def test_dollar_coupon_capped_at_food_subtotal(self):
        self.check([("GIFT25", 1), ("BAGEL225", 1)], "FIVEOFF", "27.25", "2.25", "0", "25.00")

    def test_half_cent_discount_rounds_up(self):
        self.check([("BREAD9", 2), ("SCONE375", 1), ("BAGUETTE5", 1)], "WELCOME10", "26.75", "2.68", "1.93", "26.00")
        self.check([("CINNAMON325", 2)], "FALL15", "6.50", "0.98", "0.44", "5.96")

    def test_corrected_amounts_are_stored_and_shown(self):
        order = self.check([("GIFT25", 1), ("BREAD9", 1)], "WELCOME10", "34.00", "0.90", "0.65", "33.75")
        status, fetched = self.call("GET", f"/api/orders/{order['id']}")
        self.assertMoney(fetched["tax"], "0.65")
        self.assertMoney(fetched["total"], "33.75")
        listed = {o["id"]: o for o in self.admin_orders()}[order["id"]]
        self.assertMoney(listed["total"], "33.75")
        status, page = self.call("GET", f"/order/{order['id']}")
        self.assertIn("$33.75", page)
        self.assertIn("$0.65", page)
