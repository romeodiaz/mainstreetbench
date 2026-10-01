"""HTTP server for the ordering site.

Run: python3 -m bakery.server --port 8000 --db data/bakery.db
"""

import argparse
import base64
import csv
import datetime as dt
import hmac
import html
import io
import json
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, urlparse

from . import clock, schedule, settings
from .db import Database, GiftCardInUse
from .pricing import price_order

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_QTY = 50
GIFT_CARD_SKU = "GIFT25"
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_gift_code() -> str:
    raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(12))
    return "-".join(raw[i:i + 4] for i in range(0, 12, 4))


class ValidationError(Exception):
    pass


class Conflict(Exception):
    def __init__(self, message: str, **details):
        super().__init__(message)
        self.details = details


def render(template: str, **values) -> str:
    body = Template((TEMPLATES / template).read_text(encoding="utf-8")).substitute(**values)
    return Template((TEMPLATES / "layout.html").read_text(encoding="utf-8")).substitute(
        title=values.get("title", "Corner Loaf Bakery"), body=body)


def money(value: float) -> str:
    return f"${value:,.2f}"


def order_json(db: Database, row, private: bool = True) -> dict:
    if not private:
        # Order numbers count up from 1, so without the private link only the status is shown.
        return {"id": row["id"], "status": row["status"], "pickup_date": row["pickup_date"],
                "pickup_slot": row["pickup_slot"]}
    items = [{"sku": i["sku"], "name": i["name"], "qty": i["qty"], "unit_price": i["unit_price"],
              "line_total": i["line_total"]} for i in db.order_items(row["id"])]
    return {
        "id": row["id"], "status": row["status"], "created_at": row["created_at"],
        "customer": {"name": row["customer_name"], "email": row["customer_email"], "phone": row["customer_phone"]},
        "pickup_date": row["pickup_date"], "pickup_slot": row["pickup_slot"], "items": items,
        "promo_code": row["promo_code"], "subtotal": row["subtotal"], "discount": row["discount"],
        "tax": row["tax"], "total": row["total"], "gift_card_applied": row["gift_card_applied"],
        "amount_due": round(row["total"] - row["gift_card_applied"], 2), "newsletter": bool(row["newsletter"]),
    }


def has_key(row, key) -> bool:
    return bool(row["cancel_key"]) and isinstance(key, str) and hmac.compare_digest(row["cancel_key"], key)


def confirmation_url(row) -> str:
    return f"/order/{row['id']}?key={row['cancel_key']}"


def priced_lines(db: Database, raw_items, pickup: dt.date | None) -> list:
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("Your cart is empty")
    lines = []
    for raw in raw_items:
        product = db.product(str(raw.get("sku", ""))) if isinstance(raw, dict) else None
        if product is None or not product["active"]:
            raise ValidationError("One of the items is no longer available")
        if pickup is not None and not schedule.in_season(product["sku"], pickup):
            raise ValidationError(f"{product['name']} isn't available for that day")
        qty = raw.get("qty")
        if not isinstance(qty, int) or isinstance(qty, bool) or not 1 <= qty <= MAX_QTY:
            raise ValidationError(f"Quantity for {product['name']} must be between 1 and {MAX_QTY}")
        price = product["price"]   # always our price, never one sent by the browser
        lines.append({"sku": product["sku"], "name": product["name"], "qty": qty, "category": product["category"],
                      "unit_price": price, "line_total": round(qty * price, 2)})
    return lines


def promo_for(db: Database, code: str, email: str | None):
    if not code:
        return None
    promo = db.promo(code)
    if promo is None:
        raise ValidationError("That promo code isn't valid")
    if promo["first_order_only"] and email and db.has_ordered(email):
        raise ValidationError(f"{code} is for your first order only")
    return promo


