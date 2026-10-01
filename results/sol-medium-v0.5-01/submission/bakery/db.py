"""SQLite storage. The database file is created and seeded on first start."""

from __future__ import annotations

import sqlite3
import threading
import secrets
from contextlib import contextmanager

from .pricing import cents

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

_lock = threading.RLock()


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with _lock:
            self.conn.executescript(SCHEMA)
            if not self.conn.execute("SELECT 1 FROM products LIMIT 1").fetchone():
                self.conn.executemany(
                    "INSERT INTO products (sku, name, price, category, sort_order) VALUES (?, ?, ?, ?, ?)", PRODUCTS)
                self.conn.executemany(
                    "INSERT INTO promo_codes (code, percent_off, amount_off) VALUES (?, ?, ?)", PROMO_CODES)
            columns = {r[1] for r in self.conn.execute("PRAGMA table_info(orders)")}
            for name, definition in {
                "pickup_time": "TEXT", "cancel_token": "TEXT", "gift_card_code": "TEXT",
                "gift_card_applied": "REAL NOT NULL DEFAULT 0", "gift_card_balance": "REAL",
                "amount_due": "REAL"
            }.items():
                if name not in columns:
                    self.conn.execute(f"ALTER TABLE orders ADD COLUMN {name} {definition}")
            self.conn.execute("""CREATE TABLE IF NOT EXISTS gift_cards (
                code TEXT PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
                initial_cents INTEGER NOT NULL, balance_cents INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1)""")
            for row in self.conn.execute("SELECT id FROM orders WHERE cancel_token IS NULL").fetchall():
                self.conn.execute("UPDATE orders SET cancel_token = ?, amount_due = total WHERE id = ?",
                                  (secrets.token_urlsafe(24), row['id']))
            # Existing gift-card purchases receive codes without changing historical totals.
            legacy_cards = self.conn.execute("""SELECT o.id, i.qty, i.unit_price
                FROM orders o JOIN order_items i ON i.order_id=o.id
                WHERE o.status='placed' AND i.sku LIKE 'GIFT%'
                AND NOT EXISTS (SELECT 1 FROM gift_cards g WHERE g.order_id=o.id)""").fetchall()
            for row in legacy_cards:
                for _ in range(row['qty']):
                    self.issue_card(row['id'], int(cents(row['unit_price']) * 100))
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

    def insert_order(self, order: dict, items: list) -> int:
        with _lock:
            cursor = self.conn.execute(
                "INSERT INTO orders (created_at, customer_name, customer_email, customer_phone, pickup_date, "
                "promo_code, subtotal, discount, tax, total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (order["created_at"], order["customer_name"], order["customer_email"], order["customer_phone"],
                 order["pickup_date"], order["promo_code"], order["subtotal"], order["discount"],
                 order["tax"], order["total"]))
            order_id = cursor.lastrowid
            self.conn.executemany(
                "INSERT INTO order_items (order_id, sku, name, qty, unit_price, line_total) VALUES (?, ?, ?, ?, ?, ?)",
                [(order_id, i["sku"], i["name"], i["qty"], i["unit_price"], i["line_total"]) for i in items])
            self.conn.execute("""UPDATE orders SET pickup_time=?, cancel_token=?, gift_card_code=?,
                gift_card_applied=?, gift_card_balance=?, amount_due=? WHERE id=?""",
                (order['pickup_time'], secrets.token_urlsafe(24), order['gift_card_code'],
                 order['gift_card_applied'], order['gift_card_balance'], order['amount_due'], order_id))
            return order_id

    def order(self, order_id: int):
        rows = self.query("SELECT * FROM orders WHERE id = ?", (order_id,))
        return rows[0] if rows else None

    def order_items(self, order_id: int) -> list:
        return self.query("SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid", (order_id,))

    def orders(self, pickup_date: str | None = None) -> list:
        if pickup_date:
            return self.query("SELECT * FROM orders WHERE pickup_date = ? ORDER BY pickup_time, id", (pickup_date,))
        return self.query("SELECT * FROM orders ORDER BY pickup_date, pickup_time, id")

    def set_status(self, order_id: int, status: str) -> None:
        with _lock:
            self.conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

    @contextmanager
    def atomic(self):
        with _lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                yield
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def issue_card(self, order_id, value):
        code = secrets.token_hex(8).upper()
        self.conn.execute("INSERT INTO gift_cards (code, order_id, initial_cents, balance_cents) VALUES (?, ?, ?, ?)",
                          (code, order_id, value, value))
        return code

    def card(self, code):
        rows = self.query("SELECT * FROM gift_cards WHERE code=? AND active=1", (code,))
        return rows[0] if rows else None

    def cards(self, order_id):
        return self.query("SELECT * FROM gift_cards WHERE order_id=?", (order_id,))

    def reserved(self, date, sku):
        return self.query("""SELECT COALESCE(SUM(i.qty),0) AS n FROM order_items i
            JOIN orders o ON o.id=i.order_id WHERE o.pickup_date=? AND o.status='placed' AND i.sku=?""",
            (date, sku))[0]['n']

    def slot_count(self, date, time):
        return self.query("SELECT COUNT(*) AS n FROM orders WHERE pickup_date=? AND pickup_time=? AND status='placed'",
                          (date, time))[0]['n']
