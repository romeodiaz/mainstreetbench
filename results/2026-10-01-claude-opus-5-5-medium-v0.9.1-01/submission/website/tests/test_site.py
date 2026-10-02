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

    def test_october_tax_rate_and_coupon_lowers_tax(self):
        status, order = self.order(promo_code="WELCOME10", items=[{"sku": "BREAD9", "qty": 10}])
        self.assertEqual(status, 201, order)
        self.assertEqual((order["subtotal"], order["discount"], order["tax"], order["total"]), (90.0, 9.0, 6.68, 87.68))

    def test_browser_cannot_set_prices(self):
        status, order = self.order(items=[{"sku": "GIFT25", "qty": 1, "unit_price": 0.01}])
        self.assertEqual(status, 201, order)
        self.assertEqual(order["total"], 25.0)

    def test_current_prices(self):
        prices = {p["sku"]: p["price"] for p in self.call("GET", "/api/menu")[1]["products"]}
        self.assertEqual(prices["CINNAMON325"], 3.5)
        self.assertEqual(prices["COFFEE18"], 16.5)   # on sale through Oct 15
        self.assertNotIn("PIE32", prices)            # season ended Sept 30

    def test_closed_on_holidays(self):
        self.assertFalse(self.call("GET", "/api/slots?date=2026-11-26")[1]["open"])
        self.assertEqual(self.order(pickup_date="2026-11-26")[0], 400)

    def test_cake_limit_counts_pickup_day(self):
        for n in range(6):
            status, _ = self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_date="2026-10-16",
                                   pickup_slot=["09:00", "10:00"][n % 2] if n < 4 else "11:00")
            self.assertEqual(status, 201)
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_date="2026-10-16",
                                    pickup_slot="12:00")[0], 409)

    def test_same_request_id_makes_one_order(self):
        first = self.order(request_id="abc")[1]
        second = self.order(request_id="abc")[1]
        self.assertEqual(first["id"], second["id"])

    def test_private_details_need_the_key(self):
        status, order = self.order(items=[{"sku": "GIFT25", "qty": 1}])
        status, page = self.call("GET", f"/order/{order['id']}")
        self.assertNotIn("ana@example.com", page)
        self.assertNotIn("555-0100", page)
        self.assertEqual(self.call("POST", f"/api/orders/{order['id']}/cancel", {"key": "wrong"})[0], 403)
        self.assertEqual(self.call("GET", "/admin/orders.csv")[0], 401)
        key = order["confirmation_url"].split("key=")[1]
        status, cancelled = self.call("POST", f"/api/orders/{order['id']}/cancel", {"key": key})
        self.assertEqual(cancelled["status"], "cancelled")

    def test_staff_cancel_refunds_gift_card(self):
        _, bought = self.order(items=[{"sku": "GIFT25", "qty": 1}])
        page = self.call("GET", bought["confirmation_url"])[1]
        code = page.split("Gift card code: <strong>")[1].split("<")[0]
        _, spent = self.order(items=[{"sku": "BREAD9", "qty": 1}], gift_card_code=code)
        self.assertEqual(spent["gift_card_applied"], 9.74)
        self.call("POST", f"/admin/api/orders/{spent['id']}/cancel", admin=True)
        self.assertEqual(self.call("POST", "/api/quote", {"items": [{"sku": "GIFT25", "qty": 1}],
                                                          "gift_card_code": code})[1]["gift_card_applied"], 25.0)


if __name__ == "__main__":
    unittest.main()