def create_order(db: Database, payload) -> int:
    if not isinstance(payload, dict):
        raise ValidationError("Order must be a JSON object")
    request_id = str(payload.get("request_id") or "")[:64] or None
    if request_id and (existing := db.order_by_request(request_id)):
        return existing["id"]
    customer = payload.get("customer") or {}
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
    if not schedule.is_open(pickup):
        raise ValidationError("We're closed that day. Please choose another day")
    slot = payload.get("pickup_slot")
    if slot not in schedule.SLOTS:
        raise ValidationError("Please choose a pickup time")
    lines = priced_lines(db, payload.get("items"), pickup)
    skus = {line["sku"] for line in lines}
    if skus & settings.PHONE_REQUIRED_SKUS and not re.search(r"\d{7}", re.sub(r"\D", "", phone)):
        raise ValidationError("Please add a phone number so we can call about your cake or catering order")
    notice = schedule.required_notice(skus)
    if schedule.slot_start(pickup, slot) < clock.now() + notice:
        raise ValidationError(f"Orders for that time need at least {int(notice.total_seconds() // 3600)} hours' notice")
    code = str(payload.get("promo_code") or "").strip().upper()
    promo = promo_for(db, code, email)
    totals = price_order(lines, promo, settings.tax_rate(clock.today()))
    gift_code = str(payload.get("gift_card_code") or "").strip().upper()
    wanted = {}
    for line in lines:
        wanted[line["sku"]] = wanted.get(line["sku"], 0) + line["qty"]

    def check(db_: Database, order: dict) -> None:
        used = db_.product_usage_unlocked(pickup.isoformat())
        for sku, qty in wanted.items():
            limit = settings.DAILY_LIMITS.get(sku)
            if limit is not None and qty > max(limit - used.get(sku, 0), 0):
                remaining = max(limit - used.get(sku, 0), 0)
                item = next(line["name"] for line in lines if line["sku"] == sku)
                raise Conflict(f"Sorry, {item} is sold out for that day" if not remaining else
                               f"Sorry, we only have {remaining} {item} left for that day", sku=sku, remaining=remaining)
        if db_.slot_usage_unlocked(pickup.isoformat()).get(slot, 0) >= settings.SLOT_CAPACITY:
            raise Conflict("That pickup time is full. Please choose another time")
        if gift_code:
            card = db_.gift_card_unlocked(gift_code)
            if card is None or card["status"] != "active":
                raise ValidationError("We don't recognise that gift card code")
            if card["balance"] <= 0:
                raise ValidationError("That gift card has no money left on it")
            order["gift_card_code"] = gift_code
            order["gift_card_applied"] = min(card["balance"], totals["total"])

    def after(db_: Database, order_id: int) -> None:
        if gift_code:
            row = db_.conn.execute("SELECT gift_card_applied FROM orders WHERE id = ?", (order_id,)).fetchone()
            db_.spend_gift_card_unlocked(gift_code, row[0])
        for line in lines:
            if line["sku"] == GIFT_CARD_SKU:
                for _ in range(line["qty"]):
                    db_.add_gift_card_unlocked(new_gift_code(), order_id, line["unit_price"])

    return db.insert_order({
        "created_at": clock.now().isoformat(), "customer_name": name, "customer_email": email,
        "customer_phone": phone, "pickup_date": pickup.isoformat(), "pickup_slot": slot,
        "promo_code": code or None, "cancel_key": secrets.token_urlsafe(16),
        "newsletter": 1 if payload.get("newsletter") is True else 0, "request_id": request_id, **totals,
    }, lines, check=check, after=after)


def quote(db: Database, payload) -> dict:
    """Price a cart exactly as an order would be priced, without saving anything."""
    if not isinstance(payload, dict):
        raise ValidationError("Quote must be a JSON object")
    pickup = None
    if payload.get("pickup_date"):
        try:
            pickup = dt.date.fromisoformat(str(payload["pickup_date"]))
        except ValueError:
            pickup = None
    lines = priced_lines(db, payload.get("items"), pickup)
    notes = []
    code = str(payload.get("promo_code") or "").strip().upper()
    try:
        promo = promo_for(db, code, str(payload.get("email") or "").strip() or None)
    except ValidationError as exc:
        promo, notes = None, [str(exc)]
    totals = price_order(lines, promo, settings.tax_rate(clock.today()))
    applied = balance_after = 0.0
    gift_code = str(payload.get("gift_card_code") or "").strip().upper()
    if gift_code:
        card = db.gift_card(gift_code)
        if card is None or card["status"] != "active" or card["balance"] <= 0:
            notes.append("That gift card code isn't valid or has no money left")
        else:
            applied = min(card["balance"], totals["total"])
            balance_after = round(card["balance"] - applied, 2)
    return {**totals, "gift_card_applied": applied, "gift_card_balance_after": balance_after,
            "amount_due": round(totals["total"] - applied, 2), "notes": notes}


def parse_date(value) -> dt.date:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError("Use a date like 2026-10-10") from None


def slots_json(db: Database, day: dt.date) -> dict:
    if not schedule.is_open(day):
        return {"date": day.isoformat(), "open": False, "slots": []}
    used = db.slot_usage(day.isoformat())
    earliest = clock.now() + settings.NOTICE
    return {"date": day.isoformat(), "open": True, "slots": [
        {"time": t, "remaining": max(settings.SLOT_CAPACITY - used.get(t, 0), 0),
         "available": used.get(t, 0) < settings.SLOT_CAPACITY and schedule.slot_start(day, t) >= earliest}
        for t in schedule.SLOTS]}


