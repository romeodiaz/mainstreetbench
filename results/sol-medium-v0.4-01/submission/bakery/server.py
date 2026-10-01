"""HTTP server for the ordering site.

Run: python3 -m bakery.server --port 8000 --db data/bakery.db
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
from decimal import Decimal, InvalidOperation
import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, urlparse

from . import clock
from .db import Database, OrderError
from .pricing import price_order, cents
from .pickup import eligible_slots, DAILY_LIMITS

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_QTY = 50


class ValidationError(Exception):
    pass


def render(template: str, **values) -> str:
    body = Template((TEMPLATES / template).read_text(encoding="utf-8")).substitute(**values)
    return Template((TEMPLATES / "layout.html").read_text(encoding="utf-8")).substitute(
        title=values.get("title", "Corner Loaf Bakery"), body=body)


def money(value: float) -> str:
    return f"${value:,.2f}"


def order_json(db: Database, row, private=False) -> dict:
    items = [{"sku": i["sku"], "name": i["name"], "qty": i["qty"], "unit_price": i["unit_price"],
              "line_total": i["line_total"]} for i in db.order_items(row["id"])]
    return {
        "id": row["id"], "status": row["status"], "created_at": row["created_at"],
        "customer": {"name": row["customer_name"], "email": row["customer_email"], "phone": row["customer_phone"]},
        "pickup_date": row["pickup_date"], "items": items, "promo_code": row["promo_code"],
        "pickup_time": row['pickup_time'],
        "gift_card_applied": row['gift_card_applied'], "gift_card_balance": row['gift_card_balance'],
        "amount_due": row['amount_due'] if row['amount_due'] is not None else row['total'],
        "gift_cards": [{"code": c['code'], "value": c['initial_cents']/100,
                        "balance": c['balance_cents']/100, "active": bool(c['active'])}
                       for c in db.gift_cards(row['id'])] if private else [],
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
    try:
        pickup = dt.date.fromisoformat(str(payload.get("pickup_date", "")))
    except ValueError:
        raise ValidationError("Please choose a pickup date") from None
    if pickup < clock.today():
        raise ValidationError("Pickup date is in the past")

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
                      "category": product["category"], "unit_price": product["price"], "line_total": float(cents(qty * cents(product["price"])))})

    code = str(payload.get("promo_code") or "").strip().upper()
    promo = db.promo(code) if code else None
    if code and promo is None:
        raise ValidationError("That promo code isn't valid")
    slots = eligible_slots(pickup, lines, clock.now())
    requested_time = payload.get('pickup_time')
    if requested_time is not None and (not isinstance(requested_time, str) or requested_time not in slots):
        raise ValidationError('Choose an open half-hour pickup time with enough preparation time')
    totals = price_order(lines, promo)
    return db.insert_order({
        "created_at": clock.now().isoformat(), "customer_name": name, "customer_email": email,
        "customer_phone": phone, "pickup_date": pickup.isoformat(), "promo_code": code or None, **totals,
    }, lines, slots, requested_time, str(payload.get('gift_card_code') or '').strip().upper())


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
        self.send_header("Referrer-Policy", "no-referrer")
        if content_type != "text/css" and content_type != "application/javascript":
            self.send_header("Cache-Control", "no-store")
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
            return self.confirmation_page(int(match[1]), query.get('token'))
        if path == '/api/pickup-times':
            try:
                date = dt.date.fromisoformat(query.get('date', ''))
            except ValueError:
                return self.send_json(400, {'error': 'Please choose a pickup date'})
            lines = [{'sku': sku} for sku in query.get('skus', '').split(',')]
            counts = {r['pickup_time']: r['n'] for r in self.db.query(
                "SELECT pickup_time, COUNT(*) AS n FROM orders WHERE pickup_date=? AND status='placed' GROUP BY pickup_time",
                (date.isoformat(),))}
            times = [{'time': t, 'remaining': max(0, 4-counts.get(t, 0))}
                     for t in eligible_slots(date, lines, clock.now())]
            remaining = {}
            for sku, limit in DAILY_LIMITS.items():
                sold = self.db.query("SELECT COALESCE(SUM(i.qty),0) AS n FROM order_items i JOIN orders o ON o.id=i.order_id "
                                     "WHERE o.pickup_date=? AND o.status='placed' AND i.sku=?", (date.isoformat(), sku))[0]['n']
                remaining[sku] = max(0, limit-sold)
            return self.send_json(200, {'pickup_date': date.isoformat(), 'times': times, 'remaining': remaining})
        if path == "/api/menu":
            return self.send_json(200, {"products": [
                {"sku": p["sku"], "name": p["name"], "price": p["price"], "category": p["category"]}
                for p in self.db.products()]})
        if match := re.fullmatch(r"/api/orders/(\d+)", path):
            row = self.db.order(int(match[1]))
            return self.send_json(200, order_json(self.db, row, self.private_access(row, query.get('token')))) if row else self.not_found()
        if path == "/admin":
            return self.require_admin() and self.admin_page(query.get("date"))
        if path == "/admin/api/orders":
            if self.require_admin():
                self.send_json(200, {"orders": [order_json(self.db, r, True) for r in self.db.orders(query.get("date"))]})
            return
        if path.startswith("/static/"):
            return self.static(path[len("/static/"):])
        self.not_found()

    def do_POST(self):
        path = urlparse(self.path).path
        origin = self.headers.get('Origin')
        if origin and urlparse(origin).netloc != self.headers.get('Host'):
            return self.send_json(400, {'error': 'Submit this request from the bakery website'})
        try:
            if path == '/admin/api/gift-cards':
                if not self.require_admin():
                    return
                payload = self.read_json()
                if not isinstance(payload, dict):
                    raise ValidationError('Gift card must be a JSON object')
                order_id = payload.get('order_id')
                code = str(payload.get('code') or '').strip().upper()
                if not isinstance(order_id, int) or isinstance(order_id, bool) or order_id <= 0:
                    raise ValidationError('Enter the original order number')
                if not re.fullmatch(r'[A-Z0-9-]{3,64}', code):
                    raise ValidationError('Card code must contain 3–64 letters, numbers or hyphens')
                try:
                    balance = Decimal(str(payload.get('balance')))
                    if not balance.is_finite() or balance < 0 or balance > 1000000 or balance != cents(balance):
                        raise InvalidOperation
                except (InvalidOperation, ValueError):
                    raise ValidationError('Enter a valid remaining balance in dollars with at most two decimals') from None
                if not self.db.import_gift_card(order_id, code, int(balance * 100)):
                    return self.not_found()
                return self.send_json(201, order_json(self.db, self.db.order(order_id), True))
            if path == "/api/orders":
                order_id = create_order(self.db, self.read_json())
                row = self.db.order(order_id)
                result = order_json(self.db, row, True)
                result['cancel_token'] = row['cancel_token']
                result['order_url'] = f"/order/{order_id}?token={row['cancel_token']}"
                return self.send_json(201, result)
            if match := re.fullmatch(r"/api/orders/(\d+)/cancel", path):
                payload = self.read_json()
                if not isinstance(payload, dict):
                    raise ValidationError('Cancellation must be a JSON object')
                order_id = int(match[1])
                if not self.db.cancel(order_id, clock.today(), token=payload.get('cancel_token')):
                    return self.not_found()
                return self.send_json(200, order_json(self.db, self.db.order(order_id), True))
            if match := re.fullmatch(r"/admin/api/orders/(\d+)/activate-gift-cards", path):
                if not self.require_admin():
                    return
                order_id = int(match[1])
                if not self.db.activate_gift_cards(order_id):
                    return self.not_found()
                return self.send_json(200, order_json(self.db, self.db.order(order_id), True))
            if match := re.fullmatch(r"/admin/api/orders/(\d+)/cancel", path):
                if not self.require_admin():
                    return
                row = self.db.order(int(match[1]))
                if row is None:
                    return self.not_found()
                self.db.cancel(row["id"], clock.today(), admin=True)
                return self.send_json(200, order_json(self.db, self.db.order(row["id"])))
        except (ValidationError, OrderError) as exc:
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

    def private_access(self, row, token):
        import secrets
        return self.is_admin() or bool(row and row['cancel_token'] and isinstance(token, str)
                                       and secrets.compare_digest(row['cancel_token'].encode(), token.encode()))

    def confirmation_page(self, order_id: int, token=None):
        row = self.db.order(order_id)
        if row is None:
            return self.not_found()
        private = self.private_access(row, token)
        order = order_json(self.db, row, private)
        items = "\n".join(f"<tr><td>{i['qty']} × {html.escape(i['name'])}</td><td>{money(i['line_total'])}</td></tr>"
                          for i in order["items"])
        cards = ''.join(f"<li><strong>{c['code']}</strong>: {money(c['balance'])} remaining"
                        f"{' (void)' if row['status'] == 'cancelled' else ' (activate at pickup after payment)' if not c['active'] else ''}</li>" for c in order['gift_cards'])
        cancel = ''
        if row['status'] == 'placed' and row['pickup_date'] > clock.today().isoformat():
            if private:
                credential = f'<input type="hidden" name="cancel_token" value="{html.escape(row["cancel_token"])}">'
                cancel = f'<form id="cancel-order" data-order-id="{order_id}">{credential}<button>Cancel order</button><p role="alert" id="cancel-error"></p></form><script src="/static/order.js"></script>'
            else:
                cancel = '<p>Use the private link saved after checkout to see gift card codes or cancel.</p>'
        self.send_html(200, render(
            "confirmation.html", title=f"Order #{order_id}", order_id=order_id,
            name=html.escape(order["customer"]["name"]), pickup_date=order["pickup_date"], items=items,
            pickup_time=order['pickup_time'] or 'Time not set (existing order)',
            gift_card_applied=money(order['gift_card_applied']),
            gift_card_balance=money(order['gift_card_balance']) if order['gift_card_balance'] is not None else '—',
            amount_due=money(order['amount_due']), gift_cards=f'<h2>Your gift cards</h2><ul>{cards}</ul>' if cards else '',
            cancel=cancel,
            subtotal=money(order["subtotal"]), discount=money(order["discount"]), tax=money(order["tax"]),
            total=money(order["total"]), status=order["status"]))

    def admin_page(self, pickup_date: str | None):
        rows = []
        for row in self.db.orders(pickup_date):
            order = order_json(self.db, row)
            items = ", ".join(f"{i['qty']} × {html.escape(i['name'])}" for i in order["items"])
            cards = self.db.gift_cards(order['id'])
            action = (f'<button type="button" class="activate-cards" data-order-id="{order["id"]}">Activate gift cards after payment</button>'
                      if order['status'] == 'placed' and any(not c['active'] for c in cards) else '')
            rows.append(
                f"<tr data-order-id=\"{order['id']}\" class=\"{order['status']}\"><td>#{order['id']}<br>"
                f"<a href=\"/order/{order['id']}?token={row['cancel_token']}\">Private order link</a></td>"
                f"<td>{order['pickup_date']} {order['pickup_time'] or 'Time not set'}</td><td>{html.escape(order['customer']['name'])}<br>"
                f"<small>{html.escape(order['customer']['phone'])}</small></td><td>{items}</td>"
                f"<td>{money(order['amount_due'])}</td><td>{order['status']} {action}</td></tr>")
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
