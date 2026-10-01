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
