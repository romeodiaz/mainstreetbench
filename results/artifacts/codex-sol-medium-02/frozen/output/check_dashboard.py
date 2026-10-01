#!/usr/bin/env python3
"""Independent, standard-library reconciliation. Run with python3.

Recomputes all dashboard values from saved clean_orders.csv, validates the
customer rollup and financial policies, and compares visible HTML cell text.
No builder imports, no internet, no accounts. Exit 0 = PASS, 1 = FAIL.
"""
import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

BASE = Path(__file__).resolve().parent
TODAY = date(2026, 9, 30)

class DashboardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.active = None
        self.fragments = []
        self.external = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-check' in attrs:
            assert self.active is None, 'Nested checked cells'
            self.active = (tag, attrs['data-check'])
            self.fragments = []
        for attr in ['src', 'href']:
            if attr in attrs and not attrs[attr].startswith('#'):
                self.external.append(attrs[attr])

    def handle_data(self, text):
        if self.active:
            self.fragments.append(text)

    def handle_endtag(self, tag):
        if self.active and self.active[0] == tag:
            key = self.active[1]
            assert key not in self.values, f'Duplicate dashboard key: {key}'
            self.values[key] = ''.join(self.fragments).strip()
            self.active = None

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def dollars(v):
    return f'${Decimal(v):,.2f}'

def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def run():
    for filename in ['clean_orders.csv', 'customers.csv', 'cleaning_log.md', 'dashboard.html', 'check_dashboard.py']:
        require((BASE/filename).is_file() and (BASE/filename).stat().st_size > 0, f'Missing or empty deliverable {filename}')
    rows = read_csv(BASE/'clean_orders.csv')
    customers = read_csv(BASE/'customers.csv')
    require(bool(rows), 'No cleaned orders')
    require(len({r['order_id'] for r in rows}) == len(rows), 'Repeated clean order ID')
    require(len({c['customer_id'] for c in customers}) == len(customers), 'Repeated customer ID')
    require(all(r['order_id'] not in {'90001','90002','90003'} for r in rows), 'Quarantined/test order included')
    customer_groups = defaultdict(list)
    monthly = defaultdict(lambda: [Decimal('0'), 0])
    products = defaultdict(lambda: [0, Decimal('0')])
    revenue = gift = receipts = Decimal('0')
    orders = 0
    for r in rows:
        d = date.fromisoformat(r['order_date'])
        require(d.isoformat() == r['order_date'], 'Noncanonical date')
        require(date(2025,10,1) <= d <= TODAY, 'Date out of reporting range: '+r['order_id'])
        require(re.fullmatch(r'\(\d{3}\) \d{3}-\d{4}', r['phone']), 'Malformed phone')
        require(re.fullmatch(r'-?\d+', r['quantity']), 'Quantity not a numeric integer')
        for field in ['unit_price', 'recorded_total', 'net_revenue', 'gift_card_proceeds']:
            require(re.fullmatch(r'-?\d+\.\d{2}', r[field]), 'Invalid numeric money '+field)
        q = int(r['quantity'])
        total = Decimal(r['recorded_total'])
        net = Decimal(r['net_revenue'])
        deferred = Decimal(r['gift_card_proceeds'])
        require(r['product'] in {'Sourdough Loaf','Coffee Beans 1 lb','Croissant Box (6)','Birthday Cake','Catering Tray','Gift Card'}, 'Unstandardized product')
        require(net == (Decimal('0') if r['product']=='Gift Card' else total), 'Revenue policy mismatch')
        require(deferred == (total if r['product']=='Gift Card' else Decimal('0')), 'Gift-card policy mismatch')
        require(net + deferred == total, 'Financial components do not reconcile')
        require(r['transaction_type'] in {'sale','refund'}, 'Unknown transaction type')
        sale = r['transaction_type'] == 'sale'
        require((q > 0 and total >= 0) if sale else (q < 0 and total < 0), 'Sign/type mismatch')
        require(bool(r['refund_for_order_id']) != sale, 'Missing/unexpected refund link')
        if total != q*Decimal(r['unit_price']):
            require('total_differs_from_quantity_times_price' in r['flags'], 'Unflagged arithmetic mismatch')
        customer_groups[r['customer_id']].append(r)
        monthly[r['order_date'][:7]][0] += net
        monthly[r['order_date'][:7]][1] += int(sale)
        if r['product'] != 'Gift Card':
            products[r['product']][0] += q
            products[r['product']][1] += net
        revenue += net
        gift += deferred
        receipts += total
        orders += int(sale)
    index = {r['order_id']:r for r in rows}
    for r in rows:
        if r['transaction_type']=='refund':
            original = index.get(r['refund_for_order_id'])
            require(original is not None, 'Refund original missing')
            require(original['transaction_type']=='sale', 'Refund targets non-sale')
            require(original['customer_id']==r['customer_id'] and original['product']==r['product'], 'Refund customer/product mismatch')
            require(original['order_date'] <= r['order_date'], 'Refund predates sale')
            require(Decimal(original['recorded_total']) == -Decimal(r['recorded_total']), 'Refund amount mismatch')
    require(set(customer_groups)=={c['customer_id'] for c in customers}, 'Customer coverage mismatch')
    rollups=[]
    for cid, rr in customer_groups.items():
        require(len({(r['customer_name'],r['email'],r['phone']) for r in rr})==1, 'Inconsistent customer contacts')
        purchases=[r for r in rr if r['transaction_type']=='sale']
        rollups.append(dict(customer_id=cid, name=rr[0]['customer_name'], email=rr[0]['email'],phone=rr[0]['phone'],
                            number_of_orders=str(len(purchases)),net_revenue=str(sum((Decimal(r['net_revenue']) for r in rr),Decimal('0.00'))),
                            last_order_date=max(r['order_date'] for r in purchases)))
    require(sorted(rollups,key=lambda c:c['customer_id'])==sorted(customers,key=lambda c:c['customer_id']), 'customers.csv differs from clean order rollup')

    # Verify removal and preservation against the untouched local source copy.
    source = BASE.parent/'customer_orders.csv'
    original_rows = read_csv(source)
    original_groups = defaultdict(list)
    for r in original_rows:
        original_groups[r['Order ID']].append(r)
    require(set(index)==set(original_groups)-{'90001','90002','90003'}, 'Source order coverage mismatch')
    duplicate_count=0
    for oid, rr in original_groups.items():
        require(all(r==rr[0] for r in rr), 'Conflicting source duplicate')
        duplicate_count += len(rr)-1
        if oid not in index:
            continue
        r=index[oid]; original=rr[0]
        parse_amount=lambda s: Decimal(s.replace('$','').replace('USD','').strip())
        require(Decimal(r['recorded_total'])==parse_amount(original['Total']), 'Recorded total changed: '+oid)
        require(Decimal(r['unit_price'])==parse_amount(original['Unit Price']), 'Unit price changed: '+oid)
        require(int(r['quantity'])==int(original['Qty']), 'Quantity changed: '+oid)
        require(r['notes']==original['Notes'] and r['payment']==original['Payment'], 'Notes/payment changed')
        require(r['customer_id']=='C-'+hashlib.sha256(('phone:'+re.sub(r'\D','',r['phone'])).encode()).hexdigest()[:12], 'Unstable customer ID')
        if oid in {'10221','10269'}:
            require(r['order_date']=={'10221':'2026-06-04','10269':'2026-08-06'}[oid], 'Year correction mismatch')
        else:
            parsed=None
            for fmt in ['%Y-%m-%d','%m/%d/%y','%m/%d/%Y','%d-%b-%Y','%B %d, %Y']:
                try:
                    from datetime import datetime
                    parsed=datetime.strptime(original['Order Date'],fmt).date().isoformat()
                    break
                except ValueError:
                    continue
            require(r['order_date']==parsed, 'Order date not source-derived: '+oid)
    log=(BASE/'cleaning_log.md').read_text()
    require(hashlib.sha256(source.read_bytes()).hexdigest() in log, 'Source fingerprint missing or source modified')
    require(all(oid in log for oid in original_groups), 'Order missing from audit log')

    expected={}
    def put(key, value):
        expected[key]=str(value)
    put('summary.revenue',dollars(revenue))
    put('summary.customers',len(customer_groups))
    put('summary.orders',orders)
    put('summary.receipts',dollars(receipts))
    put('summary.gift',dollars(gift))
    put('receipts.revenue',dollars(revenue))
    months=[(2025,10),(2025,11),(2025,12)]+[(2026,m) for m in range(1,10)]
    for y,m in months:
        key=f'{y}-{m:02}'
        put('month.'+key+'.label',date(y,m,1).strftime('%b %Y'))
        put('month.'+key+'.revenue',dollars(monthly[key][0]))
        put('month.'+key+'.orders',monthly[key][1])
    require(sum(v[0] for v in monthly.values())==revenue, 'Months do not sum to revenue')
    for rank,c in enumerate(sorted(rollups,key=lambda c:(-Decimal(c['net_revenue']),c['customer_id']))[:10],1):
        k=f'top.{rank}.'
        put(k+'name',c['name']);put(k+'revenue',dollars(c['net_revenue']))
        put(k+'orders',c['number_of_orders']);put(k+'last',c['last_order_date'])
    for product,(units,net) in products.items():
        k='product.'+product+'.'
        put(k+'name',product);put(k+'units',units);put(k+'revenue',dollars(net))
    inactive=[c for c in rollups if (TODAY-date.fromisoformat(c['last_order_date'])).days>90]
    put('summary.inactive',len(inactive))
    for c in inactive:
        k='inactive.'+c['customer_id']+'.'
        put(k+'name',c['name']);put(k+'last',c['last_order_date'])
        put(k+'days',(TODAY-date.fromisoformat(c['last_order_date'])).days)
        put(k+'revenue',dollars(c['net_revenue']));put(k+'email',c['email'] or 'Not recorded');put(k+'phone',c['phone'])
    parser=DashboardParser()
    html=(BASE/'dashboard.html').read_text(encoding='utf-8')
    parser.feed(html)
    require(not parser.external, 'Dashboard has external dependencies')
    require('name="viewport"' in html and '@media' in html, 'Responsive layout missing')
    require(set(parser.values)==set(expected), 'Dashboard key coverage mismatch: '+str(set(parser.values)^set(expected)))
    for key,value in expected.items():
        require(parser.values[key]==value,f'Dashboard mismatch {key}: {parser.values[key]!r} != {value!r}')
    # Check chart widths and visible ranking order in addition to numeric cells.
    bar_widths=re.findall(r'class="bar" style="width:([\d.]+)%"',html)
    maximum=max(monthly[f'{y}-{m:02}'][0] for y,m in months)
    expected_widths=[round(monthly[f'{y}-{m:02}'][0]/maximum*100,2) for y,m in months]
    require([float(v) for v in bar_widths]==[float(v) for v in expected_widths], 'Chart bar widths disagree with monthly revenue')
    visible_products=[key[len('product.'):-len('.name')] for key in parser.values if key.startswith('product.') and key.endswith('.name')]
    require(visible_products==sorted(products,key=lambda p:(-products[p][0],p)), 'Product ranking mismatch')
    print(f'PASS — all five deliverables exist; {len(expected)} visible dashboard values match clean_orders.csv; customers.csv matches.')
    print(f'{len(rows)} transactions ({orders} purchases, {len(rows)-orders} refunds); {len(customers)} customers; {len(inactive)} inactive.')
    print(f'Earned revenue {dollars(revenue)} + gift-card proceeds {dollars(gift)} = recorded receipts {dollars(receipts)}.')
    print(f'Source reconciliation: {len(original_rows)} rows − {duplicate_count} duplicate copies − 2 explicit tests − 1 quarantined suspected test = {len(rows)} transactions.')
    print('Open issues remain documented; PASS confirms reconciliation, not accuracy of unresolved source amounts or inferred test status.')

if __name__=='__main__':
    try:
        run()
    except Exception as exc:
        print('FAIL — '+str(exc),file=sys.stderr)
        sys.exit(1)
