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
                "pickup_date": "2026-10-10", "pickup_slot": "12:00", "items": [{"sku": "BREAD9", "qty": 2}]}
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

    def test_food_only_coupons_and_tax(self):
        cases = [
            ([{'sku': 'GIFT25', 'qty': 1}], 'WELCOME10', (25, 0, 0, 25)),
            ([{'sku': 'GIFT25', 'qty': 1}, {'sku': 'BREAD9', 'qty': 2}],
             'WELCOME10', (43, 1.8, 1.3, 42.5)),
            ([{'sku': 'GIFT25', 'qty': 1}, {'sku': 'SCONE375', 'qty': 1}],
             'FIVEOFF', (28.75, 3.75, 0, 25)),
            ([{'sku': 'CINNAMON325', 'qty': 1}], 'WELCOME10', (3.25, .33, .23, 3.15)),
        ]
        for items, code, expected in cases:
            status, order = self.order(items=items, promo_code=code)
            self.assertEqual(status, 201)
            self.assertEqual(tuple(order[k] for k in ('subtotal', 'discount', 'tax', 'total')), expected)

    def test_slots_notice_and_closed_days(self):
        self.assertEqual(self.order(pickup_slot=None)[0], 400)
        for slot in ('7:00', '07:15', '15:00', '06:30'):
            self.assertEqual(self.order(pickup_slot=slot)[0], 400)
        self.assertEqual(self.order(pickup_date='2026-10-12')[0], 400)
        self.assertEqual(self.order(pickup_date='2026-10-08', pickup_slot='11:00')[0], 400)
        self.assertEqual(self.order(pickup_date='2026-10-08', pickup_slot='11:30')[0], 201)
        self.assertEqual(self.order(items=[{'sku': 'CAKE48', 'qty': 1}], pickup_slot='09:00')[0], 400)
        self.assertEqual(self.order(items=[{'sku': 'CATER120', 'qty': 1}], pickup_slot='09:30')[0], 201)
        status, slots = self.call('GET', '/api/slots?date=2026-10-08')
        self.assertEqual(status, 200)
        self.assertEqual(len(slots['slots']), 16)
        self.assertFalse(next(s for s in slots['slots'] if s['time'] == '11:00')['available'])
        self.assertTrue(next(s for s in slots['slots'] if s['time'] == '11:30')['available'])
        self.assertEqual(slots['slots'][0]['time'], '07:00')
        self.assertEqual(slots['slots'][-1]['time'], '14:30')
        self.assertEqual(self.call('GET', '/api/slots?date=2026-10-12')[1],
                         {'date': '2026-10-12', 'open': False, 'slots': []})
        for url in ('/api/slots', '/api/slots?date=nope', '/api/menu?date=2026-02-30', '/api/menu?date='):
            self.assertEqual(self.call('GET', url)[0], 400)

    def test_full_slot_and_cancellation(self):
        orders = [self.order()[1] for _ in range(4)]
        self.assertEqual(self.order()[0], 409)
        slot = next(s for s in self.call('GET', '/api/slots?date=2026-10-10')[1]['slots']
                    if s['time'] == '12:00')
        self.assertEqual((slot['remaining'], slot['available']), (0, False))
        self.call('POST', f"/admin/api/orders/{orders[0]['id']}/cancel", admin=True)
        self.assertEqual(self.order()[0], 201)

    def test_product_limits_atomic_rejection_and_cancellation(self):
        items = [{'sku': 'CAKE48', 'qty': 4}, {'sku': 'CAKE48', 'qty': 3}, {'sku': 'BREAD9', 'qty': 1}]
        status, error = self.order(items=items)
        self.assertEqual((status, error['sku'], error['remaining']), (409, 'CAKE48', 6))
        self.assertEqual(self.call('GET', '/admin/api/orders', admin=True)[1]['orders'], [])
        status, order = self.order(items=[{'sku': 'CAKE48', 'qty': 6}])
        self.assertEqual(status, 201)
        product = next(p for p in self.call('GET', '/api/menu?date=2026-10-10')[1]['products'] if p['sku'] == 'CAKE48')
        self.assertEqual((product['daily_limit'], product['remaining'], product['sold_out']), (6, 0, True))
        from html.parser import HTMLParser
        class Rows(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
            def handle_starttag(self, tag, attrs):
                self.tags.append((tag, dict(attrs)))
        rows = Rows()
        rows.feed(self.call('GET', '/?date=2026-10-10')[1])
        self.assertTrue(any(t == 'li' and a.get('data-sku') == 'CAKE48' and a.get('data-sold-out') == 'true'
                            for t, a in rows.tags))
        self.assertTrue(any(t == 'button' and a.get('data-sku') == 'CAKE48' and 'disabled' in a
                            for t, a in rows.tags))
        self.assertEqual(self.order(items=[{'sku': 'CAKE48', 'qty': 1}], pickup_slot='13:00')[0], 409)
        self.assertEqual(self.order(items=[{'sku': 'CAKE48', 'qty': 1}], pickup_date='2026-10-11')[0], 201)
        self.call('POST', f"/admin/api/orders/{order['id']}/cancel", admin=True)
        self.assertEqual(self.order(items=[{'sku': 'CAKE48', 'qty': 6}])[0], 201)

    def test_admin_limits_and_pickup_order(self):
        path = '/admin/api/products/PIE32'
        self.assertEqual(self.call('PUT', path, {'daily_limit': 0})[0], 401)
        for value in (-1, 1.5, True, '5'):
            self.assertEqual(self.call('PUT', path, {'daily_limit': value}, admin=True)[0], 400)
        self.assertEqual(self.call('PUT', path, {}, admin=True)[0], 400)
        self.assertEqual(self.call('PUT', '/admin/api/products/NOPE', {'daily_limit': 1}, admin=True)[0], 404)
        self.assertEqual(self.call('PUT', path, {'daily_limit': 0}, admin=True)[1]['daily_limit'], 0)
        self.assertEqual(self.order(items=[{'sku': 'PIE32', 'qty': 1}])[0], 409)
        self.assertIsNone(self.call('PUT', path, {'daily_limit': None}, admin=True)[1]['daily_limit'])
        self.assertEqual(self.order(items=[{'sku': 'PIE32', 'qty': 20}], pickup_slot='14:00')[0], 201)
        _, early = self.order(pickup_slot='10:00')
        _, tomorrow = self.order(pickup_date='2026-10-11', pickup_slot='07:00')
        orders = self.call('GET', '/admin/api/orders', admin=True)[1]['orders']
        self.assertEqual(orders[0]['id'], early['id'])
        self.assertEqual(orders[-1]['id'], tomorrow['id'])
        status, page = self.call('GET', '/admin', admin=True)
        self.assertEqual(status, 200)
        self.assertIn('Daily baking limits', page)
        self.assertIn('10:00', page)
        self.assertIn('name="pickup_slot"', self.call('GET', '/checkout')[1])

    def test_simultaneous_orders_cannot_overbook(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda _: self.order()[0], range(8)))
        self.assertEqual(statuses.count(201), 4)
        self.assertEqual(statuses.count(409), 4)
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda n: self.order(pickup_slot=f'{10 + n // 2:02d}:{30 * (n % 2):02d}',
                                                         items=[{'sku': 'CAKE48', 'qty': 1}])[0], range(8)))
        self.assertEqual(statuses.count(201), 6)
        self.assertEqual(statuses.count(409), 2)


