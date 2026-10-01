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
    sort_order INTEGER NOT NULL DEFAULT 0,
    daily_limit INTEGER
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
    status TEXT NOT NULL DEFAULT 'placed',
    pickup_slot TEXT
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
DEFAULT_DAILY_LIMITS = {"CAKE48": 6, "CATER120": 4, "PIE32": 8}
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
            self.conn.executescript(SCHEMA)
            self._migrate()
            if not self.conn.execute("SELECT 1 FROM products LIMIT 1").fetchone():
                self.conn.executemany(
                    "INSERT INTO products (sku, name, price, category, sort_order) VALUES (?, ?, ?, ?, ?)", PRODUCTS)
                self.conn.executemany(
                    "INSERT INTO promo_codes (code, percent_off, amount_off) VALUES (?, ?, ?)", PROMO_CODES)
                self._default_limits()
            self.conn.commit()

    def _columns(self, table: str) -> set:
        return {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")}

    def _default_limits(self) -> None:
        self.conn.executemany("UPDATE products SET daily_limit = ? WHERE sku = ?",
                              [(limit, sku) for sku, limit in DEFAULT_DAILY_LIMITS.items()])

    def _migrate(self) -> None:
        """Bring databases created by earlier versions up to date without losing orders."""
        if "pickup_slot" not in self._columns("orders"):
            self.conn.execute("ALTER TABLE orders ADD COLUMN pickup_slot TEXT")
        if "daily_limit" not in self._columns("products"):
            self.conn.execute("ALTER TABLE products ADD COLUMN daily_limit INTEGER")
            self._default_limits()

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

    def insert_order(self, order: dict, items: list, check=None) -> int:
        """Insert an order. `check(db)` runs under the same lock first, so capacity
        and stock checks can't race with another order; it raises to reject."""
        with _lock:
            if check is not None:
                check(self)
            cursor = self.conn.execute(
                "INSERT INTO orders (created_at, customer_name, customer_email, customer_phone, pickup_date, "
                "pickup_slot, promo_code, subtotal, discount, tax, total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (order["created_at"], order["customer_name"], order["customer_email"], order["customer_phone"],
                 order["pickup_date"], order["pickup_slot"], order["promo_code"], order["subtotal"],
                 order["discount"], order["tax"], order["total"]))
            order_id = cursor.lastrowid
            self.conn.executemany(
                "INSERT INTO order_items (order_id, sku, name, qty, unit_price, line_total) VALUES (?, ?, ?, ?, ?, ?)",
                [(order_id, i["sku"], i["name"], i["qty"], i["unit_price"], i["line_total"]) for i in items])
            self.conn.commit()
            return order_id

    def order(self, order_id: int):
        rows = self.query("SELECT * FROM orders WHERE id = ?", (order_id,))
        return rows[0] if rows else None

    def order_items(self, order_id: int) -> list:
        return self.query("SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid", (order_id,))

    def orders(self, pickup_date: str | None = None) -> list:
        # Orders without a pickup time (placed before times existed) sort first.
        order_by = "ORDER BY pickup_date, pickup_slot IS NOT NULL, pickup_slot, id"
        if pickup_date:
            return self.query(f"SELECT * FROM orders WHERE pickup_date = ? {order_by}", (pickup_date,))
        return self.query(f"SELECT * FROM orders {order_by}")

    # Unlocked readers for use inside insert_order's check, which already holds the lock.
    def slot_usage(self, pickup_date: str) -> dict:
        rows = self.conn.execute(
            "SELECT pickup_slot, COUNT(*) AS n FROM orders WHERE pickup_date = ? AND status != 'cancelled' "
            "AND pickup_slot IS NOT NULL GROUP BY pickup_slot", (pickup_date,)).fetchall()
        return {row["pickup_slot"]: row["n"] for row in rows}

    def product_usage(self, pickup_date: str) -> dict:
        rows = self.conn.execute(
            "SELECT i.sku, SUM(i.qty) AS n FROM order_items i JOIN orders o ON o.id = i.order_id "
            "WHERE o.pickup_date = ? AND o.status != 'cancelled' GROUP BY i.sku", (pickup_date,)).fetchall()
        return {row["sku"]: row["n"] for row in rows}

    def daily_limits(self) -> dict:
        return {row["sku"]: row["daily_limit"] for row in self.conn.execute("SELECT sku, daily_limit FROM products")}

    def locked(self, reader, *args):
        with _lock:
            return reader(*args)

    def set_daily_limit(self, sku: str, limit) -> None:
        with _lock:
            self.conn.execute("UPDATE products SET daily_limit = ? WHERE sku = ?", (limit, sku))
            self.conn.commit()

    def set_status(self, order_id: int, status: str) -> None:
        with _lock:
            self.conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            self.conn.commit()
