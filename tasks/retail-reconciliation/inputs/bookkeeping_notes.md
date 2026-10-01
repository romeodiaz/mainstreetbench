# Corner Loaf Bakery — bookkeeper's notes

Close month: 2026-09
Reporting period: 2026-09-01 through 2026-09-30, inclusive.
All amounts are USD. All dates and times use our store's local calendar.
These are fictional training records, not real customers or financial data.

Please use these rules for our September 2026 close. The register and processor
exports cover the close month, plus older records needed to understand returns
and transactions that settle this month. An older order is supporting evidence,
not a new sale this month. Earlier-month card charges and completed refunds
settled in this month belong in expected payout, while their original sale,
payment, and refund-completion dates still control the other period totals.

## What each export means

- `orders.csv` is one row per order line, not one row per whole order. An order
  can have several products. `line_id` identifies a line across exports.
  Keep the highest `record_version` for each line; a newer version replaces the
  entire older line. Repeated identical rows are duplicate exports. Count the
  latest line once. Two different order IDs can be real repeat purchases even
  when everything else looks the same. All latest orders here were fulfilled.
- `payments.csv` includes register tenders and processor attempts. Count each
  `payment_id` once. `captured` means accepted; `declined` means no money was
  taken. A failed attempt followed by a captured payment is one accepted
  payment. Distinct captured IDs represent distinct actual tenders, including
  an accidental second charge; keep both and flag any excess. `reference` can
  contain `order:<order_id>` when the normal order field is missing. That exact
  reference is reliable. Do not guess a match from an amount or date alone.
- `refunds.csv` is the refund processor/register export. Count each `refund_id`
  once. Only `succeeded` refunds move money and reduce sales. `failed` and
  `pending` are requests that have not been paid. Each refund references one
  `line_id`; multiple lines on a receipt must not multiply the payment or refund.
  `refund_sales`, `refund_tax`, and `refund_total` are the actual approved amounts.
  A partial refund returns only the listed quantity and amounts. Do not refund
  the whole order just because one line has a refund. No succeeded refund in
  this packet is repeated as a payment row.
- `customers.csv` is our loyalty register. An explicit customer ID is
  authoritative even if a checkout name is abbreviated or contacts vary.
  Different IDs remain different people, including the two Alex Morgans who
  share household contact details. When an order has no ID, assign one only if
  its contact details or recorded loyalty reference identify exactly one
  register entry. If several entries fit, keep its sale and mark attribution
  `UNASSIGNED`; show that amount separately. Do not pick a person arbitrarily.
- `products.csv` supplies canonical names/categories by SKU and today's normal
  price. An order's recorded `unit_price` is the price actually agreed at sale;
  promotions may differ from the catalog. SKU is reliable even if the displayed
  product name varies. Do not overwrite a recorded price with today's catalog.

## Sales, discounts, tax, and gift cards

For merchandise, gross sales are quantity times the recorded unit price.
`discount_amount` is a total discount for that line, not a per-unit discount.
Sales before returns are gross less discount. Our training store charges 8%
tax on discounted merchandise, rounded to cents per line using half-up rounding.
`tax_amount` is the recorded tax and `line_total` is discounted sales plus tax.
All latest line arithmetic in these exports is consistent with these rules.
Use integer cents or decimal arithmetic. Do not round only after aggregating.

Recognize fulfilled sales on `ordered_at`. Recognize a succeeded return on
`completed_at`, even when its original sale happened in an earlier month.
For this close, net sales = this month's merchandise sales after discounts
minus merchandise `refund_sales` completed this month. Net units by product
follow the same timing rule. Product and customer sales rankings use this
net-sales definition and exclude sales tax and gift-card issuance. Show both
net units and net sales for best-selling products; rank the sales table by
net sales, so the ranking has a clear meaning. Show unassigned customer sales
separately from the ranked list of known customers.

Gift-card SKU GIFT25 is stored value: selling it raises money and a gift-card
liability but creates no earned sales and no tax. Redeeming an existing gift
card is payment toward merchandise, which earns sales normally. We have no
gift-card refunds in these files. Show issuance and redemption separately;
the period's liability change is issuance minus redemption. You cannot work
out the total outstanding liability without the opening balance, which is
not supplied. A quantity of two gift cards is $50 of issuance.

Each order's amount due is the sum of its latest `line_total`, including tax
and any gift-card purchase. Compare that amount with all captured tenders for
the order, before refunds. A succeeded refund does not make a paid order
unpaid. Show positive shortfalls as unpaid balances and excess captured
amounts as overpayments. Keep unmatched accepted payments in processor cash
totals while flagging them; they are not evidence of another earned sale.

## Money received and expected payout

Show captured card, cash, and redeemed gift-card tender separately using
`payment_at` in the close month. Show succeeded card and cash refunds separately
using `completed_at`. Gift-card redemption brings no new external money.
Net external receipts = captured card plus cash minus succeeded card plus
cash refunds completed in the month. Cash after refunds = captured cash less
succeeded cash refunds. These are receipt movements, not earned sales.

The recorded `fee` is authoritative. This processor charges 2.9% plus $0.30
for each accepted card charge, rounded half-up to cents; declined attempts
and cash/gift-card tenders have zero fees. Refund fees are not automatically
returned. A positive `fee_adjustment` is an explicitly credited fee; use only
what the refund export says. Show card-processing fees for charges accepted
this month. Net receipts after fees subtracts those fees from net external
receipts and adds fee adjustments on returns completed this month.

Expected card payout for the close month follows `settled_at`, which can differ
from sale or payment dates: sum accepted card amounts settled this month,
subtract succeeded card refunds settled this month, subtract the fees attached
to those settled charges, and add fee adjustments attached to those settled
refunds. Include real second charges and unmatched processor charges in this
cash calculation and flag them separately. Show accepted card charges and
completed card refunds that will settle in a later month separately.

There is no bank statement here. This is expected processor payout, not
confirmation of a deposit or reconciliation to the bank. Do not add cash or
gift-card redemption to the expected card payout.

## Review

Keep the source files unchanged. Give us traceable order/payment/refund IDs
for anything needing follow-up, and explain what evidence is missing. An
unassigned customer still counts in store/product totals. A payment mismatch
does not invalidate a supported fulfilled sale. Please show each real order
once in customer order counts; a line, payment attempt, and refund are not
additional orders. Only orders placed in the close month count, so a prior
month's customer can have a refund deduction with zero orders this month.

Sort rankings by net sales descending; ties can be displayed together or by ID
for a stable display.
