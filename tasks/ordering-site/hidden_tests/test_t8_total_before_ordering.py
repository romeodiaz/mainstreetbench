"""Ticket 8: the checkout page shows the total and what's owed at pickup before ordering, and it matches."""

from decimal import Decimal

from harness import SUNDAY, SiteCase, money_in


class TotalBeforeOrdering(SiteCase):
    def shown_then_charged(self, items, total, **kwargs):
        attempt = self.placed(items, inspect=True, **kwargs)
        self.assertIn(Decimal(total), money_in(attempt.checkout_text), "Total wasn't shown before ordering")
        self.assertMoney(self.saved(attempt.order_id)["total"], total)
        return attempt

    def test_plain_total(self):
        self.shown_then_charged([("BREAD9", 2)], "19.44")

    def test_coupon_with_half_cent_rounding(self):
        self.shown_then_charged([("BREAD9", 2), ("SCONE375", 1), ("BAGUETTE5", 1)], "26.00", promo="WELCOME10")

    def test_coupon_never_touches_gift_cards(self):
        self.shown_then_charged([("GIFT25", 1), ("BREAD9", 1)], "33.75", promo="WELCOME10")

    def test_gift_card_shows_what_is_still_owed(self):
        bought = self.placed([("GIFT25", 1)], slot="09:00")
        code, _ = self.spend_gift_card(bought, slot="10:00")
        self.assertIsNotNone(code, "Gift card could not be used")
        # $5.56 is left on the card, so a $19.44 order leaves $13.88 to pay at pickup.
        attempt = self.placed([("BREAD9", 2)], gift=code, date=SUNDAY, slot="10:00", inspect=True)
        self.assertIn(Decimal("13.88"), money_in(attempt.checkout_text), "Amount owed wasn't shown before ordering")

    def test_total_follows_cart_changes(self):
        attempt = self.placed([("BREAD9", 3)], edits=[("Sourdough Loaf", 1)], inspect=True)
        self.assertIn(Decimal("9.72"), money_in(attempt.checkout_text))
        self.assertNotIn(Decimal("29.16"), money_in(attempt.checkout_text), "Shown total didn't follow the change")
