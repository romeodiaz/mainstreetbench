"""Smoke tests: start the real server and talk to it over HTTP."""

import base64
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
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
        self.assertEqual(fetched, {k: v for k, v in order.items() if k not in ("cancel_token", "order_url")})
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

    def test_coupon_food_only_and_gift_tax(self):
        status, order = self.order(items=[{'sku': 'BREAD9', 'qty': 1}, {'sku': 'GIFT25', 'qty': 1}], promo_code='WELCOME10')
        self.assertEqual(status, 201)
        self.assertEqual((order['subtotal'], order['discount'], order['tax'], order['total']), (34, .9, .65, 33.75))
        self.assertEqual(len(order['gift_cards']), 1)
        _, gift = self.order(items=[{'sku': 'GIFT25', 'qty': 1}], promo_code='FIVEOFF')
        self.assertEqual((gift['discount'], gift['tax'], gift['total']), (0, 0, 25))

    def test_pickup_rules_and_availability(self):
        self.assertEqual(self.order(pickup_date='2026-10-12')[0], 400)  # Monday
        self.assertEqual(self.order(pickup_date='2026-10-08', pickup_time='11:00')[0], 400)
        self.assertEqual(self.order(pickup_date='2026-10-08', pickup_time='11:30')[0], 201)
        for time in ['06:30', '15:00', '12:15', '', 12]:
            self.assertEqual(self.order(pickup_time=time)[0], 400)
        cake = [{'sku': 'CAKE48', 'qty': 1}]
        self.assertEqual(self.order(items=cake, pickup_time='09:00')[0], 400)
        self.assertEqual(self.order(items=cake, pickup_time='09:30')[0], 201)
        self.assertEqual(self.order(items=cake, pickup_date='2026-10-09', pickup_time='14:30')[0], 400)
        status, data = self.call('GET', '/api/pickup-times?date=2026-10-10&skus=CAKE48')
        self.assertEqual(status, 200)
        self.assertEqual(data['times'][0]['time'], '09:30')
        self.assertEqual(data['remaining']['CAKE48'], 5)

    def test_concurrent_slots_and_release(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.order(pickup_time='12:00'), range(8)))
        self.assertEqual(sum(status == 201 for status, _ in results), 4)
        order = next(o for status, o in results if status == 201)
        path = f"/api/orders/{order['id']}/cancel"
        self.assertEqual(self.call('POST', path, {'cancel_token': 'wrong☃'})[0], 400)
        self.assertEqual(self.call('POST', path, {'cancel_token': order['cancel_token']})[0], 200)
        self.assertEqual(self.order(pickup_time='12:00')[0], 201)

    def test_daily_limits_duplicates_and_cancel(self):
        for sku, limit in [('CAKE48', 6), ('CATER120', 4), ('PIE32', 8)]:
            status, order = self.order(items=[{'sku': sku, 'qty': limit}])
            self.assertEqual(status, 201)
            status, error = self.order(items=[{'sku': sku, 'qty': 1}])
            self.assertEqual(status, 400)
            self.assertIn('sold out', error['error'])
            self.call('POST', f"/api/orders/{order['id']}/cancel", {'cancel_token': order['cancel_token']})
            self.assertEqual(self.order(items=[{'sku': sku, 'qty': limit}, {'sku': sku, 'qty': 1}])[0], 400)
            self.assertEqual(self.order(items=[{'sku': sku, 'qty': limit}])[0], 201)

    def test_concurrent_daily_limit(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda n: self.order(items=[{'sku':'CAKE48', 'qty':1}],
                                                        pickup_time=f'{10+n//2:02d}:{30*(n%2):02d}'), range(8)))
        self.assertEqual(sum(status == 201 for status, _ in results), 6)

    def test_gift_spending_refund_and_void(self):
        _, bought = self.order(items=[{'sku': 'GIFT25', 'qty': 1}])
        self.call('POST', f"/admin/api/orders/{bought['id']}/activate-gift-cards", admin=True)
        code = bought['gift_cards'][0]['code']
        _, paid = self.order(gift_card_code=code)
        self.assertEqual((paid['gift_card_applied'], paid['gift_card_balance'], paid['amount_due']), (19.44, 5.56, 0))
        self.assertEqual(self.call('POST', f"/api/orders/{bought['id']}/cancel", {'cancel_token': bought['cancel_token']})[0], 400)
        path = f"/api/orders/{paid['id']}/cancel"
        for _ in range(2):
            self.assertEqual(self.call('POST', path, {'cancel_token': paid['cancel_token']})[0], 200)
        _, next_order = self.order(gift_card_code=code)
        self.assertEqual(next_order['gift_card_balance'], 5.56)  # refund happened exactly once
        self.call('POST', f"/api/orders/{next_order['id']}/cancel", {'cancel_token': next_order['cancel_token']})
        self.assertEqual(self.call('POST', f"/api/orders/{bought['id']}/cancel", {'cancel_token': bought['cancel_token']})[0], 200)
        self.assertEqual(self.order(gift_card_code=code)[0], 400)

    def test_concurrent_card_spending(self):
        _, bought = self.order(items=[{'sku': 'GIFT25', 'qty': 1}])
        self.call('POST', f"/admin/api/orders/{bought['id']}/activate-gift-cards", admin=True)
        code = bought['gift_cards'][0]['code']
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.order(gift_card_code=code), range(4)))
        orders = [o for status, o in results if status == 201]
        self.assertEqual(sum(o['gift_card_applied'] for o in orders), 25)
        self.assertTrue(all(o['gift_card_balance'] >= 0 for o in orders))
        self.assertEqual(len(orders), 2)

    def test_private_order_page_and_cutoff(self):
        _, bought = self.order(items=[{'sku': 'GIFT25', 'qty': 1}])
        self.call('POST', f"/admin/api/orders/{bought['id']}/activate-gift-cards", admin=True)
        code = bought['gift_cards'][0]['code']
        _, public = self.call('GET', f"/order/{bought['id']}")
        self.assertNotIn(code, public)
        _, private = self.call('GET', bought['order_url'])
        self.assertIn(code, private)
        self.assertIn('cancel-order', private)
        _, same_day = self.order(pickup_date='2026-10-08', pickup_time='12:00')
        self.assertEqual(self.call('POST', f"/api/orders/{same_day['id']}/cancel", {'cancel_token': same_day['cancel_token']})[0], 400)
        self.assertEqual(self.call('POST', f"/admin/api/orders/{same_day['id']}/cancel", admin=True)[0], 200)

    def test_gift_activation_requires_payment_and_staff(self):
        _, bought = self.order(items=[{'sku': 'GIFT25', 'qty': 2}])
        self.assertEqual(len(bought['gift_cards']), 2)
        self.assertFalse(bought['gift_cards'][0]['active'])
        code = bought['gift_cards'][0]['code']
        self.assertEqual(self.order(gift_card_code=code)[0], 400)
        path = f"/admin/api/orders/{bought['id']}/activate-gift-cards"
        self.assertEqual(self.call('POST', path)[0], 401)
        self.assertEqual(self.call('POST', path, admin=True)[0], 200)
        self.assertEqual(self.order(gift_card_code=code)[0], 201)

    def test_register_existing_gift_card(self):
        _, bought = self.order(items=[{'sku': 'GIFT25', 'qty': 1}])
        # Simulate a historical purchase with no digital card, as in the original schema.
        with sqlite3.connect(f'{self.tmp.name}/t.db') as conn:
            conn.execute('DELETE FROM gift_cards WHERE order_id=?', (bought['id'],))
        payload = {'order_id': bought['id'], 'code': 'OLD-123', 'balance': '12.50'}
        self.assertEqual(self.call('POST', '/admin/api/gift-cards', payload)[0], 401)
        self.assertEqual(self.call('POST', '/admin/api/gift-cards', {**payload, 'balance': '26'}, admin=True)[0], 400)
        self.assertEqual(self.call('POST', '/admin/api/gift-cards', {**payload, 'balance': 'NaN'}, admin=True)[0], 400)
        self.assertEqual(self.call('POST', '/admin/api/gift-cards', payload, admin=True)[0], 201)
        self.assertEqual(self.call('POST', '/admin/api/gift-cards', payload, admin=True)[0], 400)
        status, paid = self.order(gift_card_code='old-123')
        self.assertEqual(status, 201)
        self.assertEqual((paid['gift_card_applied'], paid['gift_card_balance'], paid['amount_due']), (12.5, 0, 6.94))

    def test_admin_pickup_sort(self):
        _, later = self.order(pickup_time='14:00')
        _, earlier = self.order(pickup_time='08:00')
        _, data = self.call('GET', '/admin/api/orders', admin=True)
        self.assertEqual([o['id'] for o in data['orders']], [earlier['id'], later['id']])
        _, page = self.call('GET', '/admin', admin=True)
        self.assertIn('08:00', page)
        self.assertLess(page.index(f"#{earlier['id']}"), page.index(f"#{later['id']}"))


if __name__ == "__main__":
    unittest.main()
