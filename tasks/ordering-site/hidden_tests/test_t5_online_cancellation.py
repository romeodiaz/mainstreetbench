"""Ticket 5: customers cancel from their order page, not on pickup day, and cancelling undoes everything."""

from decimal import Decimal

from harness import FRIDAY, SATURDAY, SUNDAY, TODAY, SiteCase, gift_codes, money_in


class OnlineCancellation(SiteCase):
    def cancel(self, attempt):
        self.shopper.cancel(attempt.page, attempt.url)

    def status(self, order_id):
        return self.saved(order_id)["status"]

    def test_customer_can_cancel_from_their_order_page(self):
        attempt = self.placed(date=FRIDAY, slot="10:00")
        self.cancel(attempt)
        self.assertEqual(self.status(attempt.order_id), "cancelled")

    def test_not_on_the_day_of_pickup(self):
        today = self.placed(date=TODAY, slot="12:00")
        self.cancel(today)
        self.assertEqual(self.status(today.order_id), "placed")
        tomorrow = self.placed(date=FRIDAY, slot="12:00")
        self.cancel(tomorrow)
        self.assertEqual(self.status(tomorrow.order_id), "cancelled")

    def test_strangers_cannot_cancel_by_order_number(self):
        attempt = self.placed(date=SATURDAY, slot="10:00")
        self.shopper.stranger_cancel(attempt.order_id)
        self.assertEqual(self.status(attempt.order_id), "placed")
        self.cancel(attempt)
        self.assertEqual(self.status(attempt.order_id), "cancelled")

    def test_cancelling_frees_the_pickup_time(self):
        attempts = [self.placed(slot="09:00", name=f"C{n}", require_time=True) for n in range(4)]
        self.refused(slot="09:00", require_time=True)
        self.cancel(attempts[0])
        self.assertEqual(self.status(attempts[0].order_id), "cancelled")
        self.placed(slot="09:00", require_time=True)

    def test_cancelling_frees_the_cakes(self):
        attempt = self.placed([("CAKE48", 6)], slot="10:00")
        self.refused([("CAKE48", 1)], slot="10:30")
        self.cancel(attempt)
        self.placed([("CAKE48", 6)], slot="10:30")

    def test_cancelling_puts_money_back_on_the_gift_card(self):
        bought = self.placed([("GIFT25", 1)], slot="09:00")
        codes = gift_codes(bought.text)
        paid = None
        for code in codes:
            attempt = self.order([("BREAD9", 2)], gift=code, slot="10:00")
            if attempt.placed:
                paid = (code, attempt)
                break
        self.assertIsNotNone(paid, "Gift card could not be used")
        code, attempt = paid
        self.cancel(attempt)
        self.assertEqual(self.status(attempt.order_id), "cancelled")
        again = self.placed([("CAKE48", 1)], gift=code, date=SUNDAY, slot="10:00")
        self.assertIn(Decimal("25.00"), money_in(again.text), "The full $25 should be back on the card")
        # The card is empty again. Cancelling the old order a second time must not refund it twice.
        self.cancel(attempt)
        self.refused([("BREAD9", 1)], gift=code, date=SUNDAY, slot="10:30")

    def test_cancelling_a_gift_card_purchase_voids_the_card(self):
        bought = self.placed([("GIFT25", 1)], date=FRIDAY, slot="09:00")
        codes = gift_codes(bought.text)
        self.cancel(bought)
        self.assertEqual(self.status(bought.order_id), "cancelled")
        for code in codes:
            with self.subTest(code=code):
                self.refused([("BREAD9", 2)], gift=code, slot="10:00")
