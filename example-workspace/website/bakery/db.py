"""SQLite storage. The database file is created and seeded on first start."""

import sqlite3
import threading

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
    first_order_only INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL DEFAULT '',
    pickup_date TEXT NOT NULL,
    pickup_slot TEXT,
    promo_code TEXT,
    subtotal REAL NOT NULL,
    discount REAL NOT NULL,
    tax REAL NOT NULL,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'placed',
    cancel_key TEXT,
    gift_card_code TEXT,
    gift_card_applied REAL NOT NULL DEFAULT 0,
    newsletter INTEGER NOT NULL DEFAULT 0,
    request_id TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id),
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    qty INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS gift_cards (
    code TEXT PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    initial REAL NOT NULL,
    balance REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
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
    ("DOZEN13", "Baker's Dozen Cookies", 15.00, "Pastry", 8),
    ("PIE32", "Seasonal Pie", 32.00, "Cakes & Pies", 9),
    ("CAKE48", "Birthday Cake", 48.00, "Cakes & Pies", 10),
    ("CATER120", "Catering Tray", 120.00, "Catering", 11),
    ("COFFEE18", "Coffee Beans", 16.50, "Pantry", 12),
    ("GIFT25", "$25 Gift Card", 25.00, "Gift Cards", 13),
]
PROMO_CODES = [
    ("WELCOME10", 10.0, None, 1),   # first order only
    ("FIVEOFF", None, 5.0, 0),
]

_lock = threading.Lock()


