# Retail reconciliation — evaluator answer key

Task: retail-reconciliation; version 0.1; fixture seed 20260930.

Keep this key and the generator out of the solver workspace.
The task is newly authored and has not been run or calibrated against any model.

The JSON beside this file supplies exact cents-rounded expectations and SHA-256 input manifests.
Expectations are derived from the source-supported canonical ledger; no model produced these answers.

## Scope and calculations

Close: 2026-09; 100 real current-month orders. Orders export: 210 rows for 205 canonical lines (including two prior-month supporting lines).

The bookkeeper notes are the authority for period, rounding, source keys, sales/tender treatment, and settlement timing. Use the latest order-line version, unique payment/refund IDs, and only succeeded refunds. The SKU catalog identifies category and canonical display name; recorded unit prices remain authoritative.

Gross merchandise sales − line discounts − succeeded merchandise refunds completed in the close month = net sales. Sales tax and gift-card issuance are separate. Net units subtract only completed succeeded refund quantities. The prior-month sale is excluded; its current-month return is included.

Customer order counts count distinct fulfilled current-month order IDs, including a gift-card-only order. Customer net sales exclude gift-card issuance and tax and include current-month refund deductions. Missing-ID orders are matched only on unique evidence; the shared Alex Morgan household order stays UNASSIGNED. The unassigned bucket is included in the customer table so totals reconcile. Every legitimate loyalty-register customer is included, with zero orders and zero net sales when inactive; retaining an inactive roster entry is correct.

Compare original order amount due with captured tenders before returns. A refund does not reopen the customer's original amount due. Keep distinct actual charges in processor receipts, even when an order is overpaid. An unmatched processor charge affects cash/payout but never creates an unsupported sale.

Expected card payout uses settled_at: captured card amount less its fee, minus succeeded settled card refunds, plus their explicit fee adjustments. Cash, gift-card tenders, and unsettled transactions are excluded. There is no bank statement, opening gift-card balance, or evidence authorizing automatic refunds.

## Metrics

| Metric | Expected |
| --- | ---: |
| `merchandise_gross_sales` | $9,039.00 |
| `discounts` | $330.30 |
| `merchandise_sales_before_refunds` | $8,708.70 |
| `successful_refund_sales` | $92.10 |
| `net_sales` | $8,616.60 |
| `sales_tax_charged` | $696.73 |
| `successful_refund_tax` | $7.37 |
| `net_sales_tax` | $689.36 |
| `gift_card_issued` | $200.00 |
| `gift_card_redeemed` | $109.72 |
| `gift_card_liability_change` | $90.28 |
| `customer_amount_due` | $9,605.43 |
| `captured_card_payments` | $8,454.59 |
| `captured_cash_payments` | $1,169.64 |
| `captured_gift_card_payments` | $109.72 |
| `total_captured_payments` | $9,733.95 |
| `successful_card_refunds` | $86.51 |
| `successful_cash_refunds` | $12.96 |
| `total_successful_refunds` | $99.47 |
| `card_processing_fees` | $271.31 |
| `refund_fee_adjustments` | $0.30 |
| `expected_card_payout` | $8,060.18 |
| `card_captures_settling_later` | $58.32 |
| `card_refunds_settling_later` | $19.44 |
| `unpaid_order_balance` | $48.60 |
| `overpaid_order_balance` | $139.32 |
| `unmatched_card_payments` | $37.80 |
| `unassigned_customer_net_sales` | $33.00 |
| `cash_after_refunds` | $1,156.68 |
| `net_external_receipts` | $9,524.76 |
| `net_receipts_after_fees` | $9,253.75 |
| `order_count` | 100 |

## Products

Gift-card issuance is excluded from this earned-sales ranking.

| SKU | Net units | Net sales |
| --- | ---: | ---: |
| CATER120 | 29 | $3,336.00 |
| CAKE48 | 28 | $1,322.40 |
| CROISSANT21 | 63 | $1,257.90 |
| COFFEE18 | 64 | $1,103.10 |
| COOKIE12 | 77 | $891.60 |
| BREAD9 | 80 | $705.60 |

## Top customers

| Rank | Customer ID | Name | Orders | Net sales |
| --- | --- | --- | ---: | ---: |
| 1 | C002 | James Chen | 15 | $1,310.70 |
| 2 | C023 | Ivy Reed | 8 | $997.20 |
| 3 | C001 | Maria Lopez | 9 | $819.75 |
| 4 | C014 | Alex Morgan | 5 | $489.00 |
| 5 | C006 | Tom Walsh | 5 | $434.25 |
| 6 | C003 | Priya Patel | 5 | $383.70 |
| 7 | C011 | Hannah Brooks | 4 | $320.55 |
| 8 | C012 | Victor Nguyen | 4 | $316.80 |
| 9 | C027 | Zara Khan | 3 | $306.60 |
| 10 | C018 | Marcus Bell | 3 | $257.70 |

All customer rows, including the unassigned bucket, are in the JSON. Equal-value ties can be displayed in either order.

## Evidence-backed cases

A `resolve` case has sufficient evidence for a specific answer; merely flagging it does not demonstrate resolution. A `review` case must remain visible with the supported amount and record IDs. A `preserve` case checks that the solver retains valid records or prices instead of manufacturing a correction.

### latest-line-version — Amended order line (resolve)

Records: `O-202609-001-L01`.

Use version 2 (two loaves) once; discard version 1, which has one loaf.

