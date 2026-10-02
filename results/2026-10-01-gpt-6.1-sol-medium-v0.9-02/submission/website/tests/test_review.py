import datetime as dt
import os
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from bakery.db import Database, GiftCardInUse
from bakery.server import create_order, quote, Conflict, slots_json, Handler

class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Database(self.tmp.name+'/test.db')
  self.pin=patch.dict(os.environ,{'CORNERLOAF_NOW':'2026-10-08T09:10:00'});self.pin.start()
 def tearDown(self):self.db.conn.close();self.pin.stop();self.tmp.cleanup()
 def payload(self,**kw):
  p=dict(customer=dict(name='Ana',email='ana@example.com',phone='5550104242'),pickup_date='2026-10-10',pickup_slot='10:00',items=[dict(sku='BREAD9',qty=2)])
  p.update(kw);return p
 def test_prices_are_not_customer_controlled(self):
  p=self.payload(items=[dict(sku='BREAD9',qty=2,price=-50,unit_price=.01)])
  self.assertEqual(quote(self.db,p)['subtotal'],18)
  self.assertEqual(self.db.order(create_order(self.db,p))['subtotal'],18)
 def test_discount_then_new_tax(self):
  self.assertEqual(quote(self.db,self.payload(promo_code='WELCOME10'))['total'],17.54)
 def test_price_dates(self):
  self.assertEqual(quote(self.db,self.payload(items=[dict(sku='CINNAMON325',qty=1)]))['subtotal'],3.5)
  with patch.dict(os.environ,{'CORNERLOAF_NOW':'2026-10-16T09:10:00'}):
   self.assertEqual(quote(self.db,self.payload(items=[dict(sku='COFFEE18',qty=1)]))['subtotal'],18)
 def test_holidays(self):self.assertFalse(slots_json(self.db,dt.date(2026,11,26))['open'])
 def test_capacity_counts_pickup_day(self):
  for i in range(3):create_order(self.db,self.payload(pickup_slot=f'{10+i}:00',items=[dict(sku='CAKE48',qty=2)]))
  with self.assertRaises(Conflict):create_order(self.db,self.payload(pickup_slot='13:00',items=[dict(sku='CAKE48',qty=1)]))
 def test_concurrent_retry_saves_once(self):
  p=self.payload(request_id='retry-test')
  with ThreadPoolExecutor(4) as pool:ids=list(pool.map(lambda _:create_order(self.db,p),range(4)))
  self.assertEqual(len(set(ids)),1);self.assertEqual(len(self.db.orders()),1)
 def test_gift_pending_then_paid_then_cancelled(self):
  oid=create_order(self.db,self.payload(items=[dict(sku='GIFT25',qty=1)]))
  card=self.db.gift_cards_for_order(oid)[0];self.assertEqual(card['status'],'pending')
  self.assertEqual(quote(self.db,self.payload(gift_card_code=card['code']))['gift_card_applied'],0)
  self.db.record_payment(oid,'2026-10-08');self.assertEqual(self.db.gift_card(card['code'])['status'],'active')
  self.db.cancel_order(oid);self.assertEqual(self.db.gift_card(card['code'])['status'],'void')
 def test_cancel_restores_card_once_and_frees_stock(self):
  source=create_order(self.db,self.payload(items=[dict(sku='GIFT25',qty=1)]));self.db.record_payment(source,'2026-10-08')
  code=self.db.gift_cards_for_order(source)[0]['code']
  oid=create_order(self.db,self.payload(gift_card_code=code,items=[dict(sku='CAKE48',qty=1)]))
  with self.assertRaises(GiftCardInUse):self.db.cancel_order(source)
  self.db.cancel_order(oid);self.db.cancel_order(oid)
  self.assertEqual(self.db.gift_card(code)['balance'],25);self.assertEqual(self.db.product_usage('2026-10-10').get('CAKE48',0),0)
 def test_private_cancel_key(self):
  oid=create_order(self.db,self.payload());row=self.db.order(oid)
  class Fake:
   db=self.db
   def send_json(self,status,data):self.result=(status,data)
   def not_found(self):self.result=(404,{})
  h=Fake();Handler.customer_cancel(h,oid,{'key':'wrong'});self.assertEqual(h.result[0],403)
  self.assertEqual(self.db.order(oid)['status'],'placed')
  Handler.customer_cancel(h,oid,{'key':row['cancel_key']});self.assertEqual(h.result[0],200)
 def test_gift_cards_not_taxed_or_discounted(self):
  q=quote(self.db,self.payload(items=[dict(sku='GIFT25',qty=1)],promo_code='FIVEOFF'))
  self.assertEqual((q['discount'],q['tax'],q['total']),(0,0,25))
