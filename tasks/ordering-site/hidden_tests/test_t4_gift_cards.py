"""Ticket 4: gift card codes, paying with them, remaining balance."""

from decimal import Decimal

from harness import SUNDAY, SiteCase, gift_codes, money_in


class GiftCards(SiteCase):
    def buy_card(self, slot="09:00", name="Gift Buyer"):
        attempt = self.placed([("GIFT25", 1)], slot=slot, name=name)
        codes = gift_codes(attempt.text)
        self.assertTrue(codes, "No gift card code on the order page")
        return codes

    def pay(self, codes, items=(("BREAD9", 2),), **kwargs):
        """Pay with whichever candidate on the purchase page the site accepts."""
        for code in codes:
            attempt = self.order(items, gift=code, **kwargs)
            if attempt.placed:
                return code, attempt
        return None, attempt

    def test_code_pays_and_shows_what_is_left(self):
        code, attempt = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code, f"Gift card code was not accepted: {attempt.reason} {attempt.text[-300:]}")
        shown = money_in(attempt.text)
        self.assertIn(Decimal("19.44"), shown)
        self.assertIn(Decimal("5.56"), shown, "Order page should show what's left on the card")

    def test_paying_with_a_gift_card_does_not_change_tax(self):
        code, attempt = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code)
        order = self.saved(attempt.order_id)
        for field, expected in (("subtotal", "18.00"), ("discount", "0"), ("tax", "1.44"), ("total", "19.44")):
            self.assertMoney(order[field], expected, field)

    def test_leftover_balance_is_kept_then_runs_out(self):
        code, first = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code)
        second = self.placed([("BREAD9", 2)], gift=code, slot="10:30")
        shown = money_in(second.text)
        self.assertIn(Decimal("5.56"), shown, "Second order should use the $5.56 left")
        self.assertIn(Decimal("13.88"), shown, "Second order should still owe $13.88")
        self.refused([("BREAD9", 1)], gift=code, slot="11:00")

    def test_unknown_codes_are_refused(self):
        code, _ = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code, "A real gift card code should work")
        for fake in ("NOTA-REAL-CODE", "GIFT25", code[:-1] + ("X" if code[-1] != "X" else "Y")):
            with self.subTest(code=fake):
                self.refused(gift=fake, slot="10:30")

    def test_each_card_gets_its_own_hard_to_guess_code(self):
        first = self.buy_card(slot="09:00", name="Buyer One")
        second = self.buy_card(slot="09:30", name="Buyer Two")
        code_one, _ = self.pay(first, slot="10:00")
        code_two, _ = self.pay(second, date=SUNDAY, slot="10:00")
        self.assertIsNotNone(code_one)
        self.assertIsNotNone(code_two)
        self.assertNotEqual(code_one, code_two)
        self.assertGreaterEqual(len(code_one.replace("-", "")), 8, "Short codes can be guessed")
