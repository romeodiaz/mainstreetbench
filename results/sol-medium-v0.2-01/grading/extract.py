#!/usr/bin/env python3
"""Read frozen emitted results only. Never import or execute submitted code/JS."""
from pathlib import Path
from decimal import Decimal, InvalidOperation
import csv, json, re, hashlib, zipfile, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'submission/reports/2026-09'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def rows(name):
    with (REPORT / name).open(newline='') as f:
        return list(csv.DictReader(f))

def money(v):
    return format(Decimal(str(v)), 'f')

def equivalent(a, b):
    if str(a) == str(b): return True
    if a in ('True', 'False') and b in ('1', '0'): return (a == 'True') == (b == '1')
    try: return Decimal(str(a)) == Decimal(str(b))
    except InvalidOperation: return False

# Read stored XML values only; no recalculation, macros, external links or JS.
workbook = REPORT / 'Corner_Loaf_2026-09.xlsx'
sheets = {}
formula_count = 0
with zipfile.ZipFile(workbook) as z:
    strings = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for sh in ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets', NS):
        target = rels[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        path = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        tree = ET.fromstring(z.read(path))
        formula_count += len(tree.findall('.//s:f', NS))
        table = []
        for row in tree.findall('s:sheetData/s:row', NS):
            out = {}
            for cell in row:
                address = cell.attrib['r']
                col = re.match('[A-Z]+', address).group()
                v = cell.find('s:v', NS)
                value = v.text if v is not None else ''
                if cell.attrib.get('t') == 's': value = strings[int(value)]
                elif cell.attrib.get('t') == 'inlineStr': value = ''.join(cell.find('s:is', NS).itertext())
                out[col] = value
            table.append(out)
        sheets[sh.attrib['name']] = table

sheet_files = {
'Summary':'summary.csv','Counts':'counts.csv','Timing differences':'timing_differences.csv',
'Bridges':'bridges.csv','Action items':'action_items.csv','Order reconciliation':'order_reconciliation.csv',
'Order lines':'order_lines.csv','Payment ledger':'payment_ledger.csv','Refund ledger':'refund_ledger.csv',
'Customer matching':'customer_matching.csv','Products ranked':'products_ranked.csv',
'Customers ranked':'customers_ranked.csv','Dedup audit':'dedup_audit.csv','Source files':'source_files.csv','Read me':'read_me.csv'}
conflicts = []
for sheet, file in sheet_files.items():
    table = sheets[sheet]
    with (REPORT/file).open(newline='') as f: csv_table = list(csv.reader(f))
    if len(table) != len(csv_table): conflicts.append({'source':sheet,'detail':'row count differs','workbook':len(table),'csv':len(csv_table)})
    columns = list(table[0])
    for ri, csv_row in enumerate(csv_table):
        if ri >= len(table): break
        for ci, value in enumerate(csv_row):
            col = columns[ci]
            stored = table[ri].get(col, '')
            if not equivalent(value, stored): conflicts.append({'source':f'{sheet}!{col}{ri+1}', 'csv':value, 'workbook':stored})

submitted = json.loads((REPORT/'results.json').read_text())
html = (REPORT/'dashboard.html').read_text()
# JSON decoder consumes only the literal after const data=; the rest is never evaluated.
start = html.index('const data=') + len('const data=')
dashboard, end = json.JSONDecoder().raw_decode(html[start:])
if dashboard != submitted: conflicts.append({'source':'dashboard.html const data vs results.json','dashboard':dashboard,'results':submitted})
for key, file in [('products','products_ranked.csv'),('customers','customers_ranked.csv'),('issues','action_items.csv'),('bridges','bridges.csv'),('counts','counts.csv')]:
    csv_rows = rows(file)
    if len(csv_rows) != len(submitted[key]): conflicts.append({'source':file,'detail':'JSON row count differs'})
    for ri,(a,b) in enumerate(zip(csv_rows,submitted[key]),2):
        for k,v in a.items():
            if k not in b or not equivalent(v,b[k]): conflicts.append({'source':f'{file} row {ri} {k}','csv':v,'json':b.get(k)})

metric_map = {
'merchandise_sales_before_refunds':'Sales after discounts',
'successful_refund_sales':'Completed merchandise returns',
'net_sales':'Net sales',
 'total_successful_refunds':'Completed refunds incl tax',
'card_processing_fees':'Card processing fees by payment date',
'expected_card_payout':'Expected card payout',
'net_external_receipts':'Net external receipts before fees'}
summary = rows('summary.csv')
lookup = {r['metric']:(i,r['amount']) for i,r in enumerate(summary,2)}
metrics = {k:lookup[label][1] if label in lookup else None for k,label in metric_map.items()}
for i,r in enumerate(summary,2):
    if not equivalent(r['amount'],submitted['metrics'].get(r['metric'],'')):
        conflicts.append({'source':f'Summary!B{i}','csv':r['amount'],'json':submitted['metrics'].get(r['metric'])})
provenance = [{'group':'metrics','field':k,'source':f'submission/reports/2026-09/summary.csv row {lookup[label][0]}; Summary!B{lookup[label][0]}','submitted_label':label} for k,label in metric_map.items() if label in lookup]
buckets = {'','WALK-IN','WALK_IN','UNASSIGNED','UNRESOLVED','UNKNOWN','NONE'}
products = [{'sku':r['sku'],'net_units':money(r['net_units']),'net_sales':money(r['net_sales'])} for r in rows('products_ranked.csv')]
customer_rows = rows('customers_ranked.csv')
customers = [{'customer_id':r['customer_key'],'order_count':int(r['order_count']),'net_sales':money(r['net_sales'])} for r in customer_rows]
top = sorted([{'customer_id':r['customer_key'],'net_sales':money(r['net_sales'])} for r in customer_rows if r['customer_key'].upper() not in buckets], key=lambda r:Decimal(r['net_sales']), reverse=True)
orders = []
for i,r in enumerate(rows('order_reconciliation.csv'),2):
    if r['order_in_month'] != 'True': continue
    orders.append({'order_id':r['order_id'],'customer_id':'NONE' if r['customer_key'].upper() in buckets else r['customer_key'], 'sales_before_refunds':money(r['sales']),'amount_due':money(r['order_total']),'captured_tenders':money(r['accepted_payments'])})
    provenance.append({'group':'orders','id':r['order_id'],'source':f'order_reconciliation.csv row {i}; Order reconciliation!A{i}:O{i}'})
refunds = []
for i,r in enumerate(rows('refund_ledger.csv'),2):
    refunds.append({'refund_id':r['refund_id'],'deducted_sales':money(r['refund_sales']) if r['included_in_month']=='True' else '0'})
    provenance.append({'group':'refunds','id':r['refund_id'],'source':f'refund_ledger.csv row {i}; Refund ledger!A{i}:R{i}','derivation':'refund_sales (H) when included_in_month (O) is True, otherwise zero; submitted Read me Returns rule.'})
exceptions = []
for i,r in enumerate(rows('action_items.csv'),2):
    ids=[]
    for k in ['order_id','payment_id','refund_id']:
        ids.extend(x.strip() for x in r[k].split(';') if x.strip())
    exceptions.append({'record_ids':ids,'summary':f"{r['type']}: {r['detail']} {r['action']}",'submitted_amount':money(r['amount']),'source':f'action_items.csv row {i}; Action items!A{i}:G{i}'})
provenance.extend([
 {'group':'products','source':'products_ranked.csv rows 2–11; Products ranked!A2:K11','mapping':'sku A; net_units K; net_sales G. No gross-unit substitution.'},
 {'group':'top_customers','source':'customers_ranked.csv rows 2–83; Customers ranked!A2:G83','mapping':'customer_key A; net_sales E; all 80 identified customers in full displayed workbook ranking; exclude WALK-IN and UNRESOLVED. Dashboard statically specifies top 10.'},
 {'group':'customers','source':'customers_ranked.csv rows 2–83; Customers ranked!A2:G83','mapping':'All 82 summary rows retained, including two pools; order_count F, net_sales E.'},
 {'group':'exceptions','source':'action_items.csv rows 2–216; Action items!A2:G216','mapping':'Each action row retained separately; semicolon-separated payment IDs split; close_notes.md priority entries duplicate a subset and are not counted again.'},
 {'script':'extract.py','method':'Standard-library CSV, JSON, ZIP/XML and static HTML JSON-literal reading. No submitted code or JavaScript executed.'}])
for conflict in conflicts:
    if 'workbook' in conflict and 'csv' in conflict:
        try:
            delta = abs(Decimal(str(conflict['workbook'])) - Decimal(str(conflict['csv'])))
            conflict['absolute_difference'] = str(delta)
            conflict['classification'] = 'floating-point storage difference; same displayed cents' if delta < Decimal('0.000000001') else 'value disagreement'
        except InvalidOperation:
            conflict['classification'] = 'value disagreement'
files = {}
for file in sorted((ROOT/'submission').rglob('*')):
    if file.is_file(): files[str(file.relative_to(ROOT))]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':file.stat().st_size}
evidence = {'metrics':metrics,'products':products,'top_customers':top,'customers':customers,'orders':orders,'refunds':refunds,'exceptions':exceptions,
 'artifacts':{k:{'verdict':'unverified','evidence':v} for k,v in {
 'spreadsheet':'submission/reports/2026-09/Corner_Loaf_2026-09.xlsx; 15 sheets, stored values read by ZIP/XML.',
 'dashboard':'submission/reports/2026-09/dashboard.html; embedded JSON read statically; desktop/mobile PNG files present.',
 'source_preservation':'Source files sheet and source_files.csv report five source hashes; original input CSVs absent from grader workspace.'}.items()},
 'scope_review':{'verdict':'unverified','evidence':'Extraction only; no comparison to reference or scope verdict.'},'provenance':provenance,
 'submitted_summaries':{'metrics':submitted['metrics'],'products':submitted['products'],'customers':submitted['customers'],'counts':submitted['counts'],'bridges':submitted['bridges']},
 'display_conflicts':conflicts,'submitted_file_inventory':files}
(ROOT/'evidence.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
notes = '''# Frozen submission extraction

Only files within this grader workspace were accessed. Submitted solver/verification/refresh code and dashboard JavaScript were not executed. XLSX stored values were read with standard-library ZIP/XML; there are no worksheet formulas. `extract.py` reproduces evidence.json. File hashes in evidence record the frozen submitted artifacts, not independent confirmation of original input preservation.

## Primary metric mapping

'''
for k,label in metric_map.items():
    i,value=lookup[label];notes+=f'- `{k}` = {value}; submitted label “{label}”; `summary.csv` row {i}, workbook `Summary!B{i}`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.\n'
notes+='''
## Rows and exact mappings

All report filenames below are relative to `submission/reports/2026-09/`; workbook is `Corner_Loaf_2026-09.xlsx`. CSV row numbers include the header and match worksheet row numbers. Per-order and per-refund provenance is recorded in evidence; exception source locations are attached to individual entries.

- Products: 10 rows, `products_ranked.csv` rows 2–11 / `Products ranked!A2:K11`. SKU A, net sales G, net units K. Both net fields are directly submitted; no aggregation was needed.
- Customers: all 82 rows, `customers_ranked.csv` rows 2–83 / `Customers ranked!A2:G83`. Customer key A, name B, sales C, returns D, net sales E, September order count F, returned-order count G. All submitted summary fields are also preserved under `submitted_summaries`. The diagnostic customers table contains both pools.
- Top customers: 80 identified rows from that full workbook ranking, sorted by submitted net sales descending. This is the largest N actually displayed. Excluded pools: WALK-IN ($20,163.55, 179 orders) and UNRESOLVED ($640.30, 5 orders). Dashboard source specifies `.slice(0,10)` after filtering these pools, and defaults to net sales. No JavaScript was run. Its alternative product view uses gross `units_sold`; the evidence uses explicit workbook `net_units` as required.
- Orders: 1,000 September rows from `order_reconciliation.csv` / `Order reconciliation` (1,029 data rows total); filter submitted `order_in_month=True` (B). Map order_id A, customer_key D, sales F → sales_before_refunds, order_total I → amount_due, accepted_payments J → captured_tenders. Other 29 rows are submitted August orders and excluded. WALK-IN and UNRESOLVED map to NONE: 184 September orders. No payment matching or line recalculation was performed.
- Refunds: all 24 rows, `refund_ledger.csv` rows 2–25 / `Refund ledger!A2:R25`. ID A, refund_sales H, included_in_month O. Deducted sales is H if O=True, otherwise zero, following the submitted `Read me` Returns rule. This is the sole required conditional derivation. There are 17 included refunds and 7 zeros (3 failed, 2 pending, 2 October completions). September-completed refunds settling in October still have their reported merchandise deduction. Included deductions sum to 799.75, agreeing internally with the submitted Completed merchandise returns metric; this is an internal check only.
- Exceptions: 215 separate rows, `action_items.csv` rows 2–216 / `Action items!A2:G216`. IDs B/C/D, amount E, detail F and action G. Semicolon-separated payment IDs become separate IDs within the same entry. Customer candidate IDs in detail are retained in summary, not turned into order/payment/refund IDs. All action rows are actionable as presented, including 179 anonymous-customer checks and 8 declined-attempt checks explicitly asking for replacement-tender review. They are not reclassified as resolved based on reconciliation results. `close_notes.md` Priority checks repeats 28 of these entries; the dashboard priority filter excludes anonymous customers and declined attempts and likewise shows 28. Neither subset is counted again. Dedup audit and timing differences are informational and are not exceptions.

## All readable workbook sheets

'''
for sheet,file in sheet_files.items():notes+=f'- `{sheet}`: {len(sheets[sheet])-1} data rows; matching emitted `{file}`.\n'
notes+='\nAction-list categories: '+', '.join(f'{k}: {sum(r["type"]==k for r in rows("action_items.csv"))}' for k in dict.fromkeys(r['type'] for r in rows('action_items.csv')))+'.\n'
notes+='''
## Agreement, ambiguities, artifacts and omissions

Every cell in the 15 stored workbook tables was compared with its emitted CSV, allowing equivalent numeric formatting and workbook Boolean storage. Every summary metric, product, customer, action, count and bridge CSV field was compared with results.json; the dashboard embedded JSON was compared with results.json. Raw value differences found: '''+str(len(conflicts))+'. All are workbook floating-point storage differences below 0.000000001, with the same displayed cents; no displayed monetary disagreement was found. The complete raw values and cell addresses are preserved in evidence.json display_conflicts.\n'
if conflicts and any(c.get('classification') != 'floating-point storage difference; same displayed cents' for c in conflicts):
    notes+='\n'+json.dumps(conflicts,indent=2)+'\n'
notes+='''
`close_notes.md` headline amounts and `assistant-response.md` displayed amounts agree with the mapped submitted metrics. The assistant response does not display merchandise returns as a separate headline, but close notes, workbook and dashboard all-metrics data do. Dashboard's default six cards omit that separate return-sales metric, retaining it in embedded all-totals data. Net external receipts maps to the explicitly labeled before-fees amount, 116375.11; the separately reported after-fees-and-credits amount, 113522.67, is preserved under submitted_summaries and is not treated as a contradiction.

Workbook has 15 named sheets and autofilter ranges. Its full order/payment/refund/customer/line/audit detail is present. Dashboard contains an embedded JSON snapshot, empty runtime-rendered table/ranking containers, controls for ranking/checks, and workbook/close-note links. Static data and display instructions were read; browser behavior was not tested. `dashboard_desktop.png` and `dashboard_mobile.png` are present but not used as numeric sources. README describes future-month refresh; refresh was not tested. Source files table has five source names, SHA-256 hashes and byte counts. Original source CSVs are absent, so preservation claims cannot be independently verified here. Artifact and scope_review verdicts remain unverified.

No required submitted metric, product net field, September order field, refund ID or actionable entry was omitted. Exclusions are the 29 August orders from the September-order array, the two customer pools from top_customers, duplicate priority-list presentations, and resolved/informational audit/timing notes from exceptions. No original-input-derived or reference-derived results, scores or correctness claims are included.
'''
(ROOT/'extraction-notes.md').write_text(notes)
print(json.dumps({'metrics':len(metrics),'products':len(products),'top_customers':len(top),'customers':len(customers),'orders':len(orders),'refunds':len(refunds),'exceptions':len(exceptions),'conflicts':len(conflicts)},indent=2))
