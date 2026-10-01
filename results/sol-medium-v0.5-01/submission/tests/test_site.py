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
                "pickup_date": "2026-10-10", "items": [{"sku": "BREAD9", "qty": 2}]}
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
        status, fetched = self.call("GET", f"/api/orders/{order['id']}")
        self.assertEqual(fetched, order)
        status, page = self.call("GET", f"/order/{order['id']}")
        self.assertIn("$19.44", page)

    def test_rejects_bad_orders(self):
        self.assertEqual(self.order(items=[])[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-01")[0], 400)
        self.assertEqual(self.order(customer={"name": "Ana", "email": "nope"})[0], 400)
        self.assertEqual(self.order(items=[{"sku": "BREAD9", "qty": 0}])[0], 400)
        self.assertEqual(self.order(promo_code="FREECAKE")[0], 400)

    def test_admin_requires_password_and_can_cancel(self):
        _, order = self.order()
        self.assertEqual(self.call("GET", "/admin/api/orders")[0], 401)
        status, data = self.call("GET", "/admin/api/orders", admin=True)
        self.assertEqual([o["id"] for o in data["orders"]], [order["id"]])
        status, cancelled = self.call("POST", f"/admin/api/orders/{order['id']}/cancel", admin=True)
        self.assertEqual(cancelled["status"], "cancelled")

    def test_discount_tax_gift_exclusion_and_half_up(self):
        _, order = self.order(items=[{"sku": "BREAD9", "qty": 2}, {"sku": "GIFT25", "qty": 1}], promo_code="WELCOME10")
        self.assertEqual((order['subtotal'], order['discount'], order['tax'], order['total']), (43, 1.8, 1.3, 42.5))
        _, order = self.order(items=[{"sku": "SCONE375", "qty": 1}], promo_code="WELCOME10")
        self.assertEqual((order['discount'], order['tax'], order['total']), (.38, .27, 3.64))
        _, order = self.order(items=[{"sku": "GIFT25", "qty": 1}], promo_code="FIVEOFF")
        self.assertEqual((order['discount'], order['tax'], order['total']), (0, 0, 25))

    def test_hours_lead_times_and_slot_capacity(self):
        self.assertEqual(self.order(pickup_date="2026-10-12", pickup_time="09:00")[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-10", pickup_time="15:00")[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-08", pickup_time="11:00")[0], 400)
        self.assertEqual(self.order(pickup_date="2026-10-08", pickup_time="11:30")[0], 201)
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_time="09:00")[0], 400)
        self.assertEqual(self.order(items=[{"sku": "CAKE48", "qty": 1}], pickup_time="09:30")[0], 201)
        for _ in range(4):
            self.assertEqual(self.order(pickup_time="12:00")[0], 201)
        self.assertEqual(self.order(pickup_time="12:00")[0], 400)

    def test_daily_limits_duplicates_and_cancel_release(self):
        for sku, limit in [('CAKE48', 6), ('CATER120', 4), ('PIE32', 8)]:
            status, order = self.order(items=[{'sku': sku, 'qty': limit}], pickup_time="13:00")
            self.assertEqual(status, 201)
            self.assertEqual(self.order(items=[{'sku': sku, 'qty': 1}], pickup_time="13:30")[0], 400)
            _, menu = self.call('GET', '/api/menu?date=2026-10-10')
            product = next(p for p in menu['products'] if p['sku'] == sku)
            self.assertTrue(product['sold_out'])
            self.assertEqual(product['remaining'], 0)
            self.assertEqual(self.call('POST', f"/api/orders/{order['id']}/cancel", {'cancel_token': order['cancel_token']})[0], 200)
        self.assertEqual(self.order(items=[{'sku': 'CAKE48', 'qty': 4}, {'sku': 'CAKE48', 'qty': 3}], pickup_time="14:00")[0], 400)

    def test_gift_card_quote_redemption_and_refund(self):
        _, purchase = self.order(items=[{'sku': 'GIFT25', 'qty': 1}])
        code = purchase['gift_cards'][0]['code']
        body = {'pickup_date': '2026-10-10', 'pickup_time': '10:00', 'items': [{'sku': 'BREAD9', 'qty': 2}],
                'promo_code': 'WELCOME10', 'gift_card_code': code.lower()}
        status, quote = self.call('POST', '/api/quote', body)
        self.assertEqual(status, 200)
        self.assertEqual((quote['total'], quote['gift_card_applied'], quote['amount_due'], quote['gift_card_balance']), (17.5, 17.5, 0, 7.5))
        self.call('POST', '/api/quote', body)
        _, fetched = self.call('GET', f"/api/orders/{purchase['id']}")
        self.assertEqual(fetched['gift_cards'][0]['balance'], 25)
        status, order = self.order(**body)
        self.assertEqual(status, 201)
        for key, value in quote.items():
            self.assertEqual(order[key], value)
        self.assertEqual(self.call('POST', f"/api/orders/{purchase['id']}/cancel", {'cancel_token': purchase['cancel_token']})[0], 400)
        _, second = self.order(gift_card_code=code)
        self.assertEqual((second['gift_card_applied'], second['amount_due'], second['gift_card_balance']), (7.5, 11.94, 0))
        self.assertEqual(self.order(gift_card_code=code)[0], 400)
        for _ in range(2):
            self.assertEqual(self.call('POST', f"/api/orders/{order['id']}/cancel", {'cancel_token': order['cancel_token']})[0], 200)
        _, fetched = self.call('GET', f"/api/orders/{purchase['id']}")
        self.assertEqual(fetched['gift_cards'][0]['balance'], 17.5)

    def test_cancel_day_and_bad_token(self):
        _, order = self.order(pickup_date="2026-10-08", pickup_time="12:00")
        path = f"/api/orders/{order['id']}/cancel"
        self.assertEqual(self.call('POST', path, {'cancel_token': 'wrong'})[0], 400)
        self.assertEqual(self.call('POST', path, {'cancel_token': order['cancel_token']})[0], 400)
        self.assertEqual(self.call('POST', f"/admin/api/orders/{order['id']}/cancel", admin=True)[0], 200)

    def test_admin_sorted_by_time_and_templates(self):
        _, late = self.order(pickup_time="14:00")
        _, early = self.order(pickup_time="08:00")
        _, data = self.call('GET', '/admin/api/orders', admin=True)
        self.assertEqual([o['id'] for o in data['orders']], [early['id'], late['id']])
        status, page = self.call('GET', '/admin', admin=True)
        self.assertEqual(status, 200)
        self.assertIn('14:00', page)
        status, page = self.call('GET', '/checkout')
        self.assertEqual(status, 200)
        self.assertIn('gift_card_code', page)
        self.assertIn('pickup_time', page)

    def test_concurrent_capacity_and_balance(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.order(pickup_time="14:30"), range(8)))
        self.assertEqual(sum(status == 201 for status, _ in results), 4)
        _, purchase = self.order(items=[{'sku': 'GIFT25', 'qty': 1}])
        code = purchase['gift_cards'][0]['code']
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda n: self.order(gift_card_code=code, pickup_time=f"{9+n}:30".zfill(5)), range(4)))
        self.assertEqual(sum(o['gift_card_applied'] for status, o in results if status == 201), 25)
        _, fetched = self.call('GET', f"/api/orders/{purchase['id']}")
        self.assertEqual(fetched['gift_cards'][0]['balance'], 0)

    def test_invalid_payloads_and_no_partial_writes(self):
        for body in (None, [], {'customer': []}, {'customer': 'bad'}):
            self.assertEqual(self.call('POST', '/api/orders', body)[0], 400)
        self.assertEqual(self.order(gift_card_code='INVALID')[0], 400)
        self.assertEqual(self.order(items=[{'sku': 'CAKE48', 'qty': 7}], pickup_time='12:00')[0], 400)
        _, data = self.call('GET', '/admin/api/orders', admin=True)
        self.assertEqual(data['orders'], [])


if __name__ == "__main__":
    unittest.main()