def menu_json(db: Database, day: dt.date | None) -> list:
    used = db.product_usage(day.isoformat()) if day else {}
    products = []
    for p in db.products():
        item = {"sku": p["sku"], "name": p["name"], "price": p["price"], "category": p["category"]}
        if day is not None:
            limit = settings.DAILY_LIMITS.get(p["sku"])
            remaining = None if limit is None else max(limit - used.get(p["sku"], 0), 0)
            item.update(remaining=remaining, sold_out=remaining == 0,
                        available=schedule.in_season(p["sku"], day) and schedule.is_open(day))
        products.append(item)
    return products


class Handler(BaseHTTPRequestHandler):
    server_version = "CornerLoaf/2.0"
    db: Database = None
    admin_password = "flour"

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
        if "/api/" in self.path:
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
        return hmac.compare_digest(password, self.admin_password)

    def require_admin(self) -> bool:
        if self.is_admin():
            return True
        self.send(401, b"Admin login required", "text/plain", {"WWW-Authenticate": 'Basic realm="Corner Loaf admin"'})
        return False

    def do_GET(self):
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        path = url.path
        try:
            if path == "/":
                return self.menu_page()
            if path == "/checkout":
                return self.send_html(200, render("checkout.html", title="Checkout"))
            if path == "/contact":
                return self.send_html(200, render("contact.html", title="Contact us", phone=settings.SHOP_PHONE,
                                                  email=settings.SHOP_EMAIL))
            if match := re.fullmatch(r"/order/(\d+)", path):
                return self.confirmation_page(int(match[1]), query.get("key"))
            if path == "/api/menu":
                day = parse_date(query["date"]) if "date" in query else None
                return self.send_json(200, {"products": menu_json(self.db, day)})
            if path == "/api/slots":
                return self.send_json(200, slots_json(self.db, parse_date(query.get("date", ""))))
            if match := re.fullmatch(r"/api/orders/(\d+)", path):
                row = self.db.order(int(match[1]))
                if row is None:
                    return self.not_found()
                return self.send_json(200, order_json(self.db, row, private=has_key(row, query.get("key"))))
            if path == "/admin":
                return self.require_admin() and self.admin_page(query.get("date"))
            if path == "/admin/api/orders":
                if self.require_admin():
                    self.send_json(200, {"orders": [order_json(self.db, r) for r in self.db.orders(query.get("date"))]})
                return
            if path == "/admin/orders.csv":
                return self.require_admin() and self.orders_csv()
        except ValidationError as exc:
            return self.send_json(400, {"error": str(exc)})
        if path.startswith("/static/"):
            return self.static(path[len("/static/"):])
        self.not_found()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/quote":
                return self.send_json(200, quote(self.db, self.read_json()))
            if path == "/api/orders":
                row = self.db.order(create_order(self.db, self.read_json()))
                return self.send_json(201, {**order_json(self.db, row), "confirmation_url": confirmation_url(row)})
            if match := re.fullmatch(r"/api/orders/(\d+)/cancel", path):
                return self.customer_cancel(int(match[1]), self.read_json())
            if match := re.fullmatch(r"/admin/api/orders/(\d+)/cancel", path):
                if not self.require_admin():
                    return
                row = self.db.order(int(match[1]))
                if row is None:
                    return self.not_found()
                self.db.cancel_order(row["id"])
                return self.send_json(200, order_json(self.db, self.db.order(row["id"])))
        except ValidationError as exc:
            return self.send_json(400, {"error": str(exc)})
        except Conflict as exc:
            return self.send_json(409, {"error": str(exc), **exc.details})
        except GiftCardInUse as exc:
            return self.send_json(409, {"error": str(exc)})
        self.not_found()

    def customer_cancel(self, order_id: int, body):
        row = self.db.order(order_id)
        key = body.get("key") if isinstance(body, dict) else None
        if row is None or not has_key(row, key):
            return self.send_json(403, {"error": "Use the link from your order confirmation to cancel"})

        def allow(current):
            if dt.date.fromisoformat(current["pickup_date"]) <= clock.today():
                raise ValidationError("Orders can't be cancelled on the day of pickup. Please call us")

        self.db.cancel_order(order_id, allow=allow)
        self.send_json(200, order_json(self.db, self.db.order(order_id)))

    def menu_page(self):
        sections, current = [], None
        for product in self.db.products():
            if product["category"] != current:
                if current is not None:
                    sections.append("</ul></section>")
                current = product["category"]
                sections.append(f"<section><h2>{html.escape(current)}</h2><ul class=\"menu\">")
            name = html.escape(product["name"], quote=True)
            sections.append(
                f"<li class=\"item\" data-sku=\"{product['sku']}\"><span class=\"name\">{name}</span>"
                f"<span class=\"price\">{money(product['price'])}</span><span class=\"note\"></span>"
                f"<button type=\"button\" class=\"add\" data-sku=\"{product['sku']}\" data-name=\"{name}\" "
                f"data-price=\"{product['price']}\">Add</button></li>")
        if current is not None:
            sections.append("</ul></section>")
        self.send_html(200, render("menu.html", title="Order online", menu="\n".join(sections)))

    def confirmation_page(self, order_id: int, key):
        row = self.db.order(order_id)
        if row is None:
            return self.not_found()
        if not has_key(row, key):
            # Order numbers count up from 1, so without the private link show only the status.
            public = [f"Order #{order_id} is {row['status']}."]
            public.append("Open the link from your confirmation to see details.")
            return self.send_html(200, render("message.html", title=f"Order #{order_id}", message=" ".join(public)))
        order = order_json(self.db, row)
        items = "\n".join(f"<tr><td>{i['qty']} × {html.escape(i['name'])}</td><td>{money(i['line_total'])}</td></tr>"
                          for i in order["items"])
        extras = []
        for card in self.db.gift_cards_for_order(order_id):
            state = "void (order cancelled)" if card["status"] == "void" else f"{money(card['balance'])} on it"
            extras.append(f"<p class=\"gift-card-code\">Gift card code: <strong>{card['code']}</strong> ({state})</p>")
        if row["gift_card_code"]:
            card = self.db.gift_card(row["gift_card_code"])
            extras.append(f"<p>Paid with gift card: {money(row['gift_card_applied'])}. "
                          f"Left on that card: {money(card['balance'])}.</p>")
        extras.append(f"<p class=\"amount-due\">Pay at pickup: <strong>{money(order['amount_due'])}</strong></p>")
        if order["status"] == "placed" and dt.date.fromisoformat(order["pickup_date"]) > clock.today():
            extras.append(f"<button type=\"button\" id=\"cancel-order\" data-order-id=\"{order_id}\" "
                          f"data-key=\"{html.escape(key)}\">Cancel order</button>"
                          "<p id=\"cancel-error\" class=\"error\" role=\"alert\"></p>")
        self.send_html(200, render(
            "confirmation.html", title=f"Order #{order_id}", order_id=order_id,
            name=html.escape(order["customer"]["name"]), pickup_date=order["pickup_date"],
            pickup_slot=order["pickup_slot"] or "any time", items=items, subtotal=money(order["subtotal"]),
            discount=money(order["discount"]), tax=money(order["tax"]), total=money(order["total"]),
            status=order["status"], extras="\n".join(extras)))

    def admin_page(self, pickup_date):
        rows = []
        for row in self.db.orders(pickup_date):
            order = order_json(self.db, row)
            items = ", ".join(f"{i['qty']} × {html.escape(i['name'])}" for i in order["items"])
            status = order["status"]
            rows.append(
                f"<tr data-order-id=\"{order['id']}\" class=\"{status}\"><td>#{order['id']}</td>"
                f"<td>{order['pickup_date']}</td><td>{order['pickup_slot'] or '—'}</td>"
                f"<td>{html.escape(order['customer']['name'])}<br><small>{html.escape(order['customer']['phone'])}</small></td>"
                f"<td>{items}</td><td>{money(order['total'])}</td><td>{money(order['gift_card_applied'])}</td>"
                f"<td>{money(order['amount_due'])}</td><td class=\"status\">{status}</td></tr>")
        self.send_html(200, render("admin.html", title="Orders", date=html.escape(pickup_date or ""),
                                   rows="\n".join(rows) or "<tr><td colspan=\"9\">No orders</td></tr>"))

    def orders_csv(self):
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["id", "pickup_date", "pickup_slot", "name", "email", "phone", "total", "status"])
        for row in self.db.orders():
            writer.writerow([row["id"], row["pickup_date"], row["pickup_slot"] or "", row["customer_name"],
                             row["customer_email"], row["customer_phone"], f"{row['total']:.2f}", row["status"]])
        self.send(200, out.getvalue().encode(), "text/csv; charset=utf-8")

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