class MigrationTest(unittest.TestCase):
    def test_legacy_orders_preserved_and_counted_and_limits_persist(self):
        import sqlite3
        from bakery.db import Database, SCHEMA, PRODUCTS
        from bakery.server import order_json, create_order
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            path = f'{tmp}/legacy.db'
            conn = sqlite3.connect(path)
            conn.executescript(SCHEMA)
            conn.executemany('INSERT INTO products (sku, name, price, category, sort_order) VALUES (?, ?, ?, ?, ?)', PRODUCTS)
            conn.execute("INSERT INTO orders VALUES (42, '2026-10-01T09:00:00', 'Ana', 'ana@example.com', '', "
                         "'2026-10-10', NULL, 288, 0, 23.04, 311.04, 'placed')")
            conn.execute("INSERT INTO order_items VALUES (42, 'CAKE48', 'Birthday Cake', 6, 48, 288)")
            original = tuple(conn.execute('SELECT * FROM orders').fetchone())
            conn.commit()
            conn.close()
            db = Database(path)
            self.assertEqual(tuple(db.order(42))[:-1], original)
            self.assertIsNone(order_json(db, db.order(42))['pickup_slot'])
            self.assertEqual(db.sold_quantity('CAKE48', '2026-10-10'), 6)
            self.assertTrue(next(p for p in db.menu('2026-10-10') if p['sku'] == 'CAKE48')['sold_out'])
            with patch.dict(os.environ, {'CORNERLOAF_NOW': NOW}):
                new_id = create_order(db, {'customer': {'name': 'New', 'email': 'new@example.com'},
                                          'pickup_date': '2026-10-10', 'pickup_slot': '12:00',
                                          'items': [{'sku': 'BREAD9', 'qty': 1}]})
            self.assertGreater(new_id, 42)
            self.assertEqual([o['id'] for o in db.orders()], [42, new_id])
            db.set_limit('CAKE48', 2)
            db.set_limit('PIE32', None)
            db.conn.close()
            db = Database(path)
            self.assertEqual(db.product('CAKE48')['daily_limit'], 2)
            self.assertIsNone(db.product('PIE32')['daily_limit'])
            self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            db.conn.close()


if __name__ == "__main__":
    unittest.main()
