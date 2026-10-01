#!/usr/bin/env python3
"""Rebuild a bakery month close; source CSVs are read-only. See README.md."""
import argparse, csv, re, json, hashlib, html
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict, Counter
import xlsxwriter
D=Decimal
ZERO=D('0'); CENT=D('.01')
def money(x): return D(str(x or '0'))
def rounded(x): return x.quantize(CENT, rounding=ROUND_HALF_UP)
def total(rows,key): return sum((money(r[key]) for r in rows),ZERO)
def norm(x): return re.sub(r'[^a-z0-9]','',x.lower())
def phone(x): return re.sub(r'\D','',x)
def within(value,month): return bool(value) and value[:7]==month
def public(x):
 if isinstance(x,D): return float(x)
 if isinstance(x,set): return sorted(x)
 raise TypeError(type(x).__name__)
def run(src,out,month):
 out.mkdir(parents=True,exist_ok=True)
 issues=[]; audit=[]; provenance=[]
 def issue(kind,order='',payment='',refund='',amount=ZERO,detail='',action=''):
  issues.append(dict(type=kind,order_id=order,payment_id=payment,refund_id=refund,amount=amount,detail=detail,action=action))
 def load(name,key,version=False):
  paths=sorted(src.glob(name+'.csv'))+sorted(src.glob(name+'_*.csv'))
  if not paths: raise ValueError('Missing '+name+'.csv in '+str(src))
  rows=[]
  for p in paths:
   provenance.append(dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
   with p.open(newline='',encoding='utf-8-sig') as f:
    for i,r in enumerate(csv.DictReader(f),2):
     rows.append((r,str(p),i))
  groups=defaultdict(list)
  for r,p,i in rows: groups[r[key]].append((r,p,i))
  cleaned=[]
  for ident,group in groups.items():
   if not ident: raise ValueError('Blank '+key)
   maxver=max(int(r['record_version']) for r,p,i in group) if version else None
   candidates=[x for x in group if not version or int(x[0]['record_version'])==maxver]
   unique={json.dumps(r,sort_keys=True) for r,p,i in candidates}
   if len(unique)>1: raise ValueError(f'Conflicting records for {ident}; resolve in copies of input exports before rerun.')
   chosen=candidates[0]; cleaned.append(dict(chosen[0]))
   seen=set()
   for r,p,i in group:
    s=json.dumps(r,sort_keys=True)
    decision='kept'
    if s in seen: decision='exact repeat removed'
    elif version and int(r['record_version'])<maxver: decision='older version superseded'
    seen.add(s)
    if decision!='kept': audit.append(dict(dataset=name,id=ident,source=p,row=i,decision=decision,record_version=r.get('record_version',''),amount=r.get('line_total',r.get('amount',r.get('refund_total','')))))
  return cleaned
 lines=load('orders','line_id',True); payments=load('payments','payment_id'); refunds=load('refunds','refund_id'); customers=load('customers','customer_id'); products=load('products','sku')
 
 for p in payments:
  if p['status'] not in {'captured','declined'} or p['tender'] not in {'card','cash','gift_card'}: raise ValueError('Unsupported payment status/tender: '+p['payment_id'])
 for r in refunds:
  if r['status'] not in {'succeeded','failed','pending'} or r['tender'] not in {'card','cash'}: raise ValueError('Unsupported refund status/tender: '+r['refund_id'])
 catalog={r['sku']:r for r in products}; cust={r['customer_id']:r for r in customers}
 lookup={key:defaultdict(set) for key in ['email','phone','name','loyalty']}
 for r in customers:
  for key,value in [('email',r['email'].strip().lower()),('phone',phone(r['phone'])),('name',norm(r['customer_name'])),('loyalty',r['loyalty_reference'])]:
   if value: lookup[key][value].add(r['customer_id'])
 byorder=defaultdict(list); byline={r['line_id']:r for r in lines}
 for r in lines:
  if r['sku'] not in catalog: raise ValueError('Unknown SKU '+r['sku'])
  r['order_in_month']=within(r['ordered_at'],month)
  r['category']=catalog[r['sku']]['category']; r['canonical_product']=catalog[r['sku']]['product_name']
  r['gross_sales']=money(r['quantity'])*money(r['unit_price'])
  r['discounted_amount']=r['gross_sales']-money(r['discount_amount'])
  r['sales']=r['discounted_amount'] if r['category']=='merchandise' else ZERO
  r['gift_card_value']=r['discounted_amount'] if r['category']=='gift_card' else ZERO
  r['expected_tax']=rounded(r['discounted_amount']*money(catalog[r['sku']]['tax_rate']))
  r['expected_total']=r['discounted_amount']+r['expected_tax']
  if money(r['tax_amount'])!=r['expected_tax'] or money(r['line_total'])!=r['expected_total']:
   issue('Line arithmetic / tax',r['order_id'],amount=money(r['line_total'])-r['expected_total'],detail=r['line_id'],action='Check exported tax, discounts and line total; sales use charged price.')
  byorder[r['order_id']].append(r)
 identities=[]; resolved={}
 for oid,rows in byorder.items():
  ids={r['customer_id'] for r in rows if r['customer_id']}; loyalty=set(); signals=[]
  for r in rows:
   for x in re.findall(r'CL-\d+',r['notes']): loyalty|=lookup['loyalty'].get(x,set())
   for key,value in [('email',r['customer_email'].strip().lower()),('phone',phone(r['customer_phone'])),('name',norm(r['customer_name']))]:
    if value and lookup[key].get(value): signals.append((key,lookup[key][value]))
  strong=ids|loyalty
  candidates=set().union(*(v for k,v in signals)) if signals else set()
  cid=''; method=''; reason=''
  if len(strong)==1 and next(iter(strong)) in cust:
   cid=next(iter(strong)); method='customer ID' if ids else 'loyalty reference'
   if any(cid not in v for k,v in signals if k!='name'):
    issue('Customer contact conflict',oid,detail=f'{cid}: recorded contact belongs to another member',action='Verify contact details; ID/loyalty retained as authoritative.')
  elif strong: reason='Conflicting or unknown customer IDs / loyalty references'
  elif candidates:
   intersection=set.intersection(*(v for k,v in signals))
   if len(intersection)==1: cid=next(iter(intersection)); method='exact normalized contact/name evidence'
   else: reason='Conflicting contacts' if not intersection else 'Shared household contact; person ambiguous'
  else: reason='No identifying evidence' if not any(r['customer_name'] or r['customer_email'] or r['customer_phone'] for r in rows) else 'No exact customer match'
  bucket=cid or ('UNRESOLVED' if candidates or strong or any(r['customer_name'] or r['customer_email'] or r['customer_phone'] for r in rows) else 'WALK-IN')
  resolved[oid]=bucket
  rec=dict(order_id=oid,ordered_at=rows[0]['ordered_at'],customer_key=bucket,canonical_customer=cust[cid]['customer_name'] if cid else bucket,method=method or reason,candidates='; '.join(sorted(candidates|strong)),raw_names='; '.join(sorted({r['customer_name'] for r in rows if r['customer_name']})),raw_emails='; '.join(sorted({r['customer_email'] for r in rows if r['customer_email']})),raw_phones='; '.join(sorted({r['customer_phone'] for r in rows if r['customer_phone']})))
  identities.append(rec)
  if not cid and (within(rows[0]['ordered_at'],month) or any(within(x['completed_at'],month) and x['order_id']==oid for x in refunds)):
   issue('Unidentified customer' if bucket=='WALK-IN' else 'Customer needs review',oid,amount=sum((r['sales'] for r in rows),ZERO),detail=reason+'; candidates '+rec['candidates'],action='Add a loyalty ID if available; do not merge household members by shared contacts.')
  for r in rows: r['resolved_customer']=bucket
 payby=defaultdict(list)
 for p in payments:
  ref=re.search(r'order:(O-[\w-]+)',p['reference']); reference_id=ref.group(1) if ref else ''
  oid=p['order_id'] or reference_id
  if p['order_id'] and reference_id and p['order_id']!=reference_id:
   issue('Payment reference conflict',p['order_id'],p['payment_id'],amount=money(p['amount']),detail=reference_id,action='Confirm intended order; explicit order ID retained.')
  p['matched_order_id']=oid if oid in byorder else ''; p['match_method']='order_id' if p['order_id'] else ('reference' if reference_id else 'unmatched terminal')
  p['accepted']=p['status']=='captured'
  p['included_in_receipts']=p['accepted'] and within(p['payment_at'],month)
  p['included_in_payout']=p['accepted'] and p['tender']=='card' and within(p['settled_at'],month)
  if p['accepted']:
   if p['matched_order_id']: payby[oid].append(p)
   elif within(p['payment_at'],month) or within(p['settled_at'],month):
    issue('Unmatched accepted payment',oid,p['payment_id'],amount=money(p['amount']),detail=p['reference'],action='Find terminal receipt / order number. Amount retained in receipts and payout; no guessed match.')
   if p['tender']=='card' and not p['settled_at'] and within(p['payment_at'],month): issue('Card missing settlement',oid,p['payment_id'],amount=money(p['amount']),action='Get processor settlement export.')
 orders=[]
 for oid,rows in byorder.items():
  pp=payby[oid]; charged=sum((money(p['amount']) for p in pp),ZERO); due=sum((money(r['line_total']) for r in rows),ZERO); delta=charged-due
  if within(rows[0]['ordered_at'],month) and delta:
   kind='Unpaid order' if not charged else ('Underpaid order' if delta<0 else 'Overpaid / possible duplicate charge')
   issue(kind,oid,'; '.join(p['payment_id'] for p in pp),amount=abs(delta),detail=f'Order due {due}; accepted tenders {charged}.',action='Check receipt and tender history; standalone charges remain unmatched until confirmed.')
  orders.append(dict(order_id=oid,order_in_month=within(rows[0]['ordered_at'],month),ordered_at=rows[0]['ordered_at'],customer_key=resolved[oid],customer_name=cust.get(resolved[oid],{}).get('customer_name',resolved[oid]),sales=sum((r['sales'] for r in rows),ZERO),gift_card_sales=sum((r['gift_card_value'] for r in rows),ZERO),tax=sum((money(r['tax_amount']) for r in rows),ZERO),order_total=due,accepted_payments=charged,payment_difference=delta,payment_ids='; '.join(p['payment_id'] for p in pp),card=sum((money(p['amount']) for p in pp if p['tender']=='card'),ZERO),cash=sum((money(p['amount']) for p in pp if p['tender']=='cash'),ZERO),gift_card_redeemed=sum((money(p['amount']) for p in pp if p['tender']=='gift_card'),ZERO)))
 # Failed attempts never count as receipts; retain them in the payment ledger.
 for p in payments:
  if not p['accepted'] and within(p['payment_at'],month):
   issue('Declined payment attempt',p['matched_order_id'] or p['order_id'],p['payment_id'],amount=money(p['amount']),detail=p['notes'],action='Check replacement tender in order reconciliation; declined amount excluded.')
 refundby=defaultdict(list)
 for r in refunds:
  r['included_in_month']=r['status']=='succeeded' and within(r['completed_at'],month)
  r['included_in_payout']=r['status']=='succeeded' and r['tender']=='card' and within(r['settled_at'],month)
  line=byline.get(r['line_id']); r['sku']=line['sku'] if line else ''; r['resolved_customer']=resolved.get(r['order_id'],'UNRESOLVED')
  if within(r['requested_at'],month) and r['status']!='succeeded':
   issue('Refund '+r['status'],r['order_id'],refund=r['refund_id'],amount=money(r['refund_total']),detail='Excluded from completed refunds.',action='Check processor status; retry or complete only after confirming no successful refund.')
  if r['status']=='succeeded' and not r['completed_at']: issue('Refund missing completion date',r['order_id'],refund=r['refund_id'],amount=money(r['refund_total']),action='Obtain completion timestamp; cannot assign refund month.')
  if not line or line['order_id']!=r['order_id']:
   issue('Refund line mismatch',r['order_id'],refund=r['refund_id'],amount=money(r['refund_total']),action='Get original order line; do not guess product/customer.')
  else:
   if money(r['refund_sales'])+money(r['refund_tax'])!=money(r['refund_total']): issue('Refund arithmetic',r['order_id'],refund=r['refund_id'],amount=money(r['refund_total']),action='Check approved refund components.')
   if r['status']=='succeeded': refundby[r['line_id']].append(r)
   expected=rounded(line['discounted_amount']*money(r['quantity'])/money(line['quantity']))
   # Approved refunds remain actual outflows, even if their amount is unexpected.
   if money(r['refund_sales'])!=expected: issue('Refund amount differs from line',r['order_id'],refund=r['refund_id'],amount=money(r['refund_sales'])-expected,detail=f'Proportional merchandise value {expected}',action='Confirm partial-return approval / correction; retain recorded refund amount.')
  if r['included_in_month'] and r['tender']=='card' and not r['settled_at']: issue('Refund missing settlement',r['order_id'],refund=r['refund_id'],amount=money(r['refund_total']),action='Get processor settlement date.')
 for lid,rr in refundby.items():
  line=byline[lid]
  if total(rr,'quantity')>money(line['quantity']) or total(rr,'refund_total')>money(line['line_total']):
   issue('Possible repeated / excessive refund',line['order_id'],refund='; '.join(r['refund_id'] for r in rr),amount=total(rr,'refund_total'),detail=lid,action='Verify cumulative returned quantity and refund history.')
 ml=[r for r in lines if within(r['ordered_at'],month)]; mo=[r for r in orders if within(r['ordered_at'],month)]
 mp=[r for r in payments if r['accepted'] and within(r['payment_at'],month)]; mr=[r for r in refunds if r['included_in_month']]
 merchandise=[r for r in ml if r['category']=='merchandise']
 card=[p for p in mp if p['tender']=='card']; cash=[p for p in mp if p['tender']=='cash']; gifts=[p for p in mp if p['tender']=='gift_card']
 cardrefund=[r for r in mr if r['tender']=='card']; cashrefund=[r for r in mr if r['tender']=='cash']
 settled=[p for p in payments if p['accepted'] and p['tender']=='card' and within(p['settled_at'],month)]; sr=[r for r in refunds if r['included_in_payout']]
 metrics={
 'Gross merchandise sales':sum((r['gross_sales'] for r in merchandise),ZERO),
 'Merchandise discounts':total(merchandise,'discount_amount'),
 'Sales after discounts':total(ml,'sales'),
 'Completed merchandise returns':total(mr,'refund_sales'),
 'Returns of prior-month orders (merchandise)':total([r for r in mr if r['order_id'] in byorder and byorder[r['order_id']][0]['ordered_at'][:7]<month],'refund_sales'),
 'Successful requests completing after month (incl tax)':total([r for r in refunds if r['status']=='succeeded' and within(r['requested_at'],month) and r['completed_at'][:7]>month],'refund_total'),
 'Net sales':total(ml,'sales')-total(mr,'refund_sales'),
 'Sales tax charged':total(ml,'tax_amount'),
 'Gift cards sold (liability)':total(ml,'gift_card_value'),
 'Order total including tax and gift cards':total(ml,'line_total'),
 'Card receipts by payment date':total(card,'amount'),
 'Cash receipts by payment date':total(cash,'amount'),
 'Gift-card redemptions (not new money)':total(gifts,'amount'),
 'Card processing fees by payment date':total(card,'fee'),
 'Completed card refunds incl tax':total(cardrefund,'refund_total'),
 'Completed cash refunds incl tax':total(cashrefund,'refund_total'),
 'Completed refunds incl tax':total(mr,'refund_total'),
 'Refunded sales tax':total(mr,'refund_tax'),
 'Refund fee credits by completion date':total(cardrefund,'fee_adjustment'),
 'Net external receipts before fees':total(card,'amount')+total(cash,'amount')-total(mr,'refund_total'),
 'Net external receipts after fees and credits':total(card,'amount')+total(cash,'amount')-total(mr,'refund_total')-total(card,'fee')+total(cardrefund,'fee_adjustment'),
 'Card charges settled this month':total(settled,'amount'),
 'Fees on card charges settled this month':total(settled,'fee'),
 'Card refunds settled this month':total(sr,'refund_total'),
 'Refund fee credits settled this month':total(sr,'fee_adjustment'),
 'Expected card payout':total(settled,'amount')-total(settled,'fee')-total(sr,'refund_total')+total(sr,'fee_adjustment'),
 'Net cash receipts':total(cash,'amount')-total(cashrefund,'refund_total'),
 'Gift-card liability movement':total(ml,'gift_card_value')-total(gifts,'amount'),
 'Unmatched receipts by payment date':total([p for p in mp if not p['matched_order_id']],'amount'),
 'Month orders unpaid / underpaid':sum((-r['payment_difference'] for r in mo if r['payment_difference']<0),ZERO),
 'Month orders overpaid':sum((r['payment_difference'] for r in mo if r['payment_difference']>0),ZERO),
 }
 # Explicit bridges for the different accounting clocks.
 bridge=[]
 def br(section,label,value): bridge.append(dict(section=section,component=label,amount=value))
 br('Sales to external receipts','Sales after discounts',metrics['Sales after discounts'])
 br('Sales to external receipts','Add sales tax',metrics['Sales tax charged']); br('Sales to external receipts','Add gift-card sales',metrics['Gift cards sold (liability)'])
 br('Sales to external receipts','Subtract shortages on month orders',-metrics['Month orders unpaid / underpaid']); br('Sales to external receipts','Add excess payments on month orders',metrics['Month orders overpaid'])
 # Order reconciliation uses all dated accepted payments. Remove payments outside the month; add other-month-order receipts and unmatched receipts.
 br('Sales to external receipts','Subtract payments outside month on month orders',-total([p for p in payments if p['accepted'] and p['matched_order_id'] in {r['order_id'] for r in mo} and not within(p['payment_at'],month)],'amount'))
 br('Sales to external receipts','Add month receipts for other-month orders',total([p for p in mp if p['matched_order_id'] and p['matched_order_id'] not in {r['order_id'] for r in mo}],'amount'))
 br('Sales to external receipts','Add unmatched month receipts',metrics['Unmatched receipts by payment date'])
 br('Sales to external receipts','Subtract gift-card redemption tender',-metrics['Gift-card redemptions (not new money)']); br('Sales to external receipts','Subtract completed card/cash refunds',-metrics['Completed refunds incl tax'])
 br('Sales to external receipts','Net external receipts before fees',metrics['Net external receipts before fees'])
 br('Card receipts to payout','Card receipts by payment date',total(card,'amount'))
 br('Card receipts to payout','Add earlier charges settling this month',total([p for p in settled if not within(p['payment_at'],month)],'amount'))
 br('Card receipts to payout','Subtract month charges settling outside month',-total([p for p in card if not within(p['settled_at'],month)],'amount'))
 br('Card receipts to payout','Subtract settlement fees',-total(settled,'fee')); br('Card receipts to payout','Subtract card refunds settled this month',-total(sr,'refund_total')); br('Card receipts to payout','Add settlement refund fee credits',total(sr,'fee_adjustment')); br('Card receipts to payout','Expected card payout',metrics['Expected card payout'])
 for sec in ['Sales to external receipts','Card receipts to payout']:
  b=[r for r in bridge if r['section']==sec]; assert total(b[:-1],'amount')==b[-1]['amount'],sec
 # Rankings use merchandise net sales, with prior-month returns subtracted in completion month.
 pr={k:dict(sku=k,product_name=v['product_name'],gross_sales=ZERO,discounts=ZERO,sales=ZERO,returns=ZERO,net_sales=ZERO,units_sold=ZERO,units_returned=ZERO,order_ids=set()) for k,v in catalog.items() if v['category']=='merchandise'}
 cr={}
 def customerrow(key):
  if key not in cr: cr[key]=dict(customer_key=key,customer_name=cust.get(key,{}).get('customer_name',key),sales=ZERO,returns=ZERO,net_sales=ZERO,order_ids=set(),return_order_ids=set())
  return cr[key]
 for r in mo: customerrow(r['customer_key'])['order_ids'].add(r['order_id'])
 for r in merchandise:
  p=pr[r['sku']]; p['gross_sales']+=r['gross_sales']; p['discounts']+=money(r['discount_amount']); p['sales']+=r['sales']; p['units_sold']+=money(r['quantity']); p['order_ids'].add(r['order_id'])
  c=customerrow(r['resolved_customer']); c['sales']+=r['sales']; c['order_ids'].add(r['order_id'])
 for r in mr:
  if r['sku'] in pr:
   p=pr[r['sku']]; p['returns']+=money(r['refund_sales']); p['units_returned']+=money(r['quantity'])
  c=customerrow(r['resolved_customer']); c['returns']+=money(r['refund_sales']); c['return_order_ids'].add(r['order_id'])
 for p in pr.values(): p['net_sales']=p['sales']-p['returns']; p['order_count']=len(p.pop('order_ids')); p['net_units']=p['units_sold']-p['units_returned']
 for c in cr.values(): c['net_sales']=c['sales']-c['returns']; c['order_count']=len(c.pop('order_ids')); c['returned_order_count']=len(c.pop('return_order_ids'))
 product_rank=sorted(pr.values(),key=lambda r:r['net_sales'],reverse=True); customer_rank=sorted(cr.values(),key=lambda r:r['net_sales'],reverse=True)
 assert total(product_rank,'net_sales')==metrics['Net sales']; assert total(customer_rank,'net_sales')==metrics['Net sales']
 cutoffs=[]
 for p in payments:
  if p['accepted'] and p['tender']=='card' and (within(p['payment_at'],month)!=within(p['settled_at'],month)):
   cutoffs.append(dict(record_type='payment',id=p['payment_id'],order_id=p['matched_order_id'],activity_date=p['payment_at'],settled_at=p['settled_at'],amount=money(p['amount']),fee_or_credit=money(p['fee']),explanation='Earlier charge settling this month' if within(p['settled_at'],month) else 'Month charge settling outside month'))
 for r in refunds:
  if (within(r['requested_at'],month) and r['status']=='succeeded' and not within(r['completed_at'],month)) or (r['status']=='succeeded' and r['tender']=='card' and within(r['completed_at'],month)!=within(r['settled_at'],month)):
   cutoffs.append(dict(record_type='refund',id=r['refund_id'],order_id=r['order_id'],activity_date=r['completed_at'],settled_at=r['settled_at'],amount=money(r['refund_total']),fee_or_credit=money(r['fee_adjustment']),explanation='Requested in month, completed later' if not within(r['completed_at'],month) else 'Completed in month, settles later'))
 metricrows=[dict(metric=k,amount=v) for k,v in metrics.items()]
 counts=[dict(measure='Orders placed in month',count=len(mo)),dict(measure='Order lines retained (all dates)',count=len(lines)),dict(measure='Accepted payments (all dates)',count=sum(p['accepted'] for p in payments)),dict(measure='Export rows removed or superseded',count=len(audit))]
 sheets={'Summary':metricrows,'Counts':counts,'Timing differences':cutoffs,'Bridges':bridge,'Action items':issues,'Order reconciliation':orders,'Order lines':lines,'Payment ledger':payments,'Refund ledger':refunds,'Customer matching':identities,'Products ranked':product_rank,'Customers ranked':customer_rank,'Dedup audit':audit,'Source files':provenance}
 definitions=[dict(topic='Basis',rule=f'{month}; USD; store-local dates. Month determined independently by order, payment, completion and settlement date.'),dict(topic='Sales',rule='Quantity × charged unit price less line discount; merchandise only. Catalog prices never replace historical prices.'),dict(topic='Returns',rule='Only succeeded refunds with completion in month reduce sales; includes returns of earlier orders. Approved amounts retained.'),dict(topic='Payments',rule='Only captured transactions count. Each payment_id counted once. Explicit order ID, then exact order: reference; no amount-only matching.'),dict(topic='Duplicates',rule='Latest record_version per line_id. Exact repeated payment_id/refund_id rows removed. Conflicting same-ID records stop the run for review.'),dict(topic='Customers',rule='Known ID or loyalty reference authoritative; otherwise exact normalized contact/name evidence must resolve to one person. Conflicting/shared contacts stay unresolved. No fuzzy name merging.'),dict(topic='Rankings',rule='Net merchandise sales by SKU and resolved customer; monthly sold orders count once. Returned prior-month orders reported separately. WALK-IN and UNRESOLVED are pools, not customers.'),dict(topic='Fees',rule='Card charge fees by payment date shown separately from refund fee credits and fees by settlement date.'),dict(topic='Receipt vs deposit',rule='Net external receipts exclude gift redemption and fees. Expected payout uses settlement dates and includes earlier-month charges. Neither confirms bank deposits.'),dict(topic='Missing',rule='Bank statement/deposit export; terminal receipts linking unmatched charges; corrected contact/loyalty evidence; confirmation of unresolved refunds; opening gift-card liability; cash deposit/till records.'),dict(topic='Refresh',rule='Use run_month.command or python reconcile.py --input INPUT_FOLDER --month YYYY-MM. See README.md. Regenerate rather than editing output totals.')]
 sheets['Read me']=definitions
 wb=xlsxwriter.Workbook(str(out/('Corner_Loaf_'+month+'.xlsx')),{'strings_to_formulas':False,'strings_to_urls':False})
 fmt=wb.add_format({'num_format':'$#,##0.00;[Red]($#,##0.00)','font_name':'Calibri'}); header=wb.add_format({'bold':True,'bg_color':'#21564E','font_color':'white'}); wrap=wb.add_format({'text_wrap':True,'valign':'top'})
 for title,rows in sheets.items():
  ws=wb.add_worksheet(title); ws.freeze_panes(1,0); ws.set_zoom(90)
  if not rows: ws.write(0,0,'No records'); continue
  keys=list(rows[0]); ws.write_row(0,0,keys,header)
  for j,k in enumerate(keys):
   monetary=any(isinstance(r.get(k),D) for r in rows) and k not in ['quantity','units_sold','units_returned','net_units']
   ws.set_column(j,j,min(55,max(16,len(k)+2)),fmt if monetary else None)
  for i,r in enumerate(rows,1):
   for j,k in enumerate(keys):
    v=r.get(k,''); ws.write(i,j,float(v) if isinstance(v,D) else v,fmt if isinstance(v,D) and k not in ['quantity','units_sold','units_returned','net_units'] else None)
  ws.autofilter(0,0,len(rows),len(keys)-1)
  if title=='Read me': ws.set_column(1,1,105,wrap); ws.set_default_row(44)
  with (out/(title.lower().replace(' ','_')+'.csv')).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
 for sheet,name,label,value in [('Products ranked','Products by net sales',1,6),('Customers ranked','Customers and pools by net sales',1,4)]:
  chart=wb.add_chart({'type':'bar'}); n=min(10,len(sheets[sheet])); chart.add_series({'name':name,'categories':[sheet,1,label,n,label],'values':[sheet,1,value,n,value],'fill':{'color':'#21564E'},'border':{'none':True}}); chart.set_title({'name':name}); chart.set_legend({'none':True}); chart.set_size({'width':720,'height':420}); wb.get_worksheet_by_name(sheet).insert_chart('N2',chart)
 wb.close()
 data=dict(month=month,metrics=metrics,counts=counts,products=product_rank,customers=customer_rank,issues=issues,bridges=bridge)
 (out/'results.json').write_text(json.dumps(data,default=public,indent=2))
 render_dashboard(out,data)
 render_report(out,data,audit)
 print(json.dumps(dict(month=month,metrics=metrics,issue_counts=dict(Counter(i['type'] for i in issues)),dedup_counts=dict(Counter((r['dataset']+' / '+r['decision']) for r in audit))),default=public,indent=2))
 return data

def render_dashboard(out,data):
 template=Path(__file__).with_name('dashboard_template.html').read_text()
 (out/'dashboard.html').write_text(template.replace('__DATA__',json.dumps(data,default=public).replace('<','\\u003c')))

def render_report(out,data,audit):
 m=data['metrics']; dollars=lambda x:f'${x:,.2f}'
 text=f'''# Corner Loaf Bakery — {data['month']} close\n\nSales after discounts: **{dollars(m['Sales after discounts'])}**. Completed merchandise returns: **{dollars(m['Completed merchandise returns'])}**. Net sales: **{dollars(m['Net sales'])}**.\n\nCompleted refunds including tax: **{dollars(m['Completed refunds incl tax'])}**. Card charge fees by payment date: **{dollars(m['Card processing fees by payment date'])}**. Net external receipts before fees: **{dollars(m['Net external receipts before fees'])}**. Expected card payout: **{dollars(m['Expected card payout'])}**. The payout is an expectation; there is no bank statement to confirm deposits.\n\n## Why totals differ\n\nSales exclude tax and gift-card sales. Gift-card redemption pays for an order but brings in no new money. Refund totals include returned tax; only the merchandise portion reduces net sales. Returns of earlier orders reduce this month's sales. Declined attempts and failed/pending refunds do not count as money movements. Card payouts use settlement dates, including earlier charges and excluding charges or refunds settling next month. See the workbook Bridges sheet for the exact arithmetic.\n\n{len(audit)} overlapping or superseded export rows were removed. Distinct payment IDs remain money movements even when they look like repeated charges. They are flagged for review rather than silently removed.\n\n## Priority checks\n\n'''
 for kind in ['Unpaid order','Underpaid order','Overpaid / possible duplicate charge','Unmatched accepted payment','Refund failed','Refund pending','Possible repeated / excessive refund','Customer needs review','Customer contact conflict']:
  rows=[i for i in data['issues'] if i['type']==kind]
  if rows:
   text+=f'### {kind}\n\n'
   for r in rows: text+=f"- {r['order_id']} {r['payment_id']} {r['refund_id']} — {dollars(r['amount'])}. {r['detail']} {r['action']}\n"
   text+='\n'
 text+='## Missing information\n\nBank statements or processor deposit records are needed to verify actual deposits. Terminal receipts are needed to connect standalone payments to orders. Customer IDs or loyalty evidence are needed for unresolved contacts and anonymous walk-ins. Processor follow-up is needed for failed/pending refunds. The opening gift-card balance is needed for the ending liability; till counts and cash deposits are needed to confirm cash on hand or banked cash.\n\nSee Action items for every affected order, including anonymous sales and declined attempts. Customer pools are excluded from the biggest-person ranking on the dashboard.\n'
 (out/'close_notes.md').write_text(text)

if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,default=Path('.')); ap.add_argument('--month',default='2026-09'); ap.add_argument('--output',type=Path)
 args=ap.parse_args()
 if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',args.month): ap.error('month must be YYYY-MM')
 run(args.input,args.output or Path('reports')/args.month,args.month)