### legitimate-repeat — Similar repeat purchases (preserve)

Records: `O-202609-002`, `O-202609-003`.

Retain both order IDs, each with its own captured payment; these are two real purchases.

### failed-authorization — Declined attempt followed by payment (resolve)

Records: `O-202609-004`, `P-202609-004`, `P-202609-005`.

Count the captured payment and its fee once; do not count the declined attempt as receipts or an overpayment.

### split-tender — Gift-card and card split tender (resolve)

Records: `O-202609-005`, `P-202609-006`, `P-202609-007`.

Keep merchandise sales of $66.00; the $25.00 gift-card redemption is a tender, not additional external receipts or sales.

### gift-card-issuance — Selling stored value (resolve)

Records: `O-202609-006`.

Record $50.00 as gift-card issuance and accepted card receipts, with zero earned sales and zero tax.

### actual-double-charge — Two actual captured transactions (review)

Records: `O-202609-007`, `P-202609-009`, `P-202609-010`.

Retain both distinct captured payment IDs in cash and payout totals, count the sale once, and flag the $139.32 excess charge. Do not silently delete or refund it.

### missing-payment — Fulfilled order without a payment (review)

Records: `O-202609-008`.

Keep $45.00 earned sales and flag the $48.60 amount due as unsupported by a captured tender. Do not invent a payment or remove the sale.

### partial-refund — Discounted partial line return (resolve)

Records: `O-202609-009`, `O-202609-009-L01`, `R-202609-001`.

Deduct one croissant box, $18.90 sales and $1.51 tax; the other two boxes and cake remain sold. The $0.30 fee adjustment is an explicit processor credit.

### unpaid-refund-requests — Failed and pending returns (review)

Records: `O-202609-010`, `R-202609-002`, `R-202609-003`.

Flag the failed $9.72 and pending $51.84 refund requests for follow-up; neither changes units, sales, receipts, or payout until succeeded.

### settlement-cutoff — Month-end charge settles next month (resolve)

Records: `O-202609-011`, `P-202609-013`.

Count $54.00 sales and $58.32 accepted card receipts in 2026-09, but exclude this charge and its $1.99 fee from that month's payout; settlement is 2026-10-02.

### shared-household — Two people share a name and contacts (preserve)

Records: `C014`, `C015`, `O-202609-012`, `O-202609-013`.

Preserve C014 and C015 as separate customers despite identical Alex Morgan name/email/phone; explicit customer IDs determine attribution.

### supported-customer-link — Recoverable missing loyalty ID (resolve)

Records: `O-202609-014`, `C003`.

Assign C003 using the unique customer email and the matching CL-0003 loyalty reference; normalize its display name without creating an extra customer.

### ambiguous-customer — Missing ID with shared household contacts (review)

Records: `O-202609-015`, `C014`, `C015`.

Keep $33.00 in store and product net sales but attribute it to UNASSIGNED; flag that C014 versus C015 cannot be established from these files.

### stable-identity — Checkout and product label variants (resolve)

Records: `O-202609-016`, `C001`, `BREAD9`.

Use C001 and BREAD9 for aggregation despite display label variants; do not create duplicate customer or product categories.

### cash-return — Cash purchase and item refund (resolve)

Records: `O-202609-017`, `R-202609-004`.

Include the $12.96 cash refund in cash-after-refunds and the $12.00 sales reduction; exclude all cash from card payout.

### recorded-promotion — Recorded promotional price and discount (preserve)

Records: `O-202609-018`.

Keep the recorded $16.50 coffee price instead of replacing it with the $18.00 catalog price, and apply the $2.10 croissant line discount once.

### payment-reference — Payment missing the usual order field (resolve)

Records: `O-202609-019`, `P-202609-021`.

Recover the exact order link from reference order:<order_id>; this payment is supported, not unmatched.

### refund-settlement-cutoff — Completed return settles next month (resolve)

Records: `O-202609-020`, `R-202609-005`.

Deduct $18.00 sales and $19.44 card refund receipts in 2026-09; exclude this refund from that month's payout because settlement is 2026-10-02.

### prior-month-return — Return from a prior month's sale (resolve)

Records: `O-202609-000`, `R-202609-006`.

Exclude the original 2026-08 order and charge from 2026-09 sales/receipts, but deduct the succeeded $43.20 sales/$3.46 tax return completed and settled in 2026-09.

### unmatched-processor-charge — Accepted processor charge without an order (review)

Records: `P-202609-024`.

Include the real $37.80 accepted charge and its $1.40 fee in processor receipt/payout totals; flag the missing order evidence without inventing earned sales.

### duplicate-exports — Repeated exports across all transaction files (resolve)

Records: `O-202609-002-L02`, `O-202609-010-L01`, `O-202609-015-L02`, `O-202609-099-L02`, `P-202609-003`, `P-202609-010`, `P-202609-019`, `R-202609-001`.

Count repeated same-ID rows once in orders, payments, and refunds. Do not confuse repeated exports with distinct captured charges or real repeat order IDs.

## Fixture integrity

The generator checks latest versions, exact duplicate IDs, all line and refund arithmetic, cross-file references, product/customer totals, distinct customer order counts, open/overpaid balances, and the tender-to-order reconciliation bridge. Default-seed regeneration must be byte-for-byte deterministic, including answer keys. Use `python3 tasks/retail-reconciliation/generate.py --output-root /tmp/retail-fixture-check` to regenerate elsewhere.
