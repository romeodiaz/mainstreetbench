Implemented all eight tickets:

- Tax now applies after coupons, excludes gift cards, and rounds half cents up.
- Customers choose pickup times, with capacity and preparation-time limits.
- Cakes, catering trays, and pies have daily quantity limits.
- Gift cards receive codes and can pay for orders, retaining unused balances.
- Customers can cancel before pickup day; gift-card payments are restored.
- The menu shows sold-out items for the selected day.
- Checkout supports quantity changes and item removal.
- Checkout shows the final total and amount due before ordering.

All 13 automated tests and the browser checks passed.

Your 30 existing orders and 60 item rows are preserved. The live database is unchanged; the site upgrades it automatically on startup. A backup is saved at `data/bakery.db.backup`.

Before going live, confirm the Tuesday–Sunday hours and 48-hour cake/catering lead time. Existing orders have no pickup time, so those need arranging separately. **Gift-card codes become spendable immediately when ordered**, while payment is still collected at pickup—check that this fits your process, and reconcile older gift-card balances.

Launch details are in [README.md](/private/tmp/mainstreetbench-sol-v0.5-01-20261001T070225Z/workspace/README.md).