"""Read-only reconciliation of original books; writes review artifacts beside this script."""
import csv,collections,re
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'audit'
def read(name):
 with (BASE/'books'/f'{name}.csv').open() as f:return list(csv.DictReader(f))
def write(name,rows):
 if rows:
  with (OUT/name).open('w') as f:
   w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def cent(n):return n.quantize(D('.01'),rounding=ROUND_HALF_UP)
raw=read('register_export_sep01-15')+read('register_export_sep16-30');seen={};excluded=[]
for x in raw:
 if not x['date'].startswith('2026-09'):excluded.append({**x,'reason':'Outside September'});continue
 if x['order_id'] in seen:
  assert seen[x['order_id']]==x,'Conflicting duplicate requires manual review'
  excluded.append({**x,'reason':'Identical repeated export row'});continue
 seen[x['order_id']]=x
write('september_register_reconciled.csv',list(seen.values()));write('excluded_register_rows.csv',excluded)
payments=read('card_payments');fees=[]
for x in payments:
 e=cent(D(x['amount'])*D('.029')+D('.30'))
 if D(x['fee'])!=e:fees.append({**x,'contract_fee':e,'excess_fee':D(x['fee'])-e})
write('processor_fee_exceptions.csv',fees)
refunds=read('refunds');applied=collections.defaultdict(lambda:D(0));attributed=[]
for x in refunds:
 r=seen[x['order_id']];amount=D(x['amount']) if x['status']=='succeeded' else D(0)
 genuine=min(amount,max(D(r['total'])-applied[x['order_id']],D(0)))
 # Apply only up to the original sale to returns; excess is a separate receivable/loss.
 tax=cent(genuine*D(r['tax'])/D(r['total']));applied[x['order_id']]+=genuine
 attributed.append({**x,'sale_return_gross':genuine,'sale_return_tax':tax,'sale_return_net':genuine-tax,'excess_refund':amount-genuine})
write('refund_reconciliation.csv',attributed)
net=sum(D(x['subtotal'])-D(x['discount']) for x in seen.values());tax=sum(D(x['tax']) for x in seen.values())
returns_net=sum(D(x['sale_return_net']) for x in attributed);returns_tax=sum(D(x['sale_return_tax']) for x in attributed)
summary=[{'line':k,'amount':v,'note':n} for k,v,n in [
 ('Unique September receipts',len(seen),'Original exports preserved'),
 ('Food sales before returns',net,'After recorded discounts; excludes gift-card issuance'),
 ('Sales tax collected before returns',tax,'As recorded, including CL-0331 overcollection'),
 ('Successful processor refunds',sum(D(x['amount']) for x in refunds if x['status']=='succeeded'),'Actual money refunded'),
 ('Refunds attributable to sales, before tax',returns_net,'Duplicate/excess refunds excluded from sales returns'),
 ('Refunded sales tax attributable to sales',returns_tax,'Proportional allocation; bookkeeper must approve'),
 ('Net food sales after sale returns',net-returns_net,'Unresolved losses and suspected discount abuse are separate'),
 ('Net recorded sales tax after sale returns',tax-returns_tax,'Do not file without bookkeeper review'),
 ('Excess/duplicate refund loss or receivable',sum(D(x['excess_refund']) for x in attributed),'RF-012 and RF-013; not a second sale reversal'),
 ('Gift cards sold',D('425'),'Liability, not food sales revenue'),
 ('Gift card liability at September close',D('1240')+D('425')-D('180'),'Corrected from 1305'),
 ('Processor fees in excess of contract',sum(D(x['excess_fee']) for x in fees),f'{len(fees)} payments; see exact IDs'),
 ('Cash drawer shortages',sum(D(x['expected_cash'])-D(x['counted_cash']) for x in read('cash_drawer')),'Counted amounts match bank cash deposits'),
]]
write('september_summary_reconciled.csv',summary)
bank=read('bank_statement');payouts=read('payouts');payout_rows=[]
for x in payouts:
 charges=sum(D(p['amount'])-D(p['fee']) for p in payments if p['payout_id']==x['payout_id'])
 deposits=sum(D(b['amount']) for b in bank if x['payout_id'] in b['description'])
 payout_rows.append({**x,'charges_less_fees':charges,'deductions':charges-D(x['amount']),'bank_deposit':deposits,'missing_from_bank':D(x['amount'])-deposits})
write('payout_reconciliation.csv',payout_rows)
for x in summary:print(x)
print('missing payouts',[x for x in payout_rows if x['missing_from_bank']])
print('fee dates',collections.Counter(x['date'] for x in fees))
print('special receipt',seen['CL-0331'])
print('raw goods',sum(D(x['subtotal'])-D(x['discount']) for x in raw),'excluded net',sum(D(x['subtotal'])-D(x['discount']) for x in excluded))
