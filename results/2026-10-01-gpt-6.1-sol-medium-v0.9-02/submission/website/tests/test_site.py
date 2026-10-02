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

    def test_public_views_and_export_protect_details(self):
        _, order = self.order(customer={"name": "Private Customer", "email": "private@example.com", "phone": "5550104242"})
        oid = order["id"]
        self.assertNotIn("customer", self.call("GET", f"/api/orders/{oid}")[1])
        page = self.call("GET", f"/order/{oid}")[1]
        self.assertNotIn("Private Customer", page)
        self.assertNotIn("private@example.com", page)
        self.assertEqual(self.call("GET", "/admin/orders.csv")[0], 401)
        self.assertIn("amount_due", self.call("GET", "/admin/orders.csv", admin=True)[1])
        self.assertEqual(self.call("GET", order["confirmation_url"])[0], 200)

    def test_staff_cancel_undoes_gift_credit(self):
        _, source = self.order(items=[{"sku": "GIFT25", "qty": 1}])
        self.call("POST", f"/admin/api/orders/{source['id']}/payment-received", {}, admin=True)
        _, page = self.call("GET", source["confirmation_url"])
        import re
        code = re.search(r"Gift card code: <strong>([^<]+)", page)[1]
        _, order = self.order(items=[{"sku": "CAKE48", "qty": 1}], gift_card_code=code)
        self.assertEqual(order["gift_card_applied"], 25)
        self.assertEqual(self.call("POST", f"/admin/api/orders/{order['id']}/cancel", {}, admin=True)[0], 200)
        _, q = self.call("POST", "/api/quote", {"items": [{"sku": "BREAD9", "qty": 3}], "gift_card_code": code})
        self.assertEqual(q["gift_card_applied"], 25)

    def test_admin_needs_password(self):
        self.assertEqual(self.call("GET", "/admin/api/orders")[0], 401)
        self.assertEqual(self.call("GET", "/admin/api/orders", admin=True)[0], 200)


if __name__ == "__main__":
    unittest.main()
