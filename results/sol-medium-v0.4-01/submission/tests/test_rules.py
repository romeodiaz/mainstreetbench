"""Money rounding and non-destructive upgrades of the original schema."""
import datetime as dt
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bakery.db import Database, SCHEMA, OrderError
from bakery.pricing import price_order


class RulesTest(unittest.TestCase):
    def test_half_cent_rounds_up_and_fixed_coupon_is_capped(self):
        promo = {'percent_off': 10, 'amount_off': None}
        result = price_order([{'sku': 'FOOD', 'qty': 1, 'unit_price': 2.25}], promo)
        self.assertEqual(result, {'subtotal': 2.25, 'discount': .23, 'tax': .16, 'total': 2.18})
        result = price_order([{'sku': 'FOOD', 'qty': 1, 'unit_price': .0625}], None)
        self.assertEqual(result['subtotal'], .06)
        result = price_order([{'qty': 1, 'unit_price': 2.25},
                              {'sku': 'GIFT25', 'category': 'Gift Cards', 'qty': 1, 'unit_price': 25}],
                             {'percent_off': None, 'amount_off': 5})
        self.assertEqual((result['discount'], result['tax'], result['total']), (2.25, 0, 25))

    def test_upgrade_preserves_legacy_order_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'legacy.db')
            original = sqlite3.connect(path)
            original.executescript(SCHEMA)
            original.execute("INSERT INTO orders (id, created_at, customer_name, customer_email, pickup_date, subtotal, discount, tax, total) "
                             "VALUES (42, '2026-10-01T09:00:00', 'Existing customer', 'customer@example.com', '2026-10-10', 18, 0, 1.44, 19.44)")
            original.execute("INSERT INTO order_items VALUES (42, 'BREAD9', 'Sourdough Loaf', 2, 9, 18)")
            original.execute("INSERT INTO orders (id, created_at, customer_name, customer_email, pickup_date, subtotal, discount, tax, total) "
                             "VALUES (43, '2026-10-01T09:00:00', 'Gift customer', 'gift@example.com', '2026-10-10', 25, 0, 2, 27)")
            original.execute("INSERT INTO order_items VALUES (43, 'GIFT25', '$25 Gift Card', 1, 25, 25)")
            original.commit()
            columns = [r[1] for r in original.execute('PRAGMA table_info(orders)')]
            before = original.execute('SELECT * FROM orders').fetchall()
            original.close()
            for _ in range(2):
                db = Database(path)
                self.assertEqual([tuple(r) for r in db.query('SELECT '+','.join(columns)+' FROM orders')], before)
                self.assertEqual(len(db.order_items(42)), 1)
                self.assertIsNone(db.order(42)['pickup_time'])
                db.conn.close()
            backup = sqlite3.connect(path+'.pre-upgrade.bak')
            self.assertEqual(backup.execute('SELECT * FROM orders').fetchall(), before)
            backup.close()
            db = Database(path)
            with self.assertRaises(OrderError):
                db.cancel(42, dt.date(2026, 10, 8), token='wrong')
            self.assertTrue(db.cancel(42, dt.date(2026, 10, 8), token=db.order(42)['cancel_token']))
            self.assertTrue(db.import_gift_card(43, 'OLD-CARD', 1250))
            card = db.gift_cards(43)[0]
            self.assertEqual((card['initial_cents'], card['balance_cents'], card['active']), (2500, 1250, 1))
            with self.assertRaises(OrderError):
                db.import_gift_card(43, 'ANOTHER-CARD', 2500)
            with self.assertRaises(OrderError):
                db.cancel(43, dt.date(2026, 10, 8), admin=True)
            db.conn.close()
