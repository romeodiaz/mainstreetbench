# Corner Loaf Bakery — bookkeeper's notes

Close month: 2026-09 (September 2026, 2026-09-01 through 2026-09-30).
All amounts are USD. All dates and times are store local time.
These are fictional training records, not real customers or financial data.

## The exports

- `orders.csv` is the register export, one row per order line. Every order in
  it was handed over to the customer. Staff can edit a line after ringing it
  up; the line keeps its `line_id` and the edit is exported again with a higher
  `record_version`. Our register exports overlap, so some rows appear more than
  once. Loyalty members are normally rung up with their customer ID, but staff
  sometimes skip it and type whatever contact details the customer gives, or
  note the loyalty card number. Walk-in customers usually give no details.
  The export also contains late-August orders whose card charges paid out
  in September 2026, and a few older August orders that customers returned
  items from in September 2026.
- `payments.csv` has register tenders (cash and gift card) and card terminal
  transactions, including attempts, with the status the terminal reported.
  Each transaction has its own `payment_id`; these exports overlap too.
  When the terminal is linked to the register, a charge carries the order
  number in `order_id` and `reference`; sometimes only the reference came
  through. Charges keyed on the standalone terminal show a `terminal:`
  reference and no order. `fee` is what the processor charged us. The
  processor pays card charges out on `settled_at`, the next business day.
- `refunds.csv` has refund requests from the register and processor, one per
  order line, with their outcome. Each request has its own `refund_id`; these
  exports overlap too. Amounts are what was approved for that line.
  `fee_adjustment` is any fee the processor gave back. Card refunds come out of
  the processor payout on `settled_at`.
- `customers.csv` is our loyalty register. Some households share an email and
  phone number.
- `products.csv` is today's catalog. Prices change and we run promotions; the
  price on the order is what the customer was charged. Product names typed at
  the register vary; the SKU is reliable.

## How we report a month

- **Sales** are merchandise quantity times the price charged, less line
  discounts, for orders placed in the month. Returns reduce sales in the month
  the refund is completed. **Net sales** are sales after discounts minus those
  returns. Sales exclude sales tax and gift-card sales.
- Sales tax is 8% of each discounted merchandise line, rounded to the cent per
  line. Gift cards carry no tax.
- Gift cards are stored value. Selling one creates a liability, not a sale;
  redeeming one pays for merchandise. We don't have the opening gift-card
  balance.
- **Card processing fees** are the fees on card charges accepted in the month.
- **Refunds** are card and cash refunds completed in the month.
- **Net external receipts** are the card and cash money we actually took in the
  month (by payment date), less card and cash refunds completed in the month.
  Gift-card redemptions are not new money.
- **Expected card payout** is what the processor should have deposited in the
  month: card charges that settled in the month less their fees, less card
  refunds that settled in the month plus any fee given back on them. There is
  no bank statement here, so this is an expectation, not a confirmed deposit.
- Product and customer rankings use net sales. Each order counts once.

## What I need flagged

Anything where the money taken doesn't match what was ordered, refunds that
didn't go through, and sales we can't tie to a customer. Use the order,
payment, or refund numbers. If the records don't show which order or customer
something belongs to, don't guess: keep the amount, show it separately, and
flag it.