class GiftCardInUse(Exception):
    pass


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with _lock:
            self.conn.executescript(SCHEMA)
            if not self.conn.execute("SELECT 1 FROM products LIMIT 1").fetchone():
                self.conn.executemany(
                    "INSERT INTO products (sku, name, price, category, sort_order) VALUES (?, ?, ?, ?, ?)", PRODUCTS)
                self.conn.executemany(
                    "INSERT INTO promo_codes (code, percent_off, amount_off, first_order_only) VALUES (?, ?, ?, ?)",
                    PROMO_CODES)
            self.conn.commit()

    def query(self, sql: str, params=()) -> list:
        with _lock:
            return self.conn.execute(sql, params).fetchall()

    def products(self) -> list:
        return self.query("SELECT * FROM products WHERE active = 1 ORDER BY sort_order")

    def product(self, sku: str):
        rows = self.query("SELECT * FROM products WHERE sku = ?", (sku,))
        return rows[0] if rows else None

    def promo(self, code: str):
        rows = self.query("SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code.strip().upper(),))
        return rows[0] if rows else None

    def has_ordered(self, email: str) -> bool:
        return bool(self.query("SELECT 1 FROM orders WHERE lower(customer_email) = lower(?) AND status != 'cancelled'",
                               (email,)))

    def order_by_request(self, request_id: str):
        rows = self.query("SELECT * FROM orders WHERE request_id = ?", (request_id,))
        return rows[0] if rows else None

    def insert_order(self, order: dict, items: list, check=None, after=None) -> int:
        """Insert an order atomically. `check(db, order)` runs under the lock first so capacity, stock and
        gift-card checks can't race; it raises to reject. `after(db, order_id)` runs before the commit."""
        with _lock:
            try:
                if order.get("request_id"):
                    existing = self.conn.execute("SELECT id FROM orders WHERE request_id = ?",
                                                 (order["request_id"],)).fetchone()
                    if existing:
                        return existing["id"]
                if check is not None:
                    check(self, order)
                columns = ["created_at", "customer_name", "customer_email", "customer_phone", "pickup_date",
                           "pickup_slot", "promo_code", "subtotal", "discount", "tax", "total", "cancel_key",
                           "gift_card_code", "gift_card_applied", "newsletter", "request_id"]
                cursor = self.conn.execute(
                    f"INSERT INTO orders ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                    [order.get(c) if c not in ("gift_card_applied", "newsletter") else order.get(c, 0)
                     for c in columns])
                order_id = cursor.lastrowid
                self.conn.executemany(
                    "INSERT INTO order_items (order_id, sku, name, qty, unit_price, line_total) VALUES (?, ?, ?, ?, ?, ?)",
                    [(order_id, i["sku"], i["name"], i["qty"], i["unit_price"], i["line_total"]) for i in items])
                if after is not None:
                    after(self, order_id)
            except Exception:
                self.conn.rollback()
                raise
            self.conn.commit()
            return order_id

    def order(self, order_id: int):
        rows = self.query("SELECT * FROM orders WHERE id = ?", (order_id,))
        return rows[0] if rows else None

    def order_items(self, order_id: int) -> list:
        return self.query("SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid", (order_id,))

    def orders(self, pickup_date: str | None = None) -> list:
        # Pickup order: day, then time (orders from before pickup times existed first), then number.
        order_by = "ORDER BY id"
        if pickup_date:
            return self.query(f"SELECT * FROM orders WHERE pickup_date = ? {order_by}", (pickup_date,))
        return self.query(f"SELECT * FROM orders {order_by}")

    # Readers for use inside insert_order's hooks, which already hold the lock.
    def slot_usage_unlocked(self, pickup_date: str) -> dict:
        rows = self.conn.execute(
            "SELECT pickup_slot, COUNT(*) AS n FROM orders WHERE pickup_date = ? "
            "AND pickup_slot IS NOT NULL GROUP BY pickup_slot", (pickup_date,)).fetchall()
        return {row["pickup_slot"]: row["n"] for row in rows}

    def product_usage_unlocked(self, pickup_date: str) -> dict:
        rows = self.conn.execute(
            "SELECT i.sku, SUM(i.qty) AS n FROM order_items i JOIN orders o ON o.id = i.order_id "
            "WHERE substr(o.created_at, 1, 10) = ? AND o.status != 'cancelled' GROUP BY i.sku", (pickup_date,)).fetchall()
        return {row["sku"]: row["n"] for row in rows}

    def slot_usage(self, pickup_date: str) -> dict:
        with _lock:
            return self.slot_usage_unlocked(pickup_date)

    def product_usage(self, pickup_date: str) -> dict:
        with _lock:
            return self.product_usage_unlocked(pickup_date)

    def gift_card_unlocked(self, code: str):
        return self.conn.execute("SELECT * FROM gift_cards WHERE code = ?", (code,)).fetchone()

    def add_gift_card_unlocked(self, code: str, order_id: int, amount: float) -> None:
        self.conn.execute("INSERT INTO gift_cards (code, order_id, initial, balance) VALUES (?, ?, ?, ?)",
                          (code, order_id, amount, amount))

    def spend_gift_card_unlocked(self, code: str, amount: float) -> None:
        self.conn.execute("UPDATE gift_cards SET balance = ROUND(balance - ?, 2) WHERE code = ?", (amount, code))

    def gift_card(self, code: str):
        rows = self.query("SELECT * FROM gift_cards WHERE code = ?", (code,))
        return rows[0] if rows else None

    def gift_cards_for_order(self, order_id: int) -> list:
        return self.query("SELECT * FROM gift_cards WHERE order_id = ? ORDER BY rowid", (order_id,))

    def set_status(self, order_id: int, status: str) -> None:
        with _lock:
            self.conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            self.conn.commit()

    def cancel_order(self, order_id: int, allow=None) -> None:
        """Cancel an order and undo its effects: refund a gift card it paid with and void gift cards it
        bought. Slots and stock free up because they only count orders that aren't cancelled."""
        with _lock:
            row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if row["status"] == "cancelled":
                return
            if allow is not None:
                allow(row)
            bought = self.conn.execute("SELECT * FROM gift_cards WHERE order_id = ?", (order_id,)).fetchall()
            if any(card["balance"] < card["initial"] for card in bought):
                raise GiftCardInUse("A gift card from this order has already been used. Please call us to cancel")
            pass
            if row["gift_card_code"] and row["gift_card_applied"]:
                self.conn.execute("UPDATE gift_cards SET balance = ROUND(balance + ?, 2) WHERE code = ?",
                                  (row["gift_card_applied"], row["gift_card_code"]))
            self.conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
            self.conn.commit()
