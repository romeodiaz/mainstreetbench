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
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.1).close()
                break
            except OSError:
                time.sleep(0.05)

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait()
        self.proc.stderr.close()
        self.tmp.cleanup()

    def call(self, method, path, body=None, admin=False):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method,
                                         data=None if body is None else json.dumps(body).encode())
        request.add_header("Content-Type", "application/json")
        if admin:
            request.add_header("Authorization", "Basic " + base64.b64encode(b"staff:test").decode())
        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read()
                status = response.status
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

    def test_menu_lists_products(self):
        status, data = self.call("GET", "/api/menu")
        self.assertEqual(status, 200)
        self.assertIn("BREAD9", [p["sku"] for p in data["products"]])
        status, page = self.call("GET", "/")
        self.assertIn('data-sku="CAKE48"', page)

    def test_place_and_fetch_order(self):
        status, order = self.order()
        self.assertEqual(status, 201)
        self.assertEqual((order["subtotal"], order["tax"], order["total"]), (18.0, 1.44, 19.44))
        link = order.pop("confirmation_url")
        status, fetched = self.call("GET", f"/api/orders/{order['id']}")
        self.assertEqual(fetched, order)
        status, page = self.call("GET", link)
        self.assertIn("$19.44", page)
        self.assertNotIn("$19.44", self.call("GET", f"/order/{order['id']}")[1])

    def test_gift_cards_and_cancellation(self):
        _, bought = self.order(items=[{"sku": "GIFT25", "qty": 1}])
        page = self.call("GET", bought["confirmation_url"])[1]
        code = page.split("Gift card code: <strong>")[1].split("<")[0]
        _, paid = self.order(pickup_slot="11:00", gift_card_code=code)
        self.assertEqual((paid["tax"], paid["gift_card_applied"], paid["amount_due"]), (1.44, 19.44, 0.0))
        key = paid["confirmation_url"].split("key=")[1]
        self.assertEqual(self.call("POST", f"/api/orders/{paid['id']}/cancel", {"key": "wrong"})[0], 403)
        self.assertEqual(self.call("POST", f"/api/orders/{paid['id']}/cancel", {"key": key})[0], 200)
        _, again = self.order(pickup_slot="11:30", items=[{"sku": "CAKE48", "qty": 1}], gift_card_code=code)
        self.assertEqual(again["gift_card_applied"], 25.0)

    def test_rejects_bad_orders(self):
        self.assertEqual(self.order(items=[])[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-01")[0], 400)
        self.assertEqual(self.order(customer={"name": "Ana", "email": "nope"})[0], 400)
        self.assertEqual(self.order(items=[{"sku": "BREAD9", "qty": 0}])[0], 400)
        self.assertEqual(self.order(promo_code="FREECAKE")[0], 400)
        self.assertEqual(self.order(pickup_slot="07:15")[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-12")[0], 400)

    def test_slot_capacity_and_daily_limits(self):
        for n in range(4):
            self.assertEqual(self.order()[0], 201)
        self.assertEqual(self.order()[0], 409)
        status, error = self.order(pickup_slot="11:00", items=[{"sku": "CAKE48", "qty": 7}])
        self.assertEqual((status, error["sku"], error["remaining"]), (409, "CAKE48", 6))

    def test_admin_requires_password_and_can_cancel(self):
        _, order = self.order()
        self.assertEqual(self.call("GET", "/admin/api/orders")[0], 401)
        status, data = self.call("GET", "/admin/api/orders", admin=True)
        self.assertEqual([o["id"] for o in data["orders"]], [order["id"]])
        status, cancelled = self.call("POST", f"/admin/api/orders/{order['id']}/cancel", admin=True)
        self.assertEqual(cancelled["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
