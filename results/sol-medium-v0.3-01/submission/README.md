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
- `POST /api/orders` with `{"customer": {"name", "email", "phone"}, "pickup_date": "YYYY-MM-DD", "pickup_slot": "HH:MM", "items": [{"sku", "qty"}], "promo_code"}` → `201` and the order. Invalid input → `400 {"error": "..."}`. Full pickup times or insufficient daily quantities → `409` with `error` (quantity conflicts also include `sku` and `remaining`).
- `GET /api/orders/<id>` → the order, or `404`.
- `GET /admin/api/orders[?date=YYYY-MM-DD]` (admin) → `{"orders": [...]}`.
- `POST /admin/api/orders/<id>/cancel` (admin) → the order, with `status` `"cancelled"`.

An order looks like:

```json
{"id": 1, "status": "placed", "created_at": "2026-10-08T09:10:00",
 "customer": {"name": "Ana", "email": "ana@example.com", "phone": "555-0100"},
 "pickup_date": "2026-10-10", "pickup_slot": "12:00", "items": [{"sku": "BREAD9", "name": "Sourdough Loaf", "qty": 2,
 "unit_price": 9.0, "line_total": 18.0}], "promo_code": null,
 "subtotal": 18.0, "discount": 0.0, "tax": 1.44, "total": 19.44}
```

Money in the API is dollars as JSON numbers with at most two decimals. Admin endpoints use HTTP Basic auth; they return `401` without it.

## Pickup and daily availability

New orders require `pickup_slot`, a half-hour start from `07:00` through `14:30`, Tuesday–Sunday.
Allow at least 2 hours before the slot, or 48 hours for CAKE48 and CATER120.
Only non-cancelled orders count toward the 4 orders per slot and daily product limits.

- `GET /api/slots?date=YYYY-MM-DD` returns `date`, `open` and `slots` with `time`, `remaining` and `available`. Availability reflects the 2-hour minimum; orders containing cakes or catering still need 48 hours.
- `GET /api/menu` includes `daily_limit` on each product. With `?date=YYYY-MM-DD`, it also includes `remaining` and `sold_out`. Unlimited products have `remaining: null`.
- `/?date=YYYY-MM-DD` shows sold-out items for that day. Choose a date on the menu to check availability; the Cart link carries that date to checkout.
- Change limits under **Daily baking limits** on `/admin`. Blank means unlimited; 0 stops further sales. Limits apply to every pickup date and stay saved after restart.
- `PUT /admin/api/products/<sku>` (admin) accepts `{"daily_limit": 5}` or `{"daily_limit": null}` and returns the product. Invalid limits return 400; unknown products return 404.
- Admin lists sort by pickup date, then time (unassigned first), then order number.

Coupons apply only to food (all categories except Gift Cards). Tax is 8% of food after discount; gift cards are untaxed. Discount and tax use half-up cent rounding.

## Existing orders and going live

Starting the updated server adds database columns without removing or repricing old orders.
Older orders have `pickup_slot: null` and display **Time not assigned**. Their quantities still count toward daily limits.
Default limits are 6 birthday cakes, 4 catering trays and 8 seasonal pies per pickup date.
Changing limits never cancels existing orders.

A pre-change backup is saved at `data/bakery.db.backup`. All 30 existing orders and their original fields were verified against it after migration; the database integrity check passed.

Before going live:

1. Restart the server with `data/bakery.db` and check `/admin` for the existing orders and intended limits.
2. Arrange pickup times for older orders that say **Time not assigned**; those orders cannot occupy a particular slot until a time is recorded.
3. Try checkout in your browser on a separate test database, including a coupon and a gift card. Check that the pickup times load, confirmation shows the chosen time, and a limit change saves in admin.
4. Confirm the server clock uses the bakery's local time and `CORNERLOAF_NOW` is unset in production. Set your own `ADMIN_PASSWORD` instead of the default `flour`.

Use a separate database for trials, for example `python3 -m bakery.server --port 8001 --db /tmp/cornerloaf-trial.db`. Re-run the automated checks with `python3 -m unittest discover -s tests -v`; they use throwaway databases.
