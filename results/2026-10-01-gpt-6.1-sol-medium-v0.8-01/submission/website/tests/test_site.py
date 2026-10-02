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

class RegressionTest(SiteTest):
    def test_server_prices_tax_and_coupon(self):
        status, o = self.order(items=[{'sku':'BREAD9','qty':2,'price':0.01}], promo_code='WELCOME10')
        self.assertEqual(status,201,o)
        self.assertEqual((o['subtotal'],o['discount'],o['tax'],o['total']),(18.,1.8,1.34,17.54))
        self.assertEqual(self.order(promo_code='WELCOME10',pickup_slot='11:00')[0],400)

    def test_limits_use_pickup_day_and_cancel_frees_capacity(self):
        for _ in range(3):
            self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':2}])[0],201)
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],pickup_slot='11:00')[0],409)
        status, menu=self.call('GET','/api/menu?date=2026-10-10')
        self.assertEqual(next(p for p in menu['products'] if p['sku']=='CAKE48')['remaining'],0)
        self.assertEqual(self.call('POST','/admin/api/orders/1/cancel',{},admin=True)[0],200)
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':2}])[0],201)

    def test_notice_phone_and_holidays(self):
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],pickup_date='2026-10-09')[0],400)
        self.assertEqual(self.order(items=[{'sku':'CATER120','qty':1}],pickup_date='2026-10-09')[0],400)
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],customer={'name':'A','email':'a@example.com','phone':''})[0],400)
        self.assertEqual(self.order(pickup_date='2026-11-26')[0],400)
        self.assertFalse(self.call('GET','/api/slots?date=2026-12-25')[1]['open'])
        self.assertEqual(self.order(pickup_date='2026-10-12')[0],400)
        self.assertEqual(self.order(items=[{'sku':'PIE32','qty':1}])[0],400)

    def test_retry_and_privacy(self):
        _, o=self.order(request_id='retry-one')
        _, again=self.order(request_id='retry-one')
        self.assertEqual(o['id'],again['id'])
        self.assertEqual(self.order(request_id='retry-one',customer={'name':'B','email':'b@example.com'})[0],409)
        _, public=self.call('GET',f"/order/{o['id']}")
        self.assertNotIn('ana@example.com',public)
        self.assertNotIn('555-0100',public)
        self.assertEqual(self.call('GET','/admin/orders.csv')[0],401)
        self.assertEqual(self.call('GET','/admin/orders.csv',admin=True)[0],200)
        self.assertEqual(self.call('POST',f"/api/orders/{o['id']}/cancel",{'key':'wrong'})[0],403)
        self.assertEqual(self.call('GET','/api/orders/1')[1].get('customer'),None)

    def test_gift_cards_require_payment_and_restore_once(self):
        _, o=self.order(items=[{'sku':'GIFT25','qty':1}])
        _, public=self.call('GET',f"/order/{o['id']}")
        self.assertNotIn('Gift card code',public)
        _, page=self.call('GET',o['confirmation_url'])
        import re
        code=re.search(r'Gift card code: <strong>([^<]+)',page)[1]
        self.assertEqual(self.order(gift_card_code=code,pickup_slot='11:00')[0],400)
        self.call('POST',f"/admin/api/orders/{o['id']}/payment-received",{},admin=True)
        _, spent=self.order(gift_card_code=code,pickup_slot='11:00')
        self.assertEqual(spent['gift_card_applied'],19.49)
        self.assertEqual(self.call('POST',f"/admin/api/orders/{o['id']}/cancel",{},admin=True)[0],409)
        for _ in range(2):self.call('POST',f"/admin/api/orders/{spent['id']}/cancel",{},admin=True)
        _, q=self.call('POST','/api/quote',{'items':[{'sku':'CAKE48','qty':1}], 'gift_card_code':code})
        self.assertEqual(q['gift_card_applied'],25.)

    def test_cancel_unpaid_gift_card_voids_it(self):
        _, o=self.order(items=[{'sku':'GIFT25','qty':1}])
        self.call('POST',f"/admin/api/orders/{o['id']}/cancel",{},admin=True)
        _, page=self.call('GET',o['confirmation_url'])
        self.assertIn('void (order cancelled)',page)
        self.assertEqual(self.call('POST',f"/admin/api/orders/{o['id']}/payment-received",{},admin=True)[0],400)

    def test_concurrent_orders_do_not_overbook(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda n:self.order(request_id=f"simultaneous-{n}"),range(8)))
        self.assertEqual(sum(status==201 for status,_ in results),4)
        self.assertEqual(sum(status==409 for status,_ in results),4)

    def test_concurrent_first_order_coupon_used_once(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda n:self.order(request_id=f"coupon-{n}",promo_code="WELCOME10"),range(4)))
        self.assertEqual(sum(status==201 for status,_ in results),1)
        self.assertEqual(sum(status==400 for status,_ in results),3)

    def test_coffee_promotion_ends(self):
        import sys
        sys.path.insert(0,str(ROOT))
        from bakery import settings
        import datetime as dt
        p={'sku':'COFFEE18','price':16.5}
        self.assertEqual(settings.product_price(p,dt.date(2026,10,15)),16.5)
        self.assertEqual(settings.product_price(p,dt.date(2026,10,16)),18.)


if __name__ == "__main__":
    unittest.main()
