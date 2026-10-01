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

## October changes and launch checks

Coupons now discount food only. The 8% sales tax applies to food after the
coupon; gift cards have no tax or coupon discount. Money rounds half cents up.
Existing orders keep their original prices and totals.

Pickup runs Tuesday–Sunday from 07:00 through 14:30, in half-hour slots with
four orders each. Regular orders need two hours; birthday cakes and catering
trays need 48 hours. The server's local timezone must match the bakery's.
Daily limits are six cakes, four catering trays and eight seasonal pies.
Placed orders, including existing orders, count toward these limits;
cancelled orders release their reservations. Staff orders sort by pickup date,
time, then order number. Existing orders have **Time not set**; confirm their
pickup arrangements with customers before launch. Their times are not guessed
or counted against individual half-hour slots.

Gift cards get unique codes on the customer's private order page, one code per
card purchased. Because payment is collected at pickup, staff must collect
payment and then click **Activate gift cards after payment** on `/admin`.
Until then those cards cannot be spent. Checkout accepts one card per order,
applies up to its balance to the total after tax, and shows the amount applied,
balance after payment and amount still due. `total` remains the original order
total for export compatibility; `amount_due` is what staff should collect.
The card's own order page shows its current balance. Registration and
activation do not process a payment or replace your payment records.

There are seven historical gift-card purchase lines in the supplied database.
The old schema stores neither their codes nor remaining balances. Use
**Register an existing gift card** on `/admin` to enter each original order
number, existing code and verified remaining balance after checking your
payment records. Codes use 3–64 letters, digits or hyphens. The site prevents
registering more cards than were purchased on that order. Existing physical
cards are not automatically given new credit.

Customers can cancel through their private order link before the pickup day.
Cancellation restores any gift-card payment once, releases capacity and voids
unused gift cards bought on that order. Orders with purchased cards that have
already been spent require staff help. Admin cancellation keeps its existing
endpoint and can override the pickup-day cutoff, but cannot erase spent card
credit. Every order, including older orders, has a private link available to
staff on `/admin`; share that link with a customer who needs it. The site does
not send emails. Customers should save their checkout link; gift-card codes
and cancellation controls are protected by it.

Before going live:

1. Stop the old server and keep a separate backup of `data/bakery.db`. Start
   the new version with the same database path. First startup also creates
   `data/bakery.db.pre-upgrade.bak` before upgrading the original schema.
   The upgrade only adds storage; it preserves every existing order and item.
2. Confirm the hours, 48-hour cake/catering lead time and server timezone.
   Remove any testing `CORNERLOAF_NOW` setting, and set `ADMIN_PASSWORD`.
3. Review old orders without pickup times and register verified old gift cards.
4. On a test database, try a coupon order, a gift-card purchase and activation,
   a partial gift-card payment and a cancellation. Check both the customer
   page and staff page. Use HTTPS in your live hosting setup to keep private
   links and the existing Basic admin login private.

Verification: the automated suite covers prices, old-schema upgrades, HTTP
ordering, pickup rules, daily limits, private cancellation, gift-card activation,
registration and refunds, and simultaneous attempts to reserve stock, pickup
slots or spend a card. The supplied live database was also upgraded twice on a
throwaway copy; all 30 orders and all original table values were preserved.
The supplied `data/bakery.db` was left unchanged during development.

## Added API fields and endpoints

Existing endpoints, fields and dollar-number money format remain available.
New order requests can send `pickup_time` (`HH:MM`) and `gift_card_code`.
Old clients omitting the pickup time get the earliest eligible available slot.
New order fields are `pickup_time`, `gift_card_applied`, `gift_card_balance`
(the balance just after that order's payment), `amount_due`, and `gift_cards`.
Creation also returns `cancel_token` and `order_url`. Purchased card codes are
included only in the creation response, authorized cancellation response,
admin responses, or a fetch with the order's `?token=...`; public fetches
return an empty `gift_cards` list. Each private card has `code`, `value`, current
`balance` and `active`.

- `GET /api/pickup-times?date=YYYY-MM-DD&skus=CAKE48,BREAD9` returns `times`
  with `time` and remaining order capacity, plus `remaining` quantities by
  limited product SKU. Checkout revalidates availability transactionally.
- `POST /api/orders/<id>/cancel` accepts `{"cancel_token": "..."}`. Returns
  the cancelled order (`200`), `400` for invalid credentials or disallowed
  cancellations, or `404` for an unknown order. Repeating a successful
  cancellation does not refund twice.
- `POST /admin/api/orders/<id>/activate-gift-cards` (admin) activates the
  purchased cards after staff confirms payment and returns the order (`200`).
- `POST /admin/api/gift-cards` (admin) accepts
  `{"order_id": 12, "code": "OLD-123", "balance": 12.50}` to register one
  verified historical card and returns its order (`201`). Invalid input is
  `400`; an unknown order is `404`.
