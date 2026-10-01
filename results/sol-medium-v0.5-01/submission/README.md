# Corner Loaf Bakery — online ordering

Customers order on the website and pay when they pick up. Staff see orders on `/admin`.

Built with Python's standard library only: no packages to install.

## Run it

```sh
python3 -m bakery.server --port 8000 --db data/bakery.db
```

Open http://127.0.0.1:8000. The admin page is http://127.0.0.1:8000/admin; the username can be anything, and the password is `ADMIN_PASSWORD` (default `flour`). The database file is created and seeded with the menu and promo codes on first start. `data/bakery.db` is the live database, with real customer orders in it. Don't delete it.

## Test it

```sh
python3 -m unittest discover -s tests -v
```

Each test starts the server on a free port with a throwaway database. Set `CORNERLOAF_NOW=2026-10-08T09:10:00` (store local time) to pin the clock; the tests do this.

## How it fits together

| File | What it does |
|---|---|
| `bakery/server.py` | Routes, order validation, HTML pages, admin |
| `bakery/db.py` | SQLite schema, seed menu and promo codes, queries |
| `bakery/pricing.py` | Subtotal, promo discount, sales tax and total |
| `bakery/clock.py` | Store-local "now" (pinnable for tests) |
| `bakery/templates/` | Page templates (`string.Template`) |
| `bakery/static/` | CSS, cart (localStorage) and checkout script |

## API

The checkout page and the bookkeeper's export both use this API. Keep existing fields and status codes working when you change things; add new fields rather than renaming old ones.

- `GET /api/menu` → `{"products": [{"sku", "name", "price", "category"}]}`
- `POST /api/orders` with `{"customer": {"name", "email", "phone"}, "pickup_date": "YYYY-MM-DD", "items": [{"sku", "qty"}], "promo_code"}` → `201` and the order. Invalid input → `400 {"error": "..."}`.
- `GET /api/orders/<id>` → the order, or `404`.
- `GET /admin/api/orders[?date=YYYY-MM-DD]` (admin) → `{"orders": [...]}`.
- `POST /admin/api/orders/<id>/cancel` (admin) → the order, with `status` `"cancelled"`.

An order looks like:

```json
{"id": 1, "status": "placed", "created_at": "2026-10-08T09:10:00",
 "customer": {"name": "Ana", "email": "ana@example.com", "phone": "555-0100"},
 "pickup_date": "2026-10-10", "items": [{"sku": "BREAD9", "name": "Sourdough Loaf", "qty": 2,
 "unit_price": 9.0, "line_total": 18.0}], "promo_code": null,
 "subtotal": 18.0, "discount": 0.0, "tax": 1.44, "total": 19.44}
```

Money in the API is dollars as JSON numbers with at most two decimals. Admin endpoints use HTTP Basic auth; they return `401` without it.

## October ordering updates

Checkout now lets customers edit quantities, remove items, select a pickup time,
apply a coupon or gift card, and see the server-calculated total before placing
an order. Coupons apply to food only; tax is 8% on food after the discount, with
half cents rounded up. Gift cards have no tax or coupon discount. `total` remains
the total after coupons and tax; `amount_due` subtracts the gift-card payment.

Pickup times run Tuesday–Sunday, 07:00 through 14:30, with four orders per slot.
Ordinary orders require two hours; any cake or catering tray requires 48 hours.
The daily limits are six cakes, four catering trays, and eight pies. Cancelled
orders release both their slot and item capacity. Older API clients that omit
`pickup_time` get the first eligible slot; explicitly invalid times return 400.

New API additions (existing endpoints and fields are retained):

- `GET /api/menu?date=YYYY-MM-DD` adds `remaining` and `sold_out` per product.
- `GET /api/pickup-slots?date=YYYY-MM-DD&skus=CAKE48,BREAD9` returns `slots`
  containing `time` and `available`.
- `POST /api/quote` accepts order fields, without requiring customer details,
  and returns pricing, gift-card deductions, remaining balance, and pickup time.
  It validates capacity and codes without reserving stock or spending a card.
- `POST /api/orders` also accepts `pickup_time` and `gift_card_code`.
- Orders also include `pickup_time`, `gift_card_applied`, `gift_card_balance`
  (the balance immediately after this payment), `amount_due`, `gift_cards`
  (issued codes and current balances), and `cancel_token`.
- `POST /api/orders/<id>/cancel` accepts `{"cancel_token": "..."}` from the
  order confirmation page. Customers may cancel only before pickup day.
  Repeating a cancellation has no further effect.

Cancellation returns any gift-card payment and disables cards issued by that
order. An order whose issued card has already been spent cannot be cancelled
online, including through the admin endpoint; staff must resolve it manually.
Gift-card codes are issued on ordering and are immediately redeemable. This site
still collects payment at pickup, so staff should check payment for gift-card
purchases as part of their operating process.

### Before going live

1. Keep a fresh database backup. `data/bakery.db.backup` is the pre-change copy.
   The new server upgrades the database automatically, adding fields and a
   gift-card table. Existing order items and recorded totals stay unchanged.
   Active older gift-card purchases receive codes once. Older orders have
   no recorded pickup time and display “Time not recorded”; arrange those
   times with customers separately.
2. Confirm the posted hours, 48-hour cake/catering lead time, and daily limits.
   The server clock must use the bakery's local timezone. Leave
   `CORNERLOAF_NOW` unset in production.
3. Use a private `ADMIN_PASSWORD`, then try a test order on a phone: edit the
   cart, choose a slot, apply a coupon and a gift card, and cancel before
   pickup day. Verify the admin list shows the pickup time and amount due.

Validation: `python3 -m unittest discover -s tests -v` covers the existing
ordering API, pricing, capacity, simultaneous orders/redemptions, cancellation,
quotes, and migration of a copy of the live database. Browser smoke checks also
covered cart editing, previews, ordering, gift-card redemption, cancellation,
and sold-out buttons.
