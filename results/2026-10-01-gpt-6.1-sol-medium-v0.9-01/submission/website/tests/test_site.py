"""Smoke tests: start the real server and talk to it over HTTP."""

import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-10-08T09:10:00"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SiteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.port = free_port()
        env = {**os.environ, "CORNERLOAF_NOW": NOW, "ADMIN_PASSWORD": "test"}
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "bakery.server", "--port", str(self.port), "--db", f"{self.tmp.name}/t.db"],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.1).close()
                break
            except OSError:
                time.sleep(0.05)

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait()
        self.tmp.cleanup()

    def call(self, method, path, body=None, admin=False):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method,
                                         data=None if body is None else json.dumps(body).encode())
        request.add_header("Content-Type", "application/json")
        if admin:
            request.add_header("Authorization", "Basic " + base64.b64encode(b"staff:test").decode())
        try:
            with urllib.request.urlopen(request) as response:
                raw, status = response.read(), response.status
        except urllib.error.HTTPError as error:
            raw, status = error.read(), error.code
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw.decode()

    def order(self, **overrides):
        body = {"customer": {"name": "Ana", "email": "ana@example.com", "phone": "555-0100"},
                "pickup_date": "2026-10-10", "pickup_slot": "10:00", "items": [{"sku": "BREAD9", "qty": 2}]}
        body.update(overrides)
        return self.call("POST", "/api/orders", body)

    def test_menu(self):
        status, data = self.call("GET", "/api/menu")
        self.assertEqual(status, 200)
        self.assertIn("BREAD9", [p["sku"] for p in data["products"]])

    def test_place_order(self):
        status, order = self.order()
        self.assertEqual(status, 201, order)
        self.assertEqual(order["subtotal"], 18.0)

    def test_admin_needs_password(self):
        self.assertEqual(self.call("GET", "/admin/api/orders")[0], 401)
        self.assertEqual(self.call("GET", "/admin/api/orders", admin=True)[0], 200)

    def test_tax_discount_and_trusted_prices(self):
        status, data = self.call("POST", "/api/quote", {"items": [
            {"sku": "BREAD9", "qty": 2, "price": -100},
            {"sku": "GIFT25", "qty": 1, "unit_price": 0.01}], "promo_code": "WELCOME10"})
        self.assertEqual(status, 200)
        self.assertEqual((data["subtotal"], data["discount"], data["tax"], data["total"]),
                         (43.0, 1.8, 1.34, 42.54))
        status, order = self.order(items=[{"sku": "BREAD9", "qty": 2, "unit_price": 0.01}], promo_code="WELCOME10")
        self.assertEqual(status, 201)
        self.assertEqual(order["total"], 17.54)

    def test_idempotent_order(self):
        first = self.order(request_id="same-request")
        second = self.order(request_id="same-request")
        self.assertEqual(first, second)
        self.assertEqual(len(self.call("GET", "/admin/api/orders", admin=True)[1]["orders"]), 1)

    def test_private_pages_and_export(self):
        _, order = self.order(customer={"name": "PRIVATE NAME", "email": "private@example.com", "phone": "5551234567"})
        status, page = self.call("GET", f"/order/{order['id']}")
        self.assertEqual(status, 200)
        self.assertNotIn("PRIVATE NAME", page)
        self.assertNotIn("private@example.com", page)
        self.assertNotIn("5551234567", page)
        self.assertEqual(self.call("GET", "/admin/orders.csv")[0], 401)
        self.assertIn("PRIVATE NAME", self.call("GET", "/admin/orders.csv", admin=True)[1])
        self.assertIn("PRIVATE NAME", self.call("GET", order["confirmation_url"])[1])

    def test_cancellation_key_and_notice(self):
        _, order = self.order(pickup_date="2026-10-11")
        path = f"/api/orders/{order['id']}/cancel"
        self.assertEqual(self.call("POST", path, {})[0], 403)
        self.assertEqual(self.call("POST", path, {"key": "wrong"})[0], 403)
        key = order["confirmation_url"].split("key=")[1]
        self.assertEqual(self.call("POST", path, {"key": key})[1]["status"], "cancelled")
        _, soon = self.order(pickup_date="2026-10-09")
        self.assertEqual(self.call("POST", f"/api/orders/{soon['id']}/cancel",
                                  {"key": soon["confirmation_url"].split("key=")[1]})[0], 400)

    def test_holidays_season_and_long_notice(self):
        for day in ["2026-11-26", "2026-12-25", "2026-10-12"]:
            self.assertFalse(self.call("GET", f"/api/slots?date={day}")[1]["open"])
            self.assertEqual(self.order(pickup_date=day)[0], 400)
        self.assertEqual(self.order(items=[{"sku": "PIE32", "qty": 1}])[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-09", items=[{"sku": "CATER120", "qty": 1}])[0], 400)
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}],
                                    customer={"name": "Ana", "email": "ana@example.com"})[0], 400)

    def test_daily_limits_use_pickup_day_and_free_on_cancel(self):
        _, first = self.order(items=[{"sku": "CAKE48", "qty": 6}], pickup_date="2026-10-11")
        products = self.call("GET", "/api/menu?date=2026-10-11")[1]["products"]
        cake = next(p for p in products if p["sku"] == "CAKE48")
        self.assertEqual(cake["remaining"], 0)
        self.assertTrue(cake["sold_out"])
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_date="2026-10-11")[0], 409)
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_date="2026-10-14")[0], 201)
        self.call("POST", f"/admin/api/orders/{first['id']}/cancel", {}, admin=True)
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_date="2026-10-11")[0], 201)

    def test_slot_capacity(self):
        for i in range(4):
            self.assertEqual(self.order()[0], 201)
        self.assertEqual(self.order()[0], 409)

    def test_coupon_restrictions(self):
        self.assertEqual(self.order(promo_code="WELCOME10")[0], 201)
        self.assertEqual(self.order(promo_code="WELCOME10")[0], 400)
        for code in ["STAFF50", "FALL15"]:
            self.assertEqual(self.order(promo_code=code)[0], 400)
        status, data = self.call("POST", "/api/quote", {"items": [{"sku": "BREAD9", "qty": 1}], "promo_code": "FIVEOFF"})
        self.assertEqual(data["total"], 4.33)

    def gift_code(self, order):
        import re
        page = self.call("GET", order["confirmation_url"])[1]
        return re.search(r"Gift card code: <strong>([^<]+)</strong>", page)[1]

    def test_gift_card_payment_cancel_restore_and_repeat(self):
        _, purchase = self.order(items=[{"sku": "GIFT25", "qty": 1}], pickup_date="2026-10-11")
        code = self.gift_code(purchase)
        self.assertNotIn(code, self.call("GET", f"/order/{purchase['id']}")[1])
        self.assertEqual(self.order(gift_card_code=code, pickup_date="2026-10-14")[0], 400)
        self.call("POST", f"/admin/api/orders/{purchase['id']}/payment-received", {}, admin=True)
        _, redeemed = self.order(gift_card_code=code, pickup_date="2026-10-14")
        self.assertEqual(redeemed["gift_card_applied"], 19.49)
        self.assertEqual(redeemed["amount_due"], 0)
        for i in range(2):
            self.assertEqual(self.call("POST", f"/admin/api/orders/{redeemed['id']}/cancel", {}, admin=True)[0], 200)
        _, new = self.order(gift_card_code=code, pickup_date="2026-10-17", items=[{"sku": "BREAD9", "qty": 3}])
        self.assertEqual(new["gift_card_applied"], 25)
        self.assertEqual(self.call("POST", f"/admin/api/orders/{purchase['id']}/cancel", {}, admin=True)[0], 409)

    def test_cancelled_gift_purchase_is_void(self):
        _, purchase = self.order(items=[{"sku": "GIFT25", "qty": 1}], pickup_date="2026-10-11")
        code = self.gift_code(purchase)
        key = purchase["confirmation_url"].split("key=")[1]
        self.assertEqual(self.call("POST", f"/api/orders/{purchase['id']}/cancel", {"key": key})[0], 200)
        self.assertEqual(self.order(gift_card_code=code, pickup_date="2026-10-14")[0], 400)
        self.assertEqual(self.call("POST", f"/admin/api/orders/{purchase['id']}/payment-received", {}, admin=True)[0], 409)

    def test_current_catalog_and_bad_input(self):
        products = self.call("GET", "/api/menu")[1]["products"]
        self.assertEqual(next(p for p in products if p["sku"] == "CINNAMON325")["price"], 3.50)
        self.assertEqual(next(p for p in products if p["sku"] == "COFFEE18")["price"], 16.50)
        self.assertEqual(self.order(customer=[])[0], 400)
        self.assertEqual(self.order(customer=["invalid"])[0], 400)
        self.assertEqual(self.order(items=[{"sku": "BREAD9", "qty": True}])[0], 400)
        self.assertEqual(self.order(items=[{"sku": "BREAD9", "qty": 30}, {"sku": "BREAD9", "qty": 30}])[0], 400)

    def test_paid_and_cancelled_orders_have_no_amount_to_collect(self):
        _, order = self.order(pickup_date="2026-10-11")
        _, paid = self.call("POST", f"/admin/api/orders/{order['id']}/payment-received", {}, admin=True)
        self.assertTrue(paid["payment_received"])
        self.assertEqual(paid["amount_due"], 0)
        key = order["confirmation_url"].split("key=")[1]
        self.assertEqual(self.call("POST", f"/api/orders/{order['id']}/cancel", {"key": key})[0], 400)
        _, cancelled = self.call("POST", f"/admin/api/orders/{order['id']}/cancel", {}, admin=True)
        self.assertEqual(cancelled["amount_due"], 0)

    def test_concurrent_first_order_coupon(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.order(promo_code="WELCOME10"), range(2)))
        self.assertEqual(sorted(status for status, _ in results), [201, 400])

    def test_price_and_tax_effective_dates(self):
        import datetime as dt
        from unittest.mock import patch
        from bakery.server import current_price
        from bakery.settings import tax_rate
        from decimal import Decimal
        product = {"sku": "COFFEE18", "price": 16.50}
        for date, expected in [("2026-09-19", 18.00), ("2026-09-20", 16.50), ("2026-10-15", 16.50), ("2026-10-16", 18.00)]:
            with patch("bakery.clock.today", return_value=dt.date.fromisoformat(date)):
                self.assertEqual(current_price(product), expected)
        self.assertEqual(tax_rate(dt.date(2026, 9, 30)), Decimal(".08"))
        self.assertEqual(tax_rate(dt.date(2026, 10, 1)), Decimal(".0825"))


if __name__ == "__main__":
    unittest.main()
