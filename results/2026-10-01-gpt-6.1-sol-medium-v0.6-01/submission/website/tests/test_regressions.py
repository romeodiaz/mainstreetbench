"""Real HTTP regressions, always using disposable databases."""
import datetime as dt
from decimal import Decimal
import test_site
from bakery.pricing import price_order
from bakery import settings

class RegressionTest(test_site.SiteTest):
    def test_money(self):
        lines=[{'qty':1,'unit_price':9,'category':'Bread'},{'qty':1,'unit_price':25,'category':'Gift Cards'}]
        self.assertEqual(price_order(lines,{'percent_off':10,'amount_off':None},Decimal('.0825')),dict(subtotal=34.,discount=.9,tax=.67,total=33.77))
        self.assertEqual(price_order([lines[0]],{'percent_off':None,'amount_off':50},Decimal('.0825'))['total'],0)
        self.assertEqual(price_order([{'qty':1,'unit_price':2.25,'category':'Bread'}],None,Decimal('.0825'))['tax'],.19)
        self.assertEqual(settings.tax_rate(dt.date(2026,9,30)),Decimal('.08'))
        self.assertEqual(settings.tax_rate(dt.date(2026,10,1)),Decimal('.0825'))

    def test_quantities_and_prices(self):
        for qty in [-1,0,True,1.5,51]:self.assertEqual(self.order(items=[{'sku':'BREAD9','qty':qty}])[0],400)
        status,o=self.order(items=[{'sku':'BREAD9','qty':2,'unit_price':.01}])
        self.assertEqual(status,201);self.assertEqual(o['subtotal'],18);self.assertEqual(o['tax'],1.49)
        self.assertEqual(self.order(customer=['bad'])[0],400)

    def test_schedule(self):
        for day in ['2026-10-12','2026-11-26','2026-12-25']:
            self.assertFalse(self.call('GET','/api/slots?date='+day)[1]['open'])
            self.assertEqual(self.order(pickup_date=day)[0],400)
        self.assertEqual(self.call('GET','/api/slots?date=2026-10-10')[1]['slots'][-1]['time'],'14:30')
        self.assertEqual(self.order(pickup_slot='15:00')[0],400)
        self.assertEqual(self.order(items=[{'sku':'PIE32','qty':1}])[0],400)
        self.assertEqual(self.order(pickup_date='2026-10-09',items=[{'sku':'CAKE48','qty':1}])[0],400)
        self.assertEqual(self.order(customer={'name':'A','email':'a@b.com'},items=[{'sku':'CAKE48','qty':1}])[0],400)
        self.assertEqual(self.order(pickup_date='2026-10-09',pickup_slot='10:00',items=[{'sku':'CATER120','qty':1}])[0],201)

    def test_coupons(self):
        for code in ['STAFF50','FALL15']:self.assertEqual(self.order(promo_code=code)[0],400)
        status,o=self.order(promo_code='WELCOME10');self.assertEqual(status,201)
        self.assertEqual(o['discount'],1.8);self.assertEqual(o['tax'],1.34)
        self.assertEqual(self.order(promo_code='WELCOME10',pickup_slot='11:00')[0],400)
        q=self.call('POST','/api/quote',{'items':[{'sku':'BREAD9','qty':2}],'email':'ana@example.com','promo_code':'WELCOME10'})[1]
        self.assertTrue(q['notes']);self.assertEqual(q['discount'],0)

    def test_privacy_and_retry(self):
        _,o=self.order(request_id='retry-123');self.assertEqual(self.order(request_id='retry-123')[1]['id'],o['id'])
        self.assertEqual(len(self.call('GET','/admin/api/orders',admin=True)[1]['orders']),1)
        public=self.call('GET',f'/order/{o["id"]}')[1]
        self.assertNotIn('ana@example.com',public);self.assertNotIn('555-0100',public)
        self.assertEqual(self.call('GET','/admin/orders.csv')[0],401)
        self.assertEqual(self.call('POST',f'/api/orders/{o["id"]}/cancel',{'key':'wrong'})[0],403)
        self.assertIn('$19.49',self.call('GET',o['confirmation_url'])[1])
        self.assertIn('555-010-0000',self.call('GET','/contact')[1]);self.assertNotIn('555-867-5309',self.call('GET','/contact')[1])
        menu=self.call('GET','/')[1];self.assertIn('data-name="Baker&#x27;s Dozen Cookies"',menu);self.assertNotIn('onclick=',menu)

    def test_gift_cancel(self):
        _,bought=self.order(items=[{'sku':'GIFT25','qty':1}],pickup_date='2026-10-11');self.assertEqual(bought['total'],25)
        import re
        code=re.search(r'Gift card code: <strong>([^<]+)',self.call('GET',bought['confirmation_url'])[1])[1]
        self.assertNotIn(code,self.call('GET',f'/order/{bought["id"]}')[1])
        self.assertEqual(self.order(gift_card_code=code)[0],400)
        activate=f'/admin/api/orders/{bought["id"]}/activate-gift-cards'
        self.assertEqual(self.call('POST',activate,{'payment_received':True})[0],401)
        self.assertEqual(self.call('POST',activate,{},admin=True)[0],400)
        self.assertEqual(self.call('POST',activate,{'payment_received':True},admin=True)[0],200)
        self.assertEqual(self.call('POST',activate,{'payment_received':True},admin=True)[0],200)
        _,spent=self.order(gift_card_code=code);self.assertEqual(spent['gift_card_applied'],19.49)
        self.assertEqual(self.call('POST',f'/admin/api/orders/{bought["id"]}/cancel',{},admin=True)[0],409)
        key=spent['confirmation_url'].split('key=')[1]
        for _ in range(2):self.assertEqual(self.call('POST',f'/api/orders/{spent["id"]}/cancel',{'key':key})[0],200)
        q=self.call('POST','/api/quote',{'items':[{'sku':'BREAD9','qty':3}],'gift_card_code':code})[1];self.assertEqual(q['gift_card_applied'],25)
        self.assertEqual(self.call('POST',f'/admin/api/orders/{bought["id"]}/cancel',{},admin=True)[0],200)
        q=self.call('POST','/api/quote',{'items':[{'sku':'BREAD9','qty':1}],'gift_card_code':code})[1];self.assertEqual(q['gift_card_applied'],0)
        self.assertIn('cancelled',self.call('GET','/admin',admin=True)[1])
        self.assertEqual(self.call('POST',activate,{'payment_received':True},admin=True)[0],409)

    def test_limits(self):
        for _ in range(4):self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}])[0],201)
        self.assertEqual(self.order()[0],409)
        _,o=self.order(items=[{'sku':'CAKE48','qty':2}],pickup_slot='11:00')
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':1}],pickup_slot='12:00')[0],409)
        cake=next(p for p in self.call('GET','/api/menu?date=2026-10-10')[1]['products'] if p['sku']=='CAKE48')
        self.assertEqual(cake['remaining'],0);self.assertFalse(cake['available'])
        self.call('POST',f'/admin/api/orders/{o["id"]}/cancel',{},admin=True)
        self.assertEqual(self.order(items=[{'sku':'CAKE48','qty':2}],pickup_slot='11:00')[0],201)

    def test_simultaneous_orders(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as pool:
            statuses=list(pool.map(lambda n:self.order(items=[{'sku':'CAKE48','qty':2}],request_id=f'cake-{n}')[0],range(6)))
        self.assertEqual(statuses.count(201),3)
        self.assertEqual(statuses.count(409),3)
        customer={'name':'First','email':'first@example.com','phone':'555-0100'}
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(lambda n:self.order(customer=customer,pickup_date='2026-10-11',promo_code='WELCOME10',request_id=f'promo-{n}')[0],range(2)))
        self.assertEqual(sorted(statuses),[201,400])
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda n:self.order(pickup_date='2026-10-14',request_id='same-retry'),range(4)))
        self.assertTrue(all(status==201 for status,o in results))
        self.assertEqual(len({o['id'] for status,o in results}),1)
