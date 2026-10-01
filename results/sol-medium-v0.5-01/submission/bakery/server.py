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
from .db import Database
from .pricing import price_order, cents

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_QTY = 50
DAILY_LIMITS = {"CAKE48": 6, "CATER120": 4, "PIE32": 8}
SLOTS = [f"{h:02d}:{m:02d}" for h in range(7, 15) for m in (0, 30)]


class ValidationError(Exception):
    pass


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
        "pickup_date": row["pickup_date"], "pickup_time": row["pickup_time"], "items": items,
        "cancel_token": row["cancel_token"],
        "gift_card_code": row["gift_card_code"], "gift_card_applied": row["gift_card_applied"],
        "gift_card_balance": row["gift_card_balance"], "amount_due": row["amount_due"],
        "gift_cards": [{"code": c["code"], "balance": c["balance_cents"] / 100,
                        "active": bool(c["active"])} for c in db.cards(row["id"])], "promo_code": row["promo_code"],
        "subtotal": row["subtotal"], "discount": row["discount"], "tax": row["tax"], "total": row["total"],
    }


def prepare_order(db: Database, payload: dict, preview=False):
    if not isinstance(payload, dict):
        raise ValidationError("Order must be a JSON object")
    customer = payload.get("customer") or {}
    if not isinstance(customer, dict):
        raise ValidationError("Please enter customer details")
    name = str(customer.get("name", "")).strip()
    email = str(customer.get("email", "")).strip()
    phone = str(customer.get("phone", "")).strip()
    if not name and not preview:
        raise ValidationError("Please enter your name")
    if not EMAIL.match(email) and not preview:
        raise ValidationError("Please enter a valid email address")
    try:
        pickup = dt.date.fromisoformat(str(payload.get("pickup_date", "")))
    except ValueError:
        raise ValidationError("Please choose a pickup date") from None
    if pickup < clock.today():
        raise ValidationError("Pickup date is in the past")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("Your cart is empty")
    lines_by_sku = {}
    for raw in raw_items:
        product = db.product(str(raw.get("sku", ""))) if isinstance(raw, dict) else None
        if product is None or not product["active"]:
            raise ValidationError("One of the items is no longer available")
        qty = raw.get("qty")
        if not isinstance(qty, int) or isinstance(qty, bool) or not 1 <= qty <= MAX_QTY:
            raise ValidationError(f"Quantity for {product['name']} must be between 1 and {MAX_QTY}")
        if product['sku'] in lines_by_sku:
            qty += lines_by_sku[product['sku']]['qty']
        if qty > MAX_QTY:
            raise ValidationError(f"Quantity for {product['name']} must be between 1 and {MAX_QTY}")
        lines_by_sku[product['sku']] = {"sku": product["sku"], "name": product["name"], "qty": qty,
            "category": product['category'], "unit_price": product["price"],
            "line_total": float(cents(qty * cents(product['price'])))}
    lines = list(lines_by_sku.values())
    available = pickup_slots(db, pickup, lines)
    requested = payload.get('pickup_time')
    if requested is None:  # Older API clients are assigned the first available time.
        requested = next((slot['time'] for slot in available if slot['available']), None)
    if not any(slot['time'] == requested and slot['available'] for slot in available):
        raise ValidationError("Please choose an available pickup time; allow 2 hours, or 48 hours for cakes and catering")
    for line in lines:
        limit = DAILY_LIMITS.get(line['sku'])
        if limit and db.reserved(pickup.isoformat(), line['sku']) + line['qty'] > limit:
            raise ValidationError(f"{line['name']} is sold out or has too few left for that day")

    code = str(payload.get("promo_code") or "").strip().upper()
    promo = db.promo(code) if code else None
    if code and promo is None:
        raise ValidationError("That promo code isn't valid")
    totals = price_order(lines, promo)
    gift_code = str(payload.get('gift_card_code') or '').strip().upper()
    card = db.card(gift_code) if gift_code else None
    if gift_code and (card is None or card['balance_cents'] <= 0):
        raise ValidationError("That gift card isn't valid or has no balance left")
    applied = min(card['balance_cents'], int(cents(totals['total']) * 100)) if card else 0
    return {
        "created_at": clock.now().isoformat(), "customer_name": name, "customer_email": email,
        "customer_phone": phone, "pickup_date": pickup.isoformat(), "pickup_time": requested,
        "promo_code": code or None, **totals, "gift_card_code": gift_code or None,
        "gift_card_applied": applied / 100,
        "gift_card_balance": (card['balance_cents'] - applied) / 100 if card else None,
        "amount_due": float(cents(totals['total']) - cents(applied / 100)),
    }, lines


