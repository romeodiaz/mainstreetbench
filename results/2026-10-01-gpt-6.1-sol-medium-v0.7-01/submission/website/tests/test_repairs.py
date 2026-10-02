"""Regression checks use temporary databases; never customer data."""
import datetime as dt
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import test_site
from bakery import settings
from bakery.pricing import price_order

class RepairsTest(test_site.SiteTest):
    def test_pricing(self):
        _, q = self.call('POST', '/api/quote', {'items':[{'sku':'BREAD9','qty':2}], 'promo_code':'WELCOME10'})
        self.assertEqual((q['discount'],q['tax'],q['total']), (1.8,1.34,17.54))
        _, q = self.call('POST', '/api/quote', {'items':[{'sku':'GIFT25','qty':1},{'sku':'BREAD9','qty':1}], 'promo_code':'WELCOME10'})
        self.assertEqual((q['discount'],q['tax'],q['total']), (.9,.67,33.77))
        _, q = self.call('POST', '/api/quote', {'items':[{'sku':'BAGEL225','qty':1}], 'promo_code':'FIVEOFF'})
        self.assertEqual((q['discount'],q['tax'],q['total']), (2.25,0,0))
        q=price_order([{'qty':1,'unit_price':3.75,'category':'Bread'}],{'percent_off':50,'amount_off':None},Decimal('.0825'))
        self.assertEqual(q['discount'],1.88)
        self.assertEqual(settings.tax_rate(dt.date(2026,9,30)),Decimal('.08'))
        self.assertEqual(settings.product_price({'sku':'COFFEE18'},dt.date(2026,10,16)),18)

    def test_validation(self):
        for qty in [-1,0,True,51,1.5]:
            self.assertEqual(self.order(items=[{'sku':'BREAD9','qty':qty}])[0],400)
        _,o=self.order(items=[{'sku':'BREAD9','qty':1,'price':.01,'unit_price':.01}])
        self.assertEqual(o['subtotal'],9)
        self.assertEqual(self.order(customer=['invalid'])[0],400)
        for date in ['2026-11-26','2026-12-25','2026-10-12']:
            self.assertEqual(self.order(pickup_date=date)[0],400)
            self.assertFalse(self.call('GET','/api/slots?date='+date)[1]['open'])
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],pickup_date='2026-10-09')[0],400)
        self.assertEqual(self.order(items=[{'sku':'CATER120','qty':1}],customer={'name':'Ana','email':'ana@example.com'})[0],400)
        self.assertEqual(self.order(items=[{'sku':'PIE32','qty':1}])[0],400)

    def test_first_order_and_retry(self):
        _,a=self.order(promo_code='WELCOME10',request_id='repeat')
        _,b=self.order(promo_code='WELCOME10',request_id='repeat')
        self.assertEqual(a['id'],b['id'])
        self.assertEqual(self.order(promo_code='WELCOME10',request_id='new')[0],400)
        self.assertEqual(len(self.call('GET','/admin/api/orders',admin=True)[1]['orders']),1)

    def test_capacity_and_cancellation_privacy(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda n:self.order(request_id='c'+str(n)),range(8)))
        self.assertEqual(sum(s==201 for s,_ in results),4)
        self.assertEqual(sum(s==409 for s,_ in results),4)
        o=next(o for s,o in results if s==201)
        _,page=self.call('GET',f"/order/{o['id']}")
        self.assertNotIn('ana@example.com',page)
        self.assertNotIn('customer',self.call('GET',f"/api/orders/{o['id']}")[1])
        self.assertEqual(self.call('GET','/admin/orders.csv')[0],401)
        self.assertEqual(self.call('GET','/admin/orders.csv',admin=True)[0],200)
        self.assertEqual(self.call('POST',f"/api/orders/{o['id']}/cancel",{'key':'bad'})[0],403)
        key=o['confirmation_url'].split('key=')[1]
        self.assertEqual(self.call('POST',f"/api/orders/{o['id']}/cancel",{'key':key})[0],200)
        self.assertIn('class="status">cancelled',self.call('GET','/admin',admin=True)[1])
        slots=self.call('GET','/api/slots?date=2026-10-10')[1]['slots']
        self.assertEqual(next(s for s in slots if s['time']=='10:00')['remaining'],1)

    def test_daily_limits_use_pickup_and_release(self):
        _,o=self.order(items=[{'sku':'CAKE48','qty':6}])
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],pickup_slot='11:00')[0],409)
        menu=self.call('GET','/api/menu?date=2026-10-10')[1]['products']
        self.assertTrue(next(p for p in menu if p['sku']=='CAKE48')['sold_out'])
        self.call('POST',f"/admin/api/orders/{o['id']}/cancel",{},admin=True)
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],pickup_slot='11:00')[0],201)

    def test_gift_lifecycle(self):
        import re
        _,bought=self.order(items=[{'sku':'GIFT25','qty':1}])
        page=self.call('GET',bought['confirmation_url'])[1]
        code=re.search(r'<strong>([A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4})</strong>',page)[1]
        self.assertNotIn(code,self.call('GET',f"/order/{bought['id']}")[1])
        self.assertEqual(self.order(gift_card_code=code)[0],400)
        self.call('POST',f"/admin/api/orders/{bought['id']}/payment-received",{},admin=True)
        key=bought['confirmation_url'].split('key=')[1]
        self.assertEqual(self.call('POST',f"/api/orders/{bought['id']}/cancel",{'key':key})[0],400)
        _,spent=self.order(gift_card_code=code)
        self.assertEqual(spent['gift_card_applied'],19.49)
        self.assertEqual(self.call('POST',f"/admin/api/orders/{bought['id']}/cancel",{},admin=True)[0],409)
        self.call('POST',f"/admin/api/orders/{spent['id']}/cancel",{},admin=True)
        _,q=self.call('POST','/api/quote',{'items':[{'sku':'BREAD9','qty':3}], 'gift_card_code':code})
        self.assertEqual(q['gift_card_applied'],25)
        self.call('POST',f"/admin/api/orders/{bought['id']}/cancel",{},admin=True)
        self.assertEqual(self.order(gift_card_code=code)[0],400)
        self.assertEqual(self.call('POST',f"/admin/api/orders/{bought['id']}/payment-received",{},admin=True)[0],400)

    def test_customer_content(self):
        page=self.call('GET','/')[1]
        self.assertIn('Baker&#x27;s Dozen Cookies',page)
        self.assertNotIn('onclick=',page)
        self.assertIn('not suitable for tree nut allergies',page)
        products=self.call('GET','/api/menu')[1]['products']
        self.assertIn('almond',next(p for p in products if p['sku']=='SCONE375')['allergens']['contains'])
