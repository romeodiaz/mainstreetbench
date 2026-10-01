All three tickets are complete:

- Coupons now apply only to food; tax is calculated after discounts, gift cards are untaxed, and rounding is corrected.
- Customers choose half-hour pickup times, with four orders per slot and the required notice periods. Admin orders appear in pickup order.
- Daily limits prevent overselling. Sold-out items are marked, cancellations restore availability, and you can change limits on `/admin`.

All **30 existing orders** and their original details and totals were preserved. A backup is saved as `data/bakery.db.backup`. All 11 automated tests and the database integrity check passed.

Before going live, restart the server, check your orders and limits in admin, and try checkout in your browser using a separate test database. Older orders show **Time not assigned**, so arrange their pickup times. Also confirm the server’s local clock and admin password.

Instructions and a launch checklist are in [README.md](/private/tmp/mainstreetbench-sol-v0.3-01-20261001T043802Z/workspace/README.md).