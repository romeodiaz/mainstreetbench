"""Exercise upgrades on a copy; never open the live database for writing."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bakery.db import Database


class MigrationTest(unittest.TestCase):
    def test_existing_orders_survive_repeat_startup(self):
        live = Path(__file__).resolve().parents[1] / 'data' / 'bakery.db'
        with tempfile.TemporaryDirectory() as directory:
            source = sqlite3.connect(f'file:{live}?mode=ro', uri=True)
            columns = [row[1] for row in source.execute('PRAGMA table_info(orders)')]
            old_orders = source.execute('SELECT * FROM orders ORDER BY id').fetchall()
            old_items = source.execute('SELECT * FROM order_items ORDER BY rowid').fetchall()
            path = directory + '/copy.db'
            copy = sqlite3.connect(path)
            source.backup(copy)
            source.close()
            copy.close()
            db = Database(path)
            self.assertEqual([tuple(row) for row in db.query(
                'SELECT ' + ', '.join(columns) + ' FROM orders ORDER BY id')], old_orders)
            self.assertEqual([tuple(row) for row in db.query('SELECT * FROM order_items ORDER BY rowid')], old_items)
            cards = [tuple(row) for row in db.query('SELECT * FROM gift_cards')]
            db.conn.close()
            db = Database(path)
            self.assertEqual([tuple(row) for row in db.query('SELECT * FROM gift_cards')], cards)
            self.assertEqual(db.query('PRAGMA integrity_check')[0][0], 'ok')
            db.conn.close()
