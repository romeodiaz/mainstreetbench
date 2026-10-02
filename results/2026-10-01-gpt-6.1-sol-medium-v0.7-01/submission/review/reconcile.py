"""Rebuild review copies from unchanged September source records. Run from workspace root."""
import csv
from collections import defaultdict
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review'
CENT = D('.01')
def cents(n):return n.quantize(CENT,rounding=ROUND_HALF_UP)
def read(name):return list(csv.DictReader((ROOT/'books'/name).open()))
def write(name,rows,fields=None):
    fields = fields or list(rows[0])
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
raw=read('register_export_sep01-15.csv')+read('register_export_sep16-30.csv')
seen={}; excluded=[]
for row in raw:
    if not row['date'].startswith('2026-09'):
        excluded.append(dict(row,reason='Outside September'))
    elif row['order_id'] in seen:
        if row!=seen[row['order_id']]:raise ValueError('Conflicting duplicate: '+row['order_id'])
        excluded.append(dict(row,reason='Exact duplicate order ID'))
    else:seen[row['order_id']]=row
sales=list(seen.values());payments=read('card_payments.csv');refunds=read('refunds.csv')
write('september_register_clean.csv',sales)
write('excluded_register_rows.csv',excluded)
fees=[]
for p in payments:
    expected=cents(D(p['amount'])*D('.029')+D('.30'))
    if D(p['fee'])!=expected:
        fees.append(dict(p,contract_fee=str(expected),excess_fee=str(D(p['fee'])-expected)))
write('processor_fee_exceptions.csv',fees)
bank=read('bank_statement.csv'); reconciled=[]
for p in read('payouts.csv'):
    linked=[x for x in payments if x['payout_id']==p['payout_id']]
    gross=sum(D(x['amount']) for x in linked);fee=sum(D(x['fee']) for x in linked)
    completed=sum(D(x['amount']) for x in refunds if x['status']=='succeeded' and x['completed']==p['date'])
    deposits=sum(D(x['amount']) for x in bank if p['payout_id'] in x['description'])
    reconciled.append(dict(p,charges=str(gross),fees=str(fee),same_day_completed_refunds=str(completed),
                          processor_unexplained_deduction=str(gross-fee-completed-D(p['amount'])),
                          bank_deposit=str(deposits),payout_minus_bank=str(D(p['amount'])-deposits)))
write('payout_reconciliation.csv',reconciled)
pg=defaultdict(list)
for p in payments:pg[p['order_id']].append(p)
exceptions=[]
for order,sale in seen.items():
    if sale['tender']=='card' and not pg[order]:exceptions.append({'order_id':order,'payment_ids':'','amount':sale['total'],'issue':'No captured payment in supplied export; verify before collecting'})
    elif len(pg[order])>1:exceptions.append({'order_id':order,'payment_ids':'; '.join(p['payment_id'] for p in pg[order]),'amount':sale['total'],'issue':'Two captured charges for one sale'})
for p in payments:
    if not p['order_id']:exceptions.append({'order_id':'unmatched','payment_ids':p['payment_id'],'amount':p['amount'],'issue':'No order reference; terminal:T2 on '+p['date']})
write('payment_exceptions.csv',exceptions)
subtotal=sum(D(x['subtotal']) for x in sales);discount=sum(D(x['discount']) for x in sales);tax=sum(D(x['tax']) for x in sales)
succeeded=sum(D(x['amount']) for x in refunds if x['status']=='succeeded')
refund_pretax=sum(cents(D(x['amount'])/D('1.08')) for x in refunds if x['status']=='succeeded')
refund_tax=succeeded-refund_pretax
write('september_sales_report_reconciled.csv',[
 {'line':'Unique September orders','amount':len(sales),'note':'Dates filtered; exact duplicates excluded'},
 {'line':'Gross merchandise sales','amount':subtotal,'note':'Gift cards sold separately; no gift-card purchase lines in register'},
 {'line':'Discounts','amount':discount,'note':'As charged; improper discounts listed for owner review'},
 {'line':'Merchandise sales after discounts before refunds','amount':subtotal-discount,'note':'Excludes $425 gift cards sold'},
 {'line':'Sales tax collected before refunds','amount':tax,'note':'September 8%; no historical repricing'},
 {'line':'Customer sale totals before refunds','amount':subtotal-discount+tax,'note':'Excludes duplicate card charge and unmatched terminal charge'},
 {'line':'Completed refunds including duplicate','amount':succeeded,'note':'RF-010 failed and RF-011 pending excluded'},
 {'line':'Completed refunds excluding duplicate RF-013','amount':succeeded-D('93.42'),'note':'Genuine returns total; RF-013 separately flagged as excess refund'},
 {'line':'Genuine returns before tax','amount':refund_pretax-D('86.50'),'note':'Excludes duplicate RF-013'},
 {'line':'Merchandise net sales excluding duplicate refund loss','amount':subtotal-discount-refund_pretax+D('86.50'),'note':'Working operating-sales measure; bookkeeper must classify $93.42 duplicate refund separately'},
 {'line':'Merchandise after all completed refund outflows before tax','amount':subtotal-discount-refund_pretax,'note':'Includes duplicate refund; cash-flow bridge, not final accounting classification'},
 {'line':'Gift cards sold','amount':'425.00','note':'Liability increase; not extra merchandise revenue'},
 {'line':'Gift cards redeemed','amount':'180.00','note':'Liability decrease; ledger source, verify against redemption records'},
 {'line':'Gift-card closing liability','amount':'1485.00','note':'1240 + 425 - 180; original 1305 understated by 180'},
])
write('september_tax_return_review.csv',[
 {'line':'Taxable sales before returns','amount':subtotal-discount,'note':'490 unique September sales; rate 8%'},
 {'line':'Genuine refund taxable-base reduction','amount':refund_pretax-D('86.50'),'note':'Excludes second full refund RF-013'},
 {'line':'Taxable sales after genuine returns','amount':subtotal-discount-refund_pretax+D('86.50'),'note':'Bookkeeper review; unmatched PAY-00382 not yet assigned'},
 {'line':'Tax after genuine refund tax reductions','amount':tax-refund_tax+D('6.92'),'note':'1867.14; extra refund credit requires confirmation'},
 {'line':'Taxable sales if duplicate RF-013 also qualifies for tax credit','amount':subtotal-discount-refund_pretax,'note':'23252.70; conditional alternative'},
 {'line':'Tax after all completed refunds if credits allowable','amount':tax-refund_tax,'note':'1860.22; $59.07 above original draft 1801.15'},
 {'line':'Unmatched charge PAY-00382','amount':'37.80','note':'If taxable sale, may imply $35 base + $2.80 tax; do not add until matched'},
 {'line':'Rate','amount':'8%','note':'September only; October rate is 8.25%'},
])
print('September unique orders:',len(sales),'subtotal:',subtotal,'discount:',discount,'tax:',tax)
print('Fee exceptions:',len(fees),'excess:',sum(D(x['excess_fee']) for x in fees))
print('Payout minus bank:',sum(D(x['payout_minus_bank']) for x in reconciled))
print('Payout unexplained deductions:',[(x['payout_id'],x['processor_unexplained_deduction']) for x in reconciled if D(x['processor_unexplained_deduction'])])
