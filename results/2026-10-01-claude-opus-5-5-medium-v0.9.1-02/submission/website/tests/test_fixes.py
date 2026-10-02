"""Tests for the October 2026 fixes: tax, prices, privacy, cancelling, gift cards, limits and holidays."""

import re
import unittest

from test_site import SiteTest


class FixesTest(SiteTest):
    def page(self, path, admin=False):
        return self.call("GET", path, admin=admin)

    def gift_card(self, pay=True):
        status, order = self.order(items=[{"sku": "GIFT25", "qty": 1}], customer={
            "name": "Gia", "email": "gia@example.com", "phone": "555-0101"})
        self.assertEqual(status, 201, order)
        _, html = self.page(order["confirmation_url"])
        code = re.search(r"Gift card code: <strong>([A-Z0-9-]+)</strong>", html)[1]
        if pay:
            self.assertEqual(self.call("POST", f"/admin/api/orders/{order['id']}/payment-received", {}, admin=True)[0], 200)
        return order, code

    def test_new_tax_rate_and_rounding(self):
        _, order = self.order()
        self.assertEqual((order["tax"], order["total"]), (1.49, 19.49))        # 8.25% of $18.00, half up

    def test_coupon_comes_off_before_tax(self):
        _, order = self.order(promo_code="WELCOME10")
        self.assertEqual((order["discount"], order["tax"], order["total"]), (1.8, 1.34, 17.54))
        _, quote = self.call("POST", "/api/quote", {"items": [{"sku": "BREAD9", "qty": 2}], "promo_code": "FIVEOFF"})
        self.assertEqual((quote["discount"], quote["tax"], quote["total"]), (5.0, 1.07, 14.07))

    def test_gift_cards_are_not_taxed_or_discounted(self):
        _, quote = self.call("POST", "/api/quote", {"items": [{"sku": "GIFT25", "qty": 1}], "promo_code": "FIVEOFF"})
        self.assertEqual((quote["discount"], quote["tax"], quote["total"]), (0.0, 0.0, 25.0))

    def test_browser_cannot_set_the_price(self):
        _, order = self.order(items=[{"sku": "CAKE48", "qty": 1, "unit_price": 0.01, "price": 0.01}],
                              pickup_date="2026-10-13")
        self.assertEqual(order["subtotal"], 48.0)

    def test_current_prices(self):
        _, menu = self.call("GET", "/api/menu")
        prices = {p["sku"]: p["price"] for p in menu["products"]}
        self.assertEqual(prices["CINNAMON325"], 3.5)
        self.assertEqual(prices["COFFEE18"], 16.5)                              # on sale until October 15

    def test_double_click_places_one_order(self):
        _, first = self.order(request_id="abc")
        _, second = self.order(request_id="abc")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.call("GET", "/admin/api/orders", admin=True)[1]["orders"]), 1)

    def test_order_details_need_the_private_link(self):
        _, gift = self.order(items=[{"sku": "GIFT25", "qty": 1}])
        _, html = self.page(f"/order/{gift['id']}")
        for secret in ("ana@example.com", "555-0100", "Ana", "Gift card code"):
            self.assertNotIn(secret, html)
        self.assertNotIn("customer", self.call("GET", f"/api/orders/{gift['id']}")[1])
        self.assertIn("Gift card code", self.page(gift["confirmation_url"])[1])

    def test_private_links_cannot_be_guessed(self):
        _, a = self.order()
        _, b = self.order()
        self.assertNotEqual(a["confirmation_url"].split("key=")[1], b["confirmation_url"].split("key=")[1])

    def test_cancel_needs_the_key(self):
        _, order = self.order()
        self.assertEqual(self.call("POST", f"/api/orders/{order['id']}/cancel", {})[0], 403)
        self.assertEqual(self.call("POST", f"/api/orders/{order['id']}/cancel", {"key": "nope"})[0], 403)
        key = order["confirmation_url"].split("key=")[1]
        status, cancelled = self.call("POST", f"/api/orders/{order['id']}/cancel", {"key": key})
        self.assertEqual((status, cancelled["status"]), (200, "cancelled"))

    def test_orders_export_needs_the_password(self):
        self.assertEqual(self.page("/admin/orders.csv")[0], 401)
        self.assertEqual(self.page("/admin/orders.csv", admin=True)[0], 200)

    def test_gift_card_works_only_once_paid_for(self):
        _, code = self.gift_card(pay=False)
        status, data = self.order(gift_card_code=code)
        self.assertEqual(status, 400, data)
        _, code = self.gift_card()
        status, order = self.order(gift_card_code=code)
        self.assertEqual((status, order["gift_card_applied"], order["amount_due"]), (201, 19.49, 0.0))

    def test_staff_cancel_puts_money_back_on_the_gift_card(self):
        _, code = self.gift_card()
        _, order = self.order(gift_card_code=code)
        self.assertEqual(self.call("POST", f"/admin/api/orders/{order['id']}/cancel", {}, admin=True)[0], 200)
        _, again = self.order(gift_card_code=code, items=[{"sku": "CROISSANT21", "qty": 2}])
        self.assertEqual(again["gift_card_applied"], 25.0)

    def test_cancelling_a_gift_card_order_voids_the_card(self):
        gift, code = self.gift_card(pay=False)
        key = gift["confirmation_url"].split("key=")[1]
        self.assertEqual(self.call("POST", f"/api/orders/{gift['id']}/cancel", {"key": key})[0], 200)
        self.assertIn("void", self.page(gift["confirmation_url"])[1])
        self.assertEqual(self.order(gift_card_code=code)[0], 400)

    def test_daily_limit_counts_the_pickup_day(self):
        cakes = {"items": [{"sku": "CAKE48", "qty": 6}], "pickup_date": "2026-10-13"}
        self.assertEqual(self.order(**cakes)[0], 201)
        self.assertEqual(self.order(**cakes, pickup_slot="11:00")[0], 409)
        self.assertEqual(self.order(items=cakes["items"], pickup_date="2026-10-14")[0], 201)
        _, menu = self.call("GET", "/api/menu?date=2026-10-13")
        self.assertTrue(next(p for p in menu["products"] if p["sku"] == "CAKE48")["sold_out"])

    def test_closed_on_holidays_and_mondays(self):
        for day in ("2026-11-26", "2026-12-25", "2026-10-12"):
            self.assertFalse(self.call("GET", f"/api/slots?date={day}")[1]["open"])
            self.assertEqual(self.order(pickup_date=day)[0], 400)

    def test_pickup_time_fills_up(self):
        for n in range(4):
            self.assertEqual(self.order(customer={"name": "A", "email": f"a{n}@example.com", "phone": ""})[0], 201)
        self.assertEqual(self.order()[0], 409)

    def test_newsletter_is_opt_in(self):
        self.assertNotIn("checked", self.page("/checkout")[1])
        self.assertFalse(self.order()[1]["newsletter"])

    def test_season_over_items_are_off_the_menu_page(self):
        self.assertNotIn("Seasonal Pie", self.page("/")[1])
        self.assertEqual(self.order(items=[{"sku": "PIE32", "qty": 1}])[0], 400)


if __name__ == "__main__":
    unittest.main()