def pickup_slots(db, pickup, lines):
    hours = 48 if any(l['sku'] in ('CAKE48', 'CATER120') for l in lines) else 2
    earliest = clock.now() + dt.timedelta(hours=hours)
    return [{"time": time, "available": pickup.weekday() != 0
             and dt.datetime.fromisoformat(f"{pickup.isoformat()}T{time}") >= earliest
             and db.slot_count(pickup.isoformat(), time) < 4} for time in SLOTS]


def create_order(db, payload):
    with db.atomic():
        order, lines = prepare_order(db, payload)
        order_id = db.insert_order(order, lines)
        if order['gift_card_code']:
            db.conn.execute("UPDATE gift_cards SET balance_cents=balance_cents-? WHERE code=?",
                            (int(cents(order['gift_card_applied']) * 100), order['gift_card_code']))
        for line in lines:
            if line['category'] == 'Gift Cards':
                for _ in range(line['qty']):
                    db.issue_card(order_id, int(cents(line['unit_price']) * 100))
        return order_id


def cancel_order(db, order_id, token=None, admin=False):
    with db.atomic():
        row = db.order(order_id)
        if row is None:
            return None
        if not admin and token != row['cancel_token']:
            raise ValidationError("Please use the cancellation link on your order page")
        if row['status'] == 'cancelled':
            return row
        if not admin and row['pickup_date'] <= clock.today().isoformat():
            raise ValidationError("Orders cannot be cancelled on or after pickup day. Please call the bakery.")
        if any(c['balance_cents'] != c['initial_cents'] for c in db.cards(order_id)):
            raise ValidationError("A gift card from this order has been spent. Please call the bakery to cancel.")
        db.conn.execute("UPDATE gift_cards SET active=0 WHERE order_id=?", (order_id,))
        if row['gift_card_code']:
            db.conn.execute("UPDATE gift_cards SET balance_cents=balance_cents+? WHERE code=?",
                            (int(cents(row['gift_card_applied']) * 100), row['gift_card_code']))
        db.set_status(order_id, 'cancelled')
        return db.order(order_id)


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
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        path = url.path
        if path == "/":
            return self.menu_page()
        if path == "/checkout":
            return self.send_html(200, render("checkout.html", title="Checkout"))
        if match := re.fullmatch(r"/order/(\d+)", path):
            return self.confirmation_page(int(match[1]))
        if path == "/api/pickup-slots":
            try:
                pickup = dt.date.fromisoformat(query.get('date', ''))
                lines = [{'sku': sku} for sku in query.get('skus', '').split(',')]
                return self.send_json(200, {'slots': pickup_slots(self.db, pickup, lines)})
            except ValueError:
                return self.send_json(400, {'error': 'Please choose a pickup date'})
        if path == "/api/menu":
            date = query.get('date')
            if date:
                try:
                    dt.date.fromisoformat(date)
                except ValueError:
                    return self.send_json(400, {'error': 'Please choose a pickup date'})
            products = []
            for p in self.db.products():
                remaining = max(0, DAILY_LIMITS[p['sku']] - self.db.reserved(date, p['sku'])) if date and p['sku'] in DAILY_LIMITS else None
                products.append({'sku': p['sku'], 'name': p['name'], 'price': p['price'],
                    'category': p['category'], 'remaining': remaining, 'sold_out': remaining == 0})
            return self.send_json(200, {'products': products})
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
            if path == "/api/quote":
                payload = self.read_json()
                with self.db.atomic():
                    order, _ = prepare_order(self.db, payload, preview=True)
                return self.send_json(200, {key: order[key] for key in (
                    'subtotal', 'discount', 'tax', 'total', 'gift_card_applied', 'gift_card_balance',
                    'amount_due', 'pickup_date', 'pickup_time')})
            if match := re.fullmatch(r"/api/orders/(\d+)/cancel", path):
                payload = self.read_json()
                token = payload.get('cancel_token') if isinstance(payload, dict) else None
                row = cancel_order(self.db, int(match[1]), token=token)
                return self.send_json(200, order_json(self.db, row)) if row else self.not_found()
            if path == "/api/orders":
                order_id = create_order(self.db, self.read_json())
                return self.send_json(201, order_json(self.db, self.db.order(order_id)))
            if match := re.fullmatch(r"/admin/api/orders/(\d+)/cancel", path):
                if not self.require_admin():
                    return
                row = self.db.order(int(match[1]))
                if row is None:
                    return self.not_found()
                cancel_order(self.db, row["id"], admin=True)
                return self.send_json(200, order_json(self.db, self.db.order(row["id"])))
        except ValidationError as exc:
            return self.send_json(400, {"error": str(exc)})
        self.not_found()

    # --- pages ----------------------------------------------------------------------------------
    def menu_page(self):
        sections, current = [], None
        for product in self.db.products():
            if product["category"] != current:
                if current is not None:
                    sections.append("</ul></section>")
                current = product["category"]
                sections.append(f"<section><h2>{html.escape(current)}</h2><ul class=\"menu\">")
            sections.append(
                f"<li class=\"item\" data-sku=\"{product['sku']}\">"
                f"<span class=\"name\">{html.escape(product['name'])}</span>"
                f"<span class=\"price\">{money(product['price'])}</span>"
                f"<button type=\"button\" class=\"add\" data-sku=\"{product['sku']}\" "
                f"data-name=\"{html.escape(product['name'])}\" data-price=\"{product['price']}\">Add</button></li>")
        if current is not None:
            sections.append("</ul></section>")
        self.send_html(200, render("menu.html", title="Order online", menu="\n".join(sections)))

    def confirmation_page(self, order_id: int):
        row = self.db.order(order_id)
        if row is None:
            return self.not_found()
        order = order_json(self.db, row)
        items = "\n".join(f"<tr><td>{i['qty']} × {html.escape(i['name'])}</td><td>{money(i['line_total'])}</td></tr>"
                          for i in order["items"])
        self.send_html(200, render(
            "confirmation.html", title=f"Order #{order_id}", order_id=order_id,
            name=html.escape(order["customer"]["name"]), pickup_date=order["pickup_date"], pickup_time=order['pickup_time'] or 'Time not recorded', items=items,
            gift_card_applied=money(order['gift_card_applied']), amount_due=money(order['amount_due']),
            gift_card_balance=money(order['gift_card_balance']) if order['gift_card_balance'] is not None else '—',
            gift_cards=''.join(f"<p>Gift card code: <strong>{c['code']}</strong> · Balance {money(c['balance'])} · {'Active' if c['active'] else 'Cancelled'}</p>" for c in order['gift_cards']),
            cancel_token=order['cancel_token'],
            subtotal=money(order["subtotal"]), discount=money(order["discount"]), tax=money(order["tax"]),
            total=money(order["total"]), status=order["status"]))

    def admin_page(self, pickup_date: str | None):
        rows = []
        for row in self.db.orders(pickup_date):
            order = order_json(self.db, row)
            items = ", ".join(f"{i['qty']} × {html.escape(i['name'])}" for i in order["items"])
            rows.append(
                f"<tr data-order-id=\"{order['id']}\" class=\"{order['status']}\"><td>#{order['id']}</td>"
                f"<td>{order['pickup_date']} {order['pickup_time'] or 'Time not recorded'}</td><td>{html.escape(order['customer']['name'])}<br>"
                f"<small>{html.escape(order['customer']['phone'])}</small></td><td>{items}</td>"
                f"<td>{money(order['amount_due'])}</td><td>{order['status']}</td></tr>")
        self.send_html(200, render("admin.html", title="Orders", date=html.escape(pickup_date or ""),
                                   rows="\n".join(rows) or "<tr><td colspan=\"6\">No orders</td></tr>"))

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
