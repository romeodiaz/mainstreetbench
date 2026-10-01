"""Existing behavior that every change must keep working."""

from harness import SATURDAY, SiteCase


class Regression(SiteCase):
    def test_menu_api_and_page(self):
        status, data = self.call("GET", "/api/menu")
        self.assertEqual(status, 200)
        skus = {p["sku"]: p for p in data["products"]}
        self.assertEqual(len(skus), 12)
        self.assertEqual(skus["BREAD9"]["price"], 9.0)
        self.assertEqual(skus["GIFT25"]["category"], "Gift Cards")
        status, page = self.call("GET", "/")
        self.assertEqual(status, 200)
        for sku in skus:
            self.assertIn(f'data-sku="{sku}"', page)

    def test_simple_order_is_priced_and_saved(self):
        status, order = self.place()
        self.assertEqual(status, 201, order)
        self.assertEqual(order["status"], "placed")
        self.assertEqual(order["pickup_date"], SATURDAY)
        self.assertEqual([(i["sku"], i["qty"]) for i in order["items"]], [("BREAD9", 2)])
        self.assertMoney(order["subtotal"], "18.00")
        self.assertMoney(order["discount"], "0")
        self.assertMoney(order["tax"], "1.44")
        self.assertMoney(order["total"], "19.44")
        status, fetched = self.call("GET", f"/api/orders/{order['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["total"], order["total"])
        status, page = self.call("GET", f"/order/{order['id']}")
        self.assertEqual(status, 200)
        self.assertIn("$19.44", page)

    def test_invalid_orders_are_rejected(self):
        cases = [
            {"items": []},
            {"items": [{"sku": "NOPE", "qty": 1}]},
            {"items": [{"sku": "BREAD9", "qty": 0}]},
            {"items": [{"sku": "BREAD9", "qty": 51}]},
            {"customer": {"name": "", "email": "ana@example.com"}},
            {"customer": {"name": "Ana", "email": "not-an-email"}},
            {"pickup_date": "2026-10-01"},
            {"promo_code": "FREECAKE"},
        ]
        from harness import order_body
        for change in cases:
            with self.subTest(change=change):
                body = order_body()
                body.update(change)
                status, data = self.call("POST", "/api/orders", body)
                self.assertEqual(status, 400, data)
                self.assertIsInstance(data.get("error"), str)
        self.assertEqual(self.admin_orders(), [])

    def test_admin_requires_auth_and_can_cancel(self):
        _, order = self.place()
        self.assertEqual(self.call("GET", "/admin/api/orders")[0], 401)
        self.assertEqual(self.call("GET", "/admin")[0], 401)
        self.assertEqual(self.call("POST", f"/admin/api/orders/{order['id']}/cancel")[0], 401)
        self.assertEqual([o["id"] for o in self.admin_orders()], [order["id"]])
        status, page = self.call("GET", "/admin", admin=True)
        self.assertEqual(status, 200)
        self.assertIn(f'data-order-id="{order["id"]}"', page)
        status, cancelled = self.call("POST", f"/admin/api/orders/{order['id']}/cancel", admin=True)
        self.assertEqual((status, cancelled["status"]), (200, "cancelled"))

    def test_unknown_routes_and_pages(self):
        self.assertEqual(self.call("GET", "/api/orders/9999")[0], 404)
        self.assertEqual(self.call("GET", "/no-such-page")[0], 404)
        self.assertEqual(self.call("GET", "/checkout")[0], 200)
        self.assertEqual(self.call("GET", "/static/style.css")[0], 200)
