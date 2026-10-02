"""One-time, guarded changes authorized by customer emails; retains every order ID."""
import sys,sqlite3,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'website'))
from bakery.db import Database
from bakery.pricing import price_order
from bakery.settings import tax_rate
import datetime as dt

def apply():
 db=Database(str(ROOT/'website/data/bakery.db'))
 before={t:[dict(r) for r in db.query('SELECT * FROM '+t)] for t in ['orders','order_items','gift_cards','payments_received','products']}
 if (ROOT/'review/order-changes.json').exists():raise RuntimeError('Already applied; review the change log rather than running again')
 assert db.order(39)['customer_email']=='victor.chen@example.com'
 assert db.order(41)['customer_email']=='laura.bennett@example.com'
 assert [tuple(r) for r in db.order_items(40)] != []
 assert [dict(r) | {'order_id':40} for r in db.order_items(41)] == [dict(r) for r in db.order_items(40)]
 db.cancel_order(39);db.cancel_order(41)
 # Only item changes explicitly requested, not a repricing of existing orders.
 with db.conn:
  db.conn.execute("UPDATE products SET price=3.50 WHERE sku='CINNAMON325'")
  db.conn.execute("UPDATE products SET active=0 WHERE sku='PIE32'")
  for oid,email,new in [(28,'gloria.park@example.com',[('BREAD9',3),('CROISSANT21',1)]),(36,'diego.ramos@example.com',[('BREAD9',1),('BAGUETTE5',1)])]:
   row=db.order(oid);assert row['customer_email']==email and row['status']=='placed'
   lines=[]
   for sku,qty in new:
    p=db.product(sku);lines.append(dict(sku=sku,name=p['name'],qty=qty,unit_price=p['price'],line_total=round(qty*p['price'],2),category=p['category']))
   totals=price_order(lines,None,tax_rate(dt.date(2026,10,1)))
   db.conn.execute('DELETE FROM order_items WHERE order_id=?',(oid,))
   db.conn.executemany('INSERT INTO order_items(order_id,sku,name,qty,unit_price,line_total) VALUES(?,?,?,?,?,?)',[(oid,l['sku'],l['name'],l['qty'],l['unit_price'],l['line_total']) for l in lines])
   db.conn.execute('UPDATE orders SET subtotal=?,discount=?,tax=?,total=? WHERE id=?',(*[totals[k] for k in ['subtotal','discount','tax','total']],oid))
 after={t:[dict(r) for r in db.query('SELECT * FROM '+t)] for t in before}
 assert [r['id'] for r in before['orders']]==[r['id'] for r in after['orders']]
 assert all(a==b for a,b in zip(before['orders'],after['orders']) if a['id'] not in [28,36,39,41])
 assert db.gift_card('DK75-SW8R-933M')['balance']==25
 assert db.query('PRAGMA integrity_check')[0][0]=='ok'
 (ROOT/'review/order-changes.json').write_text(json.dumps({'before':before,'after':after},indent=2)+'\n')
 print('All 43 order IDs retained. Only requested orders 28, 36, 39, 41 changed. Integrity check OK.')
if __name__=='__main__':apply()
