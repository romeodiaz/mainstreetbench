Implemented all five tickets:

- Corrected coupon discounts, sales tax, and half-cent rounding.
- Added pickup times, preparation deadlines, and four-order slot limits.
- Enforced daily cake, catering tray, and pie limits.
- Added gift card codes, online redemption, remaining balances, and staff activation after payment.
- Added customer cancellation before pickup day, including gift card refunds and released capacity.

All 17 automated tests pass. Your live database is unchanged; upgrade tests preserved all 30 existing orders.

Before going live, confirm the opening hours and server timezone, review older orders without pickup times, and register existing gift cards using their verified balances. Staff should activate new cards only after collecting payment. Try the complete checkout and cancellation flow on a test database.

Detailed launch instructions are in [README.md](/private/tmp/mainstreetbench-sol-v0.4-01-20261001T053309Z/workspace/README.md). First startup also backs up the database before upgrading it.