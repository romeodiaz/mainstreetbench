"""Rebuild the September review without changing source transactions."""
import csv, re, collections
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):
 with (ROOT/'books'/f'{name}.csv').open() as f:return list(csv.DictReader(f))
def write(name,rows,fields):
 with (ROOT/'reports'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def q(n):return n.quantize(D('.01'),rounding=ROUND_HALF_UP)
raw=read('register_export_sep01-15')+read('register_export_sep16-30')
seen={};duplicates=[];out=[];sales=[]
for r in raw:
 if r['order_id'] in seen:
  assert r==seen[r['order_id']], 'Conflicting duplicate needs review'
  duplicates.append(r);continue
 seen[r['order_id']]=r
 if not r['date'].startswith('2026-09'):out.append(r);continue
 sales.append(r)
write('september_register_clean.csv',sales,list(raw[0]))
write('duplicate_register_rows.csv',duplicates,list(raw[0]))
write('outside_september.csv',out,list(raw[0]))
refunds=[r for r in read('refunds') if r['status']=='succeeded']
gross=sum(D(r['subtotal']) for r in sales); discounts=sum(D(r['discount']) for r in sales)
tax=sum(D(r['tax']) for r in sales);total=sum(D(r['total']) for r in sales)
refund_gross=sum(D(r['amount']) for r in refunds)
refund_tax=sum(q(D(r['amount'])*D(8)/D(108)) for r in refunds)
# Refund tax split is an assumption until confirmed in processor item-level records.
summary=[
 {'line':'Unique September orders','amount':len(sales),'note':'6 identical duplicates removed; August CL-0831-0107 excluded'},
 {'line':'Gross food sales','amount':gross,'note':'before recorded discounts'},
 {'line':'Recorded discounts','amount':discounts,'note':'Includes $110.29 recorded but not reflected in order totals; review exceptions'},
 {'line':'Food receipts before refunds excluding tax','amount':total-tax,'note':'actual recorded total less recorded tax; do not count gift issuance as sales'},
 {'line':'Successful refunds including tax','amount':refund_gross,'note':'RF-001 through RF-009, RF-012 and RF-013; failed/pending excluded'},
 {'line':'Estimated refund tax','amount':refund_tax,'note':'assumes all refunds taxable at 8%; confirm item-level tax treatment'},
 {'line':'Food receipts after successful refunds excluding tax','amount':total-tax-(refund_gross-refund_tax),'note':'provisional; missing and unmatched payments still require resolution'},
 {'line':'Gift cards sold (liability)','amount':'425.00','note':'separate ledger; not earned revenue'},
 {'line':'Gift cards redeemed','amount':'180.00','note':'payment of previous liability; tie to orders before booking further sales'},
 {'line':'Closing gift card liability','amount':'1485.00','note':'1240 + 425 - 180; original understated by 180'},
 {'line':'September recorded tax before refunds','amount':tax,'note':'unique in-month register rows'},
 {'line':'September tax after estimated refund adjustment','amount':tax-refund_tax,'note':'review only, not a filed return'},
 {'line':'September implied taxable base before refunds','amount':total-tax,'note':'recorded receipts basis; disputed coupon rows may require adjustment'},
 {'line':'September implied taxable base after refunds','amount':total-tax-(refund_gross-refund_tax),'note':'do not force rate multiplication to equal per-order rounded tax'},
]
write('september_summary_review.csv',summary,['line','amount','note'])
write('sales_tax_return_review.csv',[
 {'line':'Rate','amount':'8%','note':'September only; 8.25% starts October 1'},
 {'line':'Tax collected before refunds','amount':tax,'note':'deduplicated September rows'},
 {'line':'Estimated successful-refund tax adjustment','amount':refund_tax,'note':'8/108 of each refund, rounded; confirm actual tax reversals'},
 {'line':'Estimated tax after refund adjustment','amount':tax-refund_tax,'note':'not filing advice; coupon inconsistencies and processor records need review'},
 {'line':'Existing draft taxable sales','amount':'23426.13','note':'unsupported by source reconstruction; do not submit unchanged'},
 {'line':'Existing draft tax','amount':'1802.94','note':'does not match reconstructed tax'},
],['line','amount','note'])
fees=[]
for p in read('card_payments'):
 expected=q(D(p['amount'])*D('.029')+D('.30'))
 if D(p['fee'])!=expected:fees.append({**p,'contract_fee':expected,'excess_fee':D(p['fee'])-expected})
write('processor_fee_exceptions.csv',fees,list(read('card_payments')[0])+['contract_fee','excess_fee'])
issues=[]
for r in sales:
 expected=D(r['subtotal'])-D(r['discount'])+D(r['tax'])
 correct_tax=q((D(r['subtotal'])-D(r['discount']))*D('.08'))
 if expected!=D(r['total']) or correct_tax!=D(r['tax']):
  issues.append({**r,'total_using_recorded_discount':expected,'tax_if_discount_honored':correct_tax,'reason':'Recorded discount not reflected in charge; eligibility also needs review'})
write('discount_exceptions.csv',issues,list(raw[0])+['total_using_recorded_discount','tax_if_discount_honored','reason'])
costs=[]
for r in read('cost_sheet'):
 cost=D(r['flour_kg'])*D(r['flour_cost_per_kg'])+D(r['other_ingredients'])+D(r['labor'])
 costs.append({**r,'total_cost':q(cost),'contribution':q(D(r['price'])-cost),'margin_percent':q((D(r['price'])-cost)/D(r['price'])*100)})
write('current_product_margins.csv',costs,list(read('cost_sheet')[0])+['total_cost','contribution','margin_percent'])
print('SUMMARY',summary)
print('FEE EXCESS',sum(D(r['excess_fee']) for r in fees),len(fees))
print('MARGINS',costs)
