"""Independent checks for supplied September exports and generated artifacts."""
import csv, json, hashlib, zipfile, tempfile, shutil, subprocess, sys
from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict
from xml.etree import ElementTree as ET
root=Path(__file__).parent; out=root/'reports/2026-09'
def read(name):
 with (root/(name+'.csv')).open(newline='') as f: return list(csv.DictReader(f))
def amt(rows,key): return sum((D(r[key]) for r in rows),D(0))
# Recalculate from the original exports, independently of reconcile.py.
groups=defaultdict(list)
for r in read('orders'): groups[r['line_id']].append(r)
lines=[max(rr,key=lambda r:int(r['record_version'])) for rr in groups.values()]
payments=list({r['payment_id']:r for r in read('payments')}.values())
refunds=list({r['refund_id']:r for r in read('refunds')}.values())
merch=[r for r in lines if r['ordered_at'].startswith('2026-09') and r['sku']!='GIFT25']
gross=sum((D(r['quantity'])*D(r['unit_price']) for r in merch),D(0)); sales=gross-amt(merch,'discount_amount')
accepted=[r for r in payments if r['status']=='captured' and r['payment_at'].startswith('2026-09')]
completed=[r for r in refunds if r['status']=='succeeded' and r['completed_at'].startswith('2026-09')]
settled=[r for r in payments if r['status']=='captured' and r['tender']=='card' and r['settled_at'].startswith('2026-09')]
sr=[r for r in refunds if r['status']=='succeeded' and r['tender']=='card' and r['settled_at'].startswith('2026-09')]
expected={'Gross merchandise sales':gross,'Sales after discounts':sales,'Net sales':sales-amt(completed,'refund_sales'),'Completed refunds incl tax':amt(completed,'refund_total'),'Card processing fees by payment date':amt([r for r in accepted if r['tender']=='card'],'fee'),'Net external receipts before fees':amt([r for r in accepted if r['tender'] in ['card','cash']],'amount')-amt(completed,'refund_total'),'Expected card payout':amt(settled,'amount')-amt(settled,'fee')-amt(sr,'refund_total')+amt(sr,'fee_adjustment')}
data=json.loads((out/'results.json').read_text(),parse_float=D)
for k,v in expected.items(): assert v==data['metrics'][k],(k,v,data['metrics'][k])
assert expected['Sales after discounts']==D('108150.50')
assert expected['Expected card payout']==D('84108.06')
assert data['metrics']['Successful requests completing after month (incl tax)']==D('31.11')
assert data['metrics']['Returns of prior-month orders (merchandise)']==D('552')
assert len(lines)==2229 and len(payments)==1048 and len(refunds)==24
for name in ['Sales to external receipts','Card receipts to payout']:
 rows=[r for r in data['bridges'] if r['section']==name]; assert amt(rows[:-1],'amount')==rows[-1]['amount']
for k in ['products','customers']: assert amt(data[k],'net_sales')==data['metrics']['Net sales']
# File hashes prove the CSV sources match what generated the output.
with (out/'source_files.csv').open() as f:
 for r in csv.DictReader(f): assert hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()==r['sha256'],r['file']
# Match workbook Summary values to JSON; also validate the archive/XML and charts.
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(out/'Corner_Loaf_2026-09.xlsx') as z:
 assert z.testzip() is None
 for name in z.namelist():
  if name.endswith('.xml'): ET.fromstring(z.read(name))
 strings=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
 ws=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
 for row in ws.findall('m:sheetData/m:row',ns)[1:]:
  cells=row.findall('m:c',ns); key=strings[int(cells[0].find('m:v',ns).text)]; value=D(cells[1].find('m:v',ns).text)
  assert value.quantize(D('.01'))==D(str(data['metrics'][key])).quantize(D('.01')),(key,value)
 assert len([n for n in z.namelist() if n.startswith('xl/charts/chart') and n.endswith('.xml')])==2
# A future close must use completion/settlement dates rather than the request month.
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 subprocess.run([sys.executable,str(root/'reconcile.py'),'--input',str(root),'--month','2026-10','--output',str(t/'oct')],check=True,capture_output=True)
 octdata=json.loads((t/'oct/results.json').read_text(),parse_float=D)
 assert octdata['metrics']['Completed refunds incl tax']==D('31.11')
 # Conflicting same-ID payments must stop, never silently choose a money value.
 inp=t/'input'; inp.mkdir()
 for name in ['orders','payments','refunds','products','customers']: shutil.copy(root/(name+'.csv'),inp/(name+'.csv'))
 rows=read('payments'); bad=dict(rows[0]); bad['amount']='999.99'
 with (inp/'payments_overlap.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(bad)); w.writeheader(); w.writerow(bad)
 result=subprocess.run([sys.executable,str(root/'reconcile.py'),'--input',str(inp),'--output',str(t/'conflict')],capture_output=True,text=True)
 assert result.returncode!=0 and 'Conflicting records' in result.stderr
print('PASS: independent totals, bridges, rankings, source hashes, workbook XML/values, date cutoffs, conflicting-ID safeguard.')
