"""Ticket 4: gift card codes, paying with them, remaining balance."""

import re
from decimal import Decimal

from harness import SUNDAY, SiteCase, gift_codes, money_in  # noqa: F401


class GiftCards(SiteCase):
    def buy_card(self, slot="09:00", name="Gift Buyer"):
        attempt = self.placed([("GIFT25", 1)], slot=slot, name=name)
        self.assertTrue(gift_codes(attempt.text) or self.staff_activate(attempt.order_id),
                        "No gift card code on the order page")
        return attempt

    def pay(self, bought, items=(("BREAD9", 2),), **kwargs):
        return self.spend_gift_card(bought, items, **kwargs)

    def test_code_pays_and_shows_what_is_left(self):
        code, attempt = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code, f"Gift card code was not accepted: {attempt and attempt.reason}")
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

    def test_staff_see_what_is_left_to_pay(self):
        code, _ = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code)
        second = self.placed([("BREAD9", 2)], gift=code, slot="10:30")
        page = self.call("GET", "/admin", admin=True)[1]
        row = re.search(rf'data-order-id="{second.order_id}".*?</tr>', page, re.S).group(0)
        self.assertIn(Decimal("13.88"), money_in(re.sub(r"<[^>]+>", " ", row)),
                      "The orders page should tell staff what to collect at pickup")

    def test_strangers_cannot_see_gift_codes(self):
        bought = self.buy_card()
        bought.page.goto(bought.url)
        codes = gift_codes(bought.page.inner_text("body"))
        context, page = self.shopper.new_page()
        page.goto(f"/order/{bought.order_id}")
        text = page.inner_text("body")
        for code in codes:
            self.assertNotIn(code, text, "Anyone can read gift card codes by typing an order number")

    def test_two_cards_in_one_order_are_worth_fifty(self):
        # A $129.60 catering tray leaves $79.60 to pay after $50 of cards, or $104.60 after one $25 card.
        bought = self.placed([("GIFT25", 2)], slot="09:00")
        code, first = self.spend_gift_card(bought, [("CATER120", 1)], date=SUNDAY, slot="10:00")
        self.assertIsNotNone(code)
        shown = money_in(first.text)
        if Decimal("79.60") in shown:
            return
        self.assertIn(Decimal("104.60"), shown, "The card paid neither $25 nor $50")
        others = [c for c in gift_codes(bought.page.inner_text("body")) if c != code]
        for other in others:
            second = self.order([("CATER120", 1)], gift=other, date=SUNDAY, slot="10:30")
            if second.placed:
                self.assertIn(Decimal("104.60"), money_in(second.text))
                return
        self.fail("Only $25 of the $50 in gift cards could be spent")

    def test_refused_order_does_not_use_the_card(self):
        code, _ = self.pay(self.buy_card(), slot="10:00")
        self.assertIsNotNone(code)
        self.placed([("CAKE48", 6)], slot="11:00")
        self.refused([("CAKE48", 1)], gift=code, slot="11:30")
        again = self.placed([("BREAD9", 1)], gift=code, slot="12:00")
        self.assertIn(Decimal("5.56"), money_in(again.text), "A refused order took money off the card")

    def test_coupon_comes_off_before_the_card(self):
        bought = self.buy_card()
        code, paid = self.pay(bought, [("BREAD9", 2), ("CROISSANT21", 1)], promo="WELCOME10", slot="10:00")
        self.assertIsNotNone(code)
        self.assertMoney(self.saved(paid.order_id)["total"], "37.91")
        self.assertIn(Decimal("12.91"), money_in(paid.text), "After the $25 card, $12.91 is still owed")
