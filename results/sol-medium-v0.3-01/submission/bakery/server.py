"""HTTP server for the ordering site.

Run: python3 -m bakery.server --port 8000 --db data/bakery.db
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, urlparse

from . import clock
from .db import Database, CapacityError
from .pricing import price_order

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_QTY = 50


class ValidationError(Exception):
    pass


SLOTS = tuple(f'{hour:02d}:{minute:02d}' for hour in range(7, 15) for minute in (0, 30))


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValidationError('Please choose a valid pickup date (YYYY-MM-DD)')
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise ValidationError('Please choose a valid pickup date (YYYY-MM-DD)') from None


def slots_json(db, date):
    pickup = parse_date(date)
    opened = pickup.weekday() != 0
    counts = db.slot_counts(date)
    now = clock.now()
    slots = []
    if opened:
        for slot in SLOTS:
            remaining = max(0, 4 - counts.get(slot, 0))
            start = dt.datetime.combine(pickup, dt.time.fromisoformat(slot))
            slots.append({'time': slot, 'remaining': remaining,
                          'available': remaining > 0 and start - now >= dt.timedelta(hours=2)})
    return {'date': date, 'open': opened, 'slots': slots}


def render(template: str, **values) -> str:
    body = Template((TEMPLATES / template).read_text(encoding="utf-8")).substitute(**values)
    return Template((TEMPLATES / "layout.html").read_text(encoding="utf-8")).substitute(
        title=values.get("title", "Corner Loaf Bakery"), body=body)


def money(value: float) -> str:
    return f"${value:,.2f}"


def order_json(db: Database, row) -> dict:
    items = [{"sku": i["sku"], "name": i["name"], "qty": i["qty"], "unit_price": i["unit_price"],
              "line_total": i["line_total"]} for i in db.order_items(row["id"])]
    return {
        "id": row["id"], "status": row["status"], "created_at": row["created_at"],
        "customer": {"name": row["customer_name"], "email": row["customer_email"], "phone": row["customer_phone"]},
        "pickup_date": row["pickup_date"], "pickup_slot": row["pickup_slot"], "items": items, "promo_code": row["promo_code"],
        "subtotal": row["subtotal"], "discount": row["discount"], "tax": row["tax"], "total": row["total"],
    }


def create_order(db: Database, payload: dict) -> int:
    if not isinstance(payload, dict):
        raise ValidationError("Order must be a JSON object")
    customer = payload.get("customer") or {}
    if not isinstance(customer, dict):
        raise ValidationError("Customer must be a JSON object")
    name = str(customer.get("name", "")).strip()
    email = str(customer.get("email", "")).strip()
    phone = str(customer.get("phone", "")).strip()
    if not name:
        raise ValidationError("Please enter your name")
    if not EMAIL.match(email):
        raise ValidationError("Please enter a valid email address")
    pickup = parse_date(payload.get('pickup_date'))
    if pickup.weekday() == 0:
        raise ValidationError('We are closed on Mondays')
    slot = payload.get('pickup_slot')
    if not isinstance(slot, str) or slot not in SLOTS:
        raise ValidationError('Please choose a half-hour pickup time from 07:00 to 14:30')
    start = dt.datetime.combine(pickup, dt.time.fromisoformat(slot))

    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("Your cart is empty")
    lines = []
    for raw in raw_items:
        product = db.product(str(raw.get("sku", ""))) if isinstance(raw, dict) else None
        if product is None or not product["active"]:
            raise ValidationError("One of the items is no longer available")
        qty = raw.get("qty")
        if not isinstance(qty, int) or isinstance(qty, bool) or not 1 <= qty <= MAX_QTY:
            raise ValidationError(f"Quantity for {product['name']} must be between 1 and {MAX_QTY}")
        lines.append({"sku": product["sku"], "name": product["name"], "qty": qty,
                      "category": product["category"], "unit_price": product["price"], "line_total": round(qty * product["price"], 2)})

    notice = 48 if any(line['sku'] in ('CAKE48', 'CATER120') for line in lines) else 2
    if start - clock.now() < dt.timedelta(hours=notice):
        raise ValidationError(f'This order needs at least {notice} hours of notice')

    code = str(payload.get("promo_code") or "").strip().upper()
    promo = db.promo(code) if code else None
    if code and promo is None:
        raise ValidationError("That promo code isn't valid")
    totals = price_order(lines, promo)
    return db.insert_order({
        "created_at": clock.now().isoformat(), "customer_name": name, "customer_email": email,
        "customer_phone": phone, "pickup_date": pickup.isoformat(), "pickup_slot": slot, "promo_code": code or None, **totals,
    }, lines)


class Handler(BaseHTTPRequestHandler):
    server_version = "CornerLoaf/1.0"
    db: Database = None
    admin_password = "flour"

    # --- plumbing -------------------------------------------------------------------------------
    def log_message(self, format, *args):
        if os.environ.get("CORNERLOAF_LOG"):
            super().log_message(format, *args)

    def send(self, status: int, body: bytes, content_type: str, headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, data) -> None:
        self.send(status, json.dumps(data).encode(), "application/json")

    def send_html(self, status: int, text: str) -> None:
        self.send(status, text.encode(), "text/html; charset=utf-8")

    def not_found(self) -> None:
        if self.path.startswith("/api/") or self.path.startswith("/admin/api/"):
            self.send_json(404, {"error": "Not found"})
        else:
            self.send_html(404, render("message.html", title="Not found", message="We couldn't find that page."))

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(length) or b"null")
        except json.JSONDecodeError:
            raise ValidationError("Request body must be JSON") from None

    def is_admin(self) -> bool:
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            _, _, password = base64.b64decode(header[6:]).decode().partition(":")
        except ValueError:
            return False
        return password == self.admin_password

    def require_admin(self) -> bool:
        if self.is_admin():
            return True
        self.send(401, b"Admin login required", "text/plain",
                  {"WWW-Authenticate": 'Basic realm="Corner Loaf admin"'})
        return False

    # --- routing --------------------------------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
        path = url.path
        if path == "/":
            try:
                return self.menu_page(query.get('date'))
            except ValidationError as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == "/checkout":
            return self.send_html(200, render("checkout.html", title="Checkout"))
        if match := re.fullmatch(r"/order/(\d+)", path):
            return self.confirmation_page(int(match[1]))
        if path in ('/api/menu', '/api/slots'):
            try:
                if path == '/api/slots':
                    return self.send_json(200, slots_json(self.db, query.get('date')))
                date = query.get('date')
                if date is not None:
                    parse_date(date)
                return self.send_json(200, {'products': self.db.menu(date)})
            except ValidationError as exc:
                return self.send_json(400, {'error': str(exc)})
        if match := re.fullmatch(r"/api/orders/(\d+)", path):
            row = self.db.order(int(match[1]))
            return self.send_json(200, order_json(self.db, row)) if row else self.not_found()
        if path == "/admin":
            return self.require_admin() and self.admin_page(query.get("date"))
        if path == "/admin/api/orders":
            if self.require_admin():
                self.send_json(200, {"orders": [order_json(self.db, r) for r in self.db.orders(query.get("date"))]})
            return
        if path.startswith("/static/"):
            return self.static(path[len("/static/"):])
        self.not_found()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/orders":
                order_id = create_order(self.db, self.read_json())
                return self.send_json(201, order_json(self.db, self.db.order(order_id)))
            if match := re.fullmatch(r"/admin/api/orders/(\d+)/cancel", path):
                if not self.require_admin():
                    return
                row = self.db.order(int(match[1]))
                if row is None:
                    return self.not_found()
                self.db.set_status(row["id"], "cancelled")
                return self.send_json(200, order_json(self.db, self.db.order(row["id"])))
        except CapacityError as exc:
            return self.send_json(409, {'error': str(exc), **exc.details})
        except ValidationError as exc:
            return self.send_json(400, {"error": str(exc)})
        self.not_found()

    def do_PUT(self):
        path = urlparse(self.path).path
        if match := re.fullmatch(r'/admin/api/products/([^/]+)', path):
            if not self.require_admin():
                return
            product = self.db.product(match[1])
            if product is None:
                return self.not_found()
            try:
                payload = self.read_json()
                if not isinstance(payload, dict) or 'daily_limit' not in payload:
                    raise ValidationError('Please provide daily_limit')
                limit = payload['daily_limit']
                if limit is not None and (type(limit) is not int or limit < 0):
                    raise ValidationError('Daily limit must be a nonnegative whole number or null')
                self.db.set_limit(product['sku'], limit)
                updated = self.db.product(product['sku'])
                return self.send_json(200, {k: updated[k] for k in
                                           ('sku', 'name', 'price', 'category', 'daily_limit')})
            except ValidationError as exc:
                return self.send_json(400, {'error': str(exc)})
        self.not_found()

    # --- pages ----------------------------------------------------------------------------------
    def menu_page(self, date=None):
        if date is not None:
            parse_date(date)
        sections, current = [], None
        for product in self.db.menu(date):
            if product["category"] != current:
                if current is not None:
                    sections.append("</ul></section>")
                current = product["category"]
                sections.append(f"<section><h2>{html.escape(current)}</h2><ul class=\"menu\">")
            sold_out = product.get('sold_out', False)
            sold_attr = ' data-sold-out="true"' if sold_out else ''
            disabled = ' disabled' if sold_out else ''
            label = 'Sold out' if sold_out else 'Add'
            sections.append(
                f"<li class=\"item\" data-sku=\"{product['sku']}\"{sold_attr}>"
                f"<span class=\"name\">{html.escape(product['name'])}</span>"
                f"<span class=\"price\">{money(product['price'])}</span>"
                f"<button type=\"button\" class=\"add\" data-sku=\"{product['sku']}\" "
                f"data-name=\"{html.escape(product['name'])}\" data-price=\"{product['price']}\"{disabled}>{label}</button></li>")
        if current is not None:
            sections.append("</ul></section>")
        self.send_html(200, render("menu.html", title="Order online", menu="\n".join(sections), date=html.escape(date or "")))

    def confirmation_page(self, order_id: int):
        row = self.db.order(order_id)
        if row is None:
            return self.not_found()
        order = order_json(self.db, row)
        items = "\n".join(f"<tr><td>{i['qty']} × {html.escape(i['name'])}</td><td>{money(i['line_total'])}</td></tr>"
                          for i in order["items"])
        self.send_html(200, render(
            "confirmation.html", title=f"Order #{order_id}", order_id=order_id,
            name=html.escape(order["customer"]["name"]), pickup_date=order["pickup_date"], pickup_slot=order["pickup_slot"] or "Time not assigned", items=items,
            subtotal=money(order["subtotal"]), discount=money(order["discount"]), tax=money(order["tax"]),
            total=money(order["total"]), status=order["status"]))

    def admin_page(self, pickup_date: str | None):
        rows = []
        for row in self.db.orders(pickup_date):
            order = order_json(self.db, row)
            items = ", ".join(f"{i['qty']} × {html.escape(i['name'])}" for i in order["items"])
            rows.append(
                f"<tr data-order-id=\"{order['id']}\" class=\"{order['status']}\"><td>#{order['id']}</td>"
                f"<td>{order['pickup_date']}<br>{order['pickup_slot'] or 'Time not assigned'}</td><td>{html.escape(order['customer']['name'])}<br>"
                f"<small>{html.escape(order['customer']['phone'])}</small></td><td>{items}</td>"
                f"<td>{money(order['total'])}</td><td>{order['status']}</td></tr>")
        self.send_html(200, render("admin.html", title="Orders", date=html.escape(pickup_date or ""),
                                   rows="\n".join(rows) or "<tr><td colspan=\"6\">No orders</td></tr>",
                                   products=json.dumps(self.db.menu()).replace("<", "\\u003c")))

    def static(self, name: str):
        target = (STATIC / name).resolve()
        if STATIC not in target.parents or not target.is_file():
            return self.not_found()
        types = {".css": "text/css", ".js": "application/javascript"}
        self.send(200, target.read_bytes(), types.get(target.suffix, "application/octet-stream"))


def make_server(port: int, db_path: str, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    handler = type("BoundHandler", (Handler,), {
        "db": Database(db_path), "admin_password": os.environ.get("ADMIN_PASSWORD", "flour")})
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Corner Loaf Bakery ordering site")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--db", default="data/bakery.db")
    args = parser.parse_args()
    server = make_server(args.port, args.db, args.host)
    print(f"Corner Loaf ordering site on http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
