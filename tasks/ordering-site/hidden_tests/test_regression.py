"""Existing behavior that must keep working after all five tickets."""

from harness import SATURDAY, LegacyCase, SiteCase


class Regression(SiteCase):
    def test_menu_lists_every_product(self):
        status, data = self.call("GET", "/api/menu")
        self.assertEqual(status, 200)
        skus = {p["sku"]: p for p in data["products"]}
        self.assertEqual(len(skus), 12)
        self.assertEqual((skus["BREAD9"]["price"], skus["GIFT25"]["category"]), (9.0, "Gift Cards"))
        status, page = self.call("GET", "/")
        for sku in skus:
            self.assertIn(f'data-sku="{sku}"', page)

    def test_customer_can_order_and_see_confirmation(self):
        attempt = self.placed([("BREAD9", 2)], slot="10:00")
        order = self.saved(attempt.order_id)
        self.assertEqual((order["status"], order["pickup_date"]), ("placed", SATURDAY))
        self.assertEqual([(i["sku"], i["qty"]) for i in order["items"]], [("BREAD9", 2)])
        for field, expected in (("subtotal", "18.00"), ("discount", "0"), ("tax", "1.44"), ("total", "19.44")):
            self.assertMoney(order[field], expected, field)
        self.assertIn("$19.44", attempt.text)

    def test_bad_promo_code_is_refused(self):
        attempt = self.refused([("BREAD9", 1)], promo="FREECAKE")
        self.assertRegex(attempt.text, r"(?i)promo|code|valid")

    def test_admin_needs_password_and_can_cancel(self):
        attempt = self.placed()
        self.assertEqual(self.call("GET", "/admin/api/orders")[0], 401)
        self.assertEqual(self.call("GET", "/admin")[0], 401)
        self.assertEqual(self.call("POST", f"/admin/api/orders/{attempt.order_id}/cancel")[0], 401)
        status, page = self.call("GET", "/admin", admin=True)
        self.assertEqual(status, 200)
        self.assertIn(f'data-order-id="{attempt.order_id}"', page)
        status, cancelled = self.call("POST", f"/admin/api/orders/{attempt.order_id}/cancel", admin=True)
        self.assertEqual((status, cancelled["status"]), (200, "cancelled"))

    def test_customer_names_are_shown_as_text(self):
        self.placed(name="Ana <b>Bold</b>")
        self.assertNotIn("<b>Bold</b>", self.call("GET", "/admin", admin=True)[1])

    def test_pages_and_missing_things(self):
        self.assertEqual(self.call("GET", "/checkout")[0], 200)
        self.assertEqual(self.call("GET", "/static/style.css")[0], 200)
        self.assertEqual(self.call("GET", "/no-such-page")[0], 404)
        self.assertEqual(self.call("GET", "/api/orders/9999")[0], 404)


class PastOrdersKeepTheirTotals(LegacyCase):
    def test_existing_orders_are_not_repriced(self):
        # Legacy orders were charged under the old rules; they are history, not quotes.
        saved = {o["id"]: o for o in self.admin_orders()}
        for old in self.legacy_orders:
            with self.subTest(order=old["id"]):
                for field in ("subtotal", "discount", "tax", "total"):
                    self.assertEqual(saved[old["id"]][field], old[field], field)
