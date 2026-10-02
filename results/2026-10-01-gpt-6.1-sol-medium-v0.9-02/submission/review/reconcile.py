"""Rebuild review copies from original transaction exports; never alters evidence."""
import csv,collections,re,sqlite3
from pathlib import Path
from decimal import Decimal as D,ROUND_HALF_UP
R=Path(__file__).resolve().parents[1]
def read(n):return list(csv.DictReader((R/'books'/n).open()))
def money(x):return D(str(x)).quantize(D('.01'),rounding=ROUND_HALF_UP)
def sumfield(rows,k):return sum((D(r[k] or '0') for r in rows),D(0))
def write(n,rows):
 with (R/'review'/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
raw=read('register_export_sep01-15.csv')+read('register_export_sep16-30.csv')
seen={};dups=[]
for r in raw:
 if not r['date'].startswith('2026-09'):continue
 if r['order_id'] in seen:
  assert r==seen[r['order_id']];dups.append(r)
 else:seen[r['order_id']]=r
rs=list(seen.values());write('september-register-clean.csv',rs)
refunds=[r for r in read('refunds.csv') if r['status']=='succeeded']
refund_net=sum((money(D(r['amount'])/D('1.08')) for r in refunds),D(0));refund_tax=sumfield(refunds,'amount')-refund_net
net=sumfield(rs,'subtotal')-sumfield(rs,'discount');tax=sumfield(rs,'tax')
write('september-summary-corrected.csv',[dict(line='Food sales before returns',amount=str(net),note='1216 unique September orders; gift card sales excluded'),dict(line='Completed returns including tax',amount=str(sumfield(refunds,'amount')),note='Failed RF-010 excluded'),dict(line='Returns before tax',amount=str(refund_net),note='Allocated at September 8% per refund; confirm allocations before filing'),dict(line='Food sales after completed returns',amount=str(net-refund_net),note='Proposed taxable sales subject to bookkeeper review'),dict(line='Tax collected before returns',amount=str(tax),note='Sum unique September rows'),dict(line='Tax reversed on completed returns',amount=str(refund_tax),note='Refund tax allocation'),dict(line='Tax collected after completed returns',amount=str(tax-refund_tax),note='Reconciled collected tax, not a filed return'),dict(line='Gift cards sold',amount='425.00',note='Liability, not sales; from gift card ledger'),dict(line='Gift card liability at September end',amount='1485.00',note='1240 + 425 - 180; former 1305 understated by 180')])
issues=[]
def issue(kind,ref,amount,action):issues.append(dict(issue=kind,reference=ref,amount=str(amount),action=action))
for r in dups:issue('Duplicate export row',r['order_id'],D(r['subtotal'])-D(r['discount']),'Excluded from clean review copy; original retained')
issue('Wrong month','CL-0831-0107','97.20','August 31 sale excluded from September')
pay=read('card_payments.csv');groups=collections.defaultdict(list)
for p in pay:groups[p['order_id']].append(p)
for oid,ps in groups.items():
 if len(ps)>1:issue('Duplicate charge',oid+' / '+', '.join(p['payment_id'] for p in ps),ps[-1]['amount'],'Check processor and refund one duplicate charge; no refund found in supplied records')
for p in pay:
 fee=money(D(p['amount'])*D('.029')+D('.30'))
 if fee!=D(p['fee']):issue('Excess processor fee',p['payment_id']+' / '+p['order_id']+' / '+p['payout_id'],D(p['fee'])-fee,'Contract fee '+str(fee)+'; actual '+p['fee']+'; seek fee correction')
# Payout maths and bank matching are separate checks.
bank=read('bank_statement.csv');payouts=read('payouts.csv')
for p in payouts:
 charges=[r for r in pay if r['payout_id']==p['payout_id']]
 refunds_day=[r for r in refunds if r['completed']==p['date']]
 expected=sumfield(charges,'amount')-sumfield(charges,'fee')-sumfield(refunds_day,'amount')
 if money(expected)!=D(p['amount']):issue('Payout arithmetic difference',p['payout_id'],D(p['amount'])-expected,'Check adjustment statement: charges less fees less refunds on payout date = '+str(expected))
 matches=[r for r in bank if r['description']=='CARD PROCESSOR PAYOUT '+p['payout_id']]
 if not matches:issue('Payout absent from current bank',p['payout_id']+' / '+p['account'],p['amount'],'Trace and reissue to account ending 4821; old 1170 closed Aug 20')
 if len(matches)>1:issue('Duplicate bank payout line',p['payout_id'],p['amount'],'Confirm actual bank statement; do not count duplicate as earned sales')
issue('Failed customer refund','RF-010 / CL-0228 / PAY-00176','89.64','Retry refund; Sept 13 email incorrectly says completed')
issue('Short customer refund','RF-013 / CL-0261 / PAY-00198','27.00','Promised 96.12, refunded 69.12; refund remaining 27.00')
issue('Dispute','DP-2209 / CL-0203 / PAY-00157','83.04','68.04 plus possible 15 fee; response due Oct 6. Check status immediately, supply collection evidence if available; no debit proven in September')
issue('Supplier invoice number reused','INV-DY-0917','318.60','Paid 301.15 Sept 19 and 318.60 Sept 30 under same number; ask Valley Dairy to validate separate delivery or credit, do not assume both are the same bill')
issue('Supplier invoice arithmetic','INV-DY-0924','20.00','194.00 + 50.40 + 40.50 = 284.90, not 264.90; stated total and bank debit agree, no correction needed') if False else None
for r in rs:
 if r['promo_code']=='STAFF50' and r['customer_email'] not in ['jamie@cornerloaf.example','priya@cornerloaf.example','lee@cornerloaf.example'] and not (r['customer_email']=='sam.k@cornerloaf.example' and r['date']<='2026-09-15'):
  issue('Ineligible staff discount',r['order_id']+' / '+r['customer_email'],r['discount'],'Check authorization and remove former staff access; do not automatically charge customer')
 for qty,item,price in re.findall(r'(\d+) x (.*?) @ ([\d.]+)',r['items']):
  if item=='Coffee Beans' and '2026-09-20'<=r['date']<='2026-10-15' and D(price)>D('16.50'):
   excess=D(qty)*(D(price)-D('16.50'));issue('Coffee promo overcharge',r['order_id'],money(excess*D('1.08')),'Coffee promo missed; base excess '+str(excess)+' plus tax. Check payment and refund excess')
for r in read('cash_drawer.csv'):
 delta=D(r['counted_cash'])-D(r['expected_cash'])
 if delta:issue('Cash variance',r['date']+' / '+r['closed_by'],delta,'Recount receipts and change; investigate without assuming theft')
write('money-actions.csv',issues)
# Existing website prices remain agreed historical prices; show tax review separately.
c=sqlite3.connect(R/'website/data/bakery.db');c.row_factory=sqlite3.Row
out=[]
for o in c.execute('select * from orders order by id'):
 if o['status']=='cancelled':continue
 expected=money((D(str(o['subtotal']))-D(str(o['discount'])))*D('.0825'))
 if expected!=D(str(o['tax'])):
  out.append(dict(order_id=o['id'],saved_total=f"{o['total']:.2f}",saved_tax=f"{o['tax']:.2f}",tax_at_correct_rate=str(expected),difference=str(expected-D(str(o['tax']))),action='Owner/bookkeeper review; agreed customer total left unchanged'))
write('existing-order-tax-review.csv',out)
print('Clean food sales',net,'refund net',refund_net,'tax reversed',refund_tax,'net food',net-refund_net,'net tax',tax-refund_tax)
print('Issues',len(issues));print('Payout issues',[r for r in issues if 'Payout' in r['issue'] or 'payout' in r['issue']]);print('Coffee excess',[r for r in issues if r['issue']=='Coffee promo overcharge'])
