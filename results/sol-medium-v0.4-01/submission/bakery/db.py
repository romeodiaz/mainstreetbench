"""SQLite storage. The database file is created and seeded on first start."""

from __future__ import annotations

import sqlite3
import threading
import secrets
from pathlib import Path
from .pricing import cents
from .pickup import DAILY_LIMITS


class OrderError(ValueError):
    pass

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    percent_off REAL,
    amount_off REAL,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL DEFAULT '',
    pickup_date TEXT NOT NULL,
    promo_code TEXT,
    subtotal REAL NOT NULL,
    discount REAL NOT NULL,
    tax REAL NOT NULL,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'placed'
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id),
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    qty INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL
);
"""

PRODUCTS = [
    ("BREAD9", "Sourdough Loaf", 9.00, "Bread", 1),
    ("BAGUETTE5", "Baguette", 5.00, "Bread", 2),
    ("BAGEL225", "Everything Bagel", 2.25, "Bread", 3),
    ("CROISSANT21", "Croissant Box (6)", 21.00, "Pastry", 4),
    ("CINNAMON325", "Cinnamon Roll", 3.25, "Pastry", 5),
    ("SCONE375", "Blueberry Scone", 3.75, "Pastry", 6),
    ("COOKIE12", "Cookie Box (12)", 12.00, "Pastry", 7),
    ("PIE32", "Seasonal Pie", 32.00, "Cakes & Pies", 8),
    ("CAKE48", "Birthday Cake", 48.00, "Cakes & Pies", 9),
    ("CATER120", "Catering Tray", 120.00, "Catering", 10),
    ("COFFEE18", "Coffee Beans 1lb", 18.00, "Pantry", 11),
    ("GIFT25", "$25 Gift Card", 25.00, "Gift Cards", 12),
]
PROMO_CODES = [
    ("WELCOME10", 10.0, None),
    ("FALL15", 15.0, None),
    ("FIVEOFF", None, 5.0),
]

_lock = threading.Lock()


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with _lock:
            existing = self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'").fetchone()
            if existing and 'pickup_time' not in {r['name'] for r in self.conn.execute('PRAGMA table_info(orders)')}:
                backup_path = Path(str(path) + '.pre-upgrade.bak')
                if not backup_path.exists():
                    backup = sqlite3.connect(str(backup_path))
                    try:
                        self.conn.backup(backup)
                    finally:
                        backup.close()
            self.conn.executescript(SCHEMA)
            if not self.conn.execute("SELECT 1 FROM products LIMIT 1").fetchone():
                self.conn.executemany(
                    "INSERT INTO products (sku, name, price, category, sort_order) VALUES (?, ?, ?, ?, ?)", PRODUCTS)
                self.conn.executemany(
                    "INSERT INTO promo_codes (code, percent_off, amount_off) VALUES (?, ?, ?)", PROMO_CODES)
            columns = {r['name'] for r in self.conn.execute('PRAGMA table_info(orders)')}
            for name, definition in {
                'pickup_time': 'TEXT', 'cancel_token': 'TEXT', 'gift_card_code': 'TEXT',
                'gift_card_applied': 'REAL NOT NULL DEFAULT 0',
                'gift_card_balance': 'REAL', 'amount_due': 'REAL'
            }.items():
                if name not in columns:
                    self.conn.execute(f'ALTER TABLE orders ADD COLUMN {name} {definition}')
            self.conn.execute('CREATE TABLE IF NOT EXISTS gift_cards ('
                              'code TEXT PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), '
                              'initial_cents INTEGER NOT NULL, balance_cents INTEGER NOT NULL, '
                              'active INTEGER NOT NULL DEFAULT 0)')
            for row in self.conn.execute('SELECT id FROM orders WHERE cancel_token IS NULL').fetchall():
                self.conn.execute('UPDATE orders SET cancel_token=? WHERE id=?', (secrets.token_urlsafe(32), row['id']))
            self.conn.commit()

    def query(self, sql: str, params=()) -> list:
        with _lock:
            return self.conn.execute(sql, params).fetchall()

    def products(self, active_only: bool = True) -> list:
        where = "WHERE active = 1" if active_only else ""
        return self.query(f"SELECT * FROM products {where} ORDER BY sort_order")

    def product(self, sku: str):
        rows = self.query("SELECT * FROM products WHERE sku = ?", (sku,))
        return rows[0] if rows else None

    def promo(self, code: str):
        rows = self.query("SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code.strip().upper(),))
        return rows[0] if rows else None

    def insert_order(self, order: dict, items: list, slots: list, requested_time=None, gift_code='') -> int:
        # Reservations, gift-card spending and order creation are one transaction.
        with _lock:
            try:
                self.conn.execute('BEGIN IMMEDIATE')
                counts = dict(self.conn.execute(
                    "SELECT pickup_time, COUNT(*) FROM orders WHERE pickup_date=? AND status='placed' GROUP BY pickup_time",
                    (order['pickup_date'],)).fetchall())
                available = [s for s in slots if counts.get(s, 0) < 4]
                if requested_time:
                    if requested_time not in slots:
                        raise OrderError('Choose an open half-hour pickup time with enough preparation time')
                    if requested_time not in available:
                        raise OrderError('That pickup time is full. Please choose another')
                    selected = requested_time
                elif available:
                    selected = available[0]
                else:
                    raise OrderError('No pickup times available. Please choose another date')
                for sku, limit in DAILY_LIMITS.items():
                    qty = sum(i['qty'] for i in items if i['sku'] == sku)
                    sold = self.conn.execute(
                        "SELECT COALESCE(SUM(i.qty), 0) FROM order_items i JOIN orders o ON o.id=i.order_id "
                        "WHERE o.pickup_date=? AND o.status='placed' AND i.sku=?",
                        (order['pickup_date'], sku)).fetchone()[0]
                    if qty and sold + qty > limit:
                        name = next(i['name'] for i in items if i['sku'] == sku)
                        raise OrderError(f'{name} is sold out for that quantity on this date ({max(0, limit-sold)} left)')
                applied = 0
                balance = None
                if gift_code:
                    card = self.conn.execute('SELECT * FROM gift_cards WHERE code=? AND active=1', (gift_code,)).fetchone()
                    if card is None or card['balance_cents'] <= 0:
                        raise OrderError('That gift card is invalid, not yet activated, or has no balance')
                    applied = min(card['balance_cents'], int(cents(order['total']) * 100))
                    balance = card['balance_cents'] - applied
                    self.conn.execute('UPDATE gift_cards SET balance_cents=? WHERE code=?', (balance, gift_code))
                order.update(pickup_time=selected, cancel_token=secrets.token_urlsafe(32),
                             gift_card_code=gift_code or None, gift_card_applied=applied / 100,
                             gift_card_balance=None if balance is None else balance / 100,
                             amount_due=float(cents(order['total']) - cents(applied / 100)))
                keys = list(order)
                cursor = self.conn.execute(
                    f"INSERT INTO orders ({', '.join(keys)}) VALUES ({', '.join('?' for _ in keys)})",
                    [order[k] for k in keys])
                order_id = cursor.lastrowid
                self.conn.executemany(
                    'INSERT INTO order_items (order_id, sku, name, qty, unit_price, line_total) VALUES (?, ?, ?, ?, ?, ?)',
                    [(order_id, i['sku'], i['name'], i['qty'], i['unit_price'], i['line_total']) for i in items])
                for item in items:
                    if item['category'] == 'Gift Cards':
                        for _ in range(item['qty']):
                            value = int(cents(item['unit_price']) * 100)
                            self.conn.execute('INSERT INTO gift_cards (code, order_id, initial_cents, balance_cents, active) VALUES (?, ?, ?, ?, 0)',
                                              ('CL-' + secrets.token_hex(12).upper(), order_id, value, value))
                self.conn.commit()
                return order_id
            except Exception:
                self.conn.rollback()
                raise

    def gift_cards(self, order_id):
        return self.query('SELECT code, initial_cents, balance_cents, active FROM gift_cards WHERE order_id=?', (order_id,))

    def import_gift_card(self, order_id, code, balance_cents):
        """Staff verifies payment and the physical card's remaining balance."""
        with _lock:
            try:
                self.conn.execute('BEGIN IMMEDIATE')
                row = self.conn.execute('SELECT status FROM orders WHERE id=?', (order_id,)).fetchone()
                if row is None:
                    self.conn.rollback()
                    return False
                if row['status'] != 'placed':
                    raise OrderError('Cannot register a gift card from a cancelled order')
                purchases = self.conn.execute(
                    "SELECT i.qty, i.unit_price FROM order_items i LEFT JOIN products p ON p.sku=i.sku "
                    "WHERE i.order_id=? AND (p.category='Gift Cards' OR i.sku LIKE 'GIFT%') ORDER BY i.rowid",
                    (order_id,)).fetchall()
                values = [int(cents(r['unit_price']) * 100) for r in purchases for _ in range(r['qty'])]
                count = self.conn.execute('SELECT COUNT(*) FROM gift_cards WHERE order_id=?', (order_id,)).fetchone()[0]
                if count >= len(values):
                    raise OrderError('All gift cards on this order already have codes, or this order contains no gift cards')
                value = values[count]
                if not 0 <= balance_cents <= value:
                    raise OrderError('Remaining balance must be between zero and the purchased card value')
                if self.conn.execute('SELECT 1 FROM gift_cards WHERE code=?', (code,)).fetchone():
                    raise OrderError('That gift card code is already registered')
                self.conn.execute('INSERT INTO gift_cards (code, order_id, initial_cents, balance_cents, active) VALUES (?, ?, ?, ?, 1)',
                                  (code, order_id, value, balance_cents))
                self.conn.commit()
                return True
            except Exception:
                self.conn.rollback()
                raise

    def activate_gift_cards(self, order_id):
        with _lock:
            try:
                self.conn.execute('BEGIN IMMEDIATE')
                row = self.conn.execute('SELECT status FROM orders WHERE id=?', (order_id,)).fetchone()
                if row is None:
                    self.conn.rollback()
                    return False
                if row['status'] != 'placed':
                    raise OrderError('Cannot activate gift cards from a cancelled order')
                self.conn.execute('UPDATE gift_cards SET active=1 WHERE order_id=?', (order_id,))
                self.conn.commit()
                return True
            except Exception:
                self.conn.rollback()
                raise

    def cancel(self, order_id, today, token=None, admin=False):
        with _lock:
            try:
                self.conn.execute('BEGIN IMMEDIATE')
                row = self.conn.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
                if row is None:
                    self.conn.rollback()
                    return False
                if not admin:
                    if not isinstance(token, str) or not secrets.compare_digest(token.encode(), row['cancel_token'].encode()):
                        raise OrderError('Use your private order link to cancel. Please call the bakery if you lost the link')
                if row['status'] == 'cancelled':
                    self.conn.commit()
                    return True
                if not admin and row['pickup_date'] <= today.isoformat():
                    raise OrderError('Orders cannot be cancelled on or after the pickup day. Please call the bakery')
                spent = self.conn.execute('SELECT 1 FROM gift_cards WHERE order_id=? AND balance_cents < initial_cents', (order_id,)).fetchone()
                if spent:
                    raise OrderError('A gift card from this order has been used. Please call the bakery to cancel')
                if row['gift_card_code'] and row['gift_card_applied']:
                    self.conn.execute('UPDATE gift_cards SET balance_cents=balance_cents+? WHERE code=?',
                                      (int(cents(row['gift_card_applied']) * 100), row['gift_card_code']))
                self.conn.execute('UPDATE gift_cards SET active=0 WHERE order_id=?', (order_id,))
                self.conn.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
                self.conn.commit()
                return True
            except Exception:
                self.conn.rollback()
                raise

    def order(self, order_id: int):
        rows = self.query("SELECT * FROM orders WHERE id = ?", (order_id,))
        return rows[0] if rows else None

    def order_items(self, order_id: int) -> list:
        return self.query("SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid", (order_id,))

    def orders(self, pickup_date: str | None = None) -> list:
        if pickup_date:
            return self.query("SELECT * FROM orders WHERE pickup_date = ? ORDER BY COALESCE(pickup_time, ''), id", (pickup_date,))
        return self.query("SELECT * FROM orders ORDER BY pickup_date, COALESCE(pickup_time, ''), id")

