# Retail reconciliation — evaluator answer key

Task: retail-reconciliation; version 0.2; fixture seed 20260930.

Keep this key and the generator out of the solver workspace.
The task has not yet been calibrated against any model.

The JSON beside this file supplies exact cents-rounded expectations, the per-order and per-refund tables, every keyed instance with its checks, and SHA-256 input manifests. Expectations are derived from the source-supported canonical ledger; no model produced these answers.

## Scope and calculations

Close: 2026-09; 1000 current-month orders. Orders export: 2250 rows for 2229 canonical lines, including 2026-08 supporting orders. Payments export: 1054 rows for 1048 payment IDs. Refunds export: 26 rows for 24 refund IDs.

Use the latest version of each line, each payment/refund ID once, and only succeeded refunds completed in the close month. Recorded unit prices are authoritative; SKU identifies the product.

Gross merchandise sales − line discounts − merchandise refunds completed in the close month = net sales. Sales tax and gift-card issuance are separate. Prior-month orders are not close-month sales or receipts, but their close-month returns are deducted.

Orders without a customer ID are attributed only when every supplied clue (email, phone, loyalty card) points to the same single member. No details at all = walk-in. Clues that fit several members or conflict = unassigned and flagged. Explicit IDs are authoritative.

Each order's amount due (all latest line totals, including gift cards) is compared with captured tenders linked by order_id or an order:<id> reference. Amount matches alone are never a link. Distinct accepted charges all count in receipts and payout.

Expected card payout uses settled_at (next business day, skipping weekends and bank holidays): settled card charges less their fees, minus settled succeeded card refunds plus their fee adjustments.

## Metrics

| Metric | Expected |
| --- | ---: |
| `merchandise_gross_sales` | $112,273.70 |
| `discounts` | $4,123.20 |
| `merchandise_sales_before_refunds` | $108,150.50 |
| `successful_refund_sales` | $799.75 |
| `net_sales` | $107,350.75 |
| `sales_tax_charged` | $8,651.96 |
| `successful_refund_tax` | $63.98 |
| `net_sales_tax` | $8,587.98 |
| `gift_card_issued` | $400.00 |
| `gift_card_redeemed` | $85.00 |
| `gift_card_liability_change` | $315.00 |
| `customer_amount_due` | $117,202.46 |
| `captured_card_payments` | $90,454.54 |
| `captured_cash_payments` | $26,784.30 |
| `captured_gift_card_payments` | $85.00 |
| `total_captured_payments` | $117,323.84 |
| `successful_card_refunds` | $719.44 |
| `successful_cash_refunds` | $144.29 |
| `total_successful_refunds` | $863.73 |
| `card_processing_fees` | $2,852.74 |
| `refund_fee_adjustments` | $0.30 |
| `expected_card_payout` | $84,108.06 |
| `prior_month_charges_settled` | $909.03 |
| `card_captures_settling_later` | $3,801.37 |
| `card_refunds_settling_later` | $27.54 |
| `unpaid_order_balance` | $738.14 |
| `overpaid_order_balance` | $592.71 |
| `unmatched_card_payments` | $266.81 |
| `unassigned_customer_net_sales` | $640.30 |
| `walk_in_net_sales` | $20,163.55 |
| `cash_after_refunds` | $26,640.01 |
| `net_external_receipts` | $116,375.11 |
| `net_receipts_after_fees` | $113,522.67 |
| `order_count` | 1000 |

## Products

Gift-card issuance is excluded from this earned-sales ranking.

| SKU | Net units | Net sales |
| --- | ---: | ---: |
| CATER120 | 313 | $36,012.00 |
| CAKE48 | 323 | $14,923.20 |
| CROISSANT21 | 511 | $10,330.95 |
| PIE32 | 311 | $9,667.20 |
| COFFEE18 | 503 | $8,770.50 |
| MUFFIN15 | 514 | $7,441.50 |
| COOKIE12 | 576 | $6,609.60 |
| GRANOLA11 | 523 | $5,557.20 |
| BREAD9 | 617 | $5,378.85 |
| BAGUETTE5 | 551 | $2,659.75 |

## Top customers

| Rank | Customer ID | Name | Orders | Net sales |
| --- | --- | --- | ---: | ---: |
| 1 | C002 | James Chen | 55 | $6,061.50 |
| 2 | C003 | Priya Patel | 55 | $5,971.80 |
| 3 | C004 | Daniel Okafor | 50 | $5,749.70 |
| 4 | C005 | Aisha Rahman | 49 | $5,132.05 |
| 5 | C009 | Grace Kim | 33 | $3,805.65 |
| 6 | C001 | Maria Lopez | 41 | $3,788.25 |
| 7 | C006 | Tom Walsh | 21 | $3,356.10 |
| 8 | C013 | Nina Petrov | 25 | $3,044.05 |
| 9 | C011 | Hannah Brooks | 30 | $2,635.90 |
| 10 | C010 | Omar Haddad | 27 | $2,490.35 |

All customer rows, including the walk-in and unassigned buckets, are in the JSON. Equal-value ties can be displayed in either order.

## Keyed instances

118 instances across 28 types; 26 require a flag. An instance passes when every listed per-order/per-refund value matches and, if a flag is required, one of its anchor IDs appears in the submitted exception list. `resolve` = enough evidence for a specific answer; `review` = keep the supported amount visible and flag it; `preserve` = keep valid records as they are.

| Type | Count |
| --- | ---: |
| `ambiguous-household` | 3 |
| `cash-refund` | 3 |
| `coincidental-amount` | 2 |
| `conflicting-contacts` | 2 |
| `declined-then-captured` | 5 |
| `double-charge` | 4 |
| `duplicate-export` | 16 |
| `gift-card-redemption` | 5 |
| `gift-card-sale` | 6 |
| `household-members` | 3 |
| `id-from-email` | 4 |
| `id-from-loyalty-card` | 3 |
| `id-from-phone` | 2 |
| `label-variant` | 5 |
| `line-edit` | 8 |
| `missing-payment` | 4 |
| `partial-refund` | 5 |
| `prior-month-return` | 3 |
| `promotional-price` | 5 |
| `reference-link` | 5 |
| `refund-not-paid` | 5 |
| `refund-on-edited-line` | 2 |
| `refund-timing` | 4 |
| `repeat-purchase` | 4 |
| `same-name` | 1 |
| `short-payment` | 3 |
| `two-card-split` | 3 |
| `unlinked-charge` | 3 |

| Instance | Kind | Flag | Records | Expected behavior |
| --- | --- | --- | --- | --- |
| `line-edit-01` | resolve |  | `O-202609-0674` | Use only the latest version (v2) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-02` | resolve |  | `O-202609-0391` | Use only the latest version (v2) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-03` | resolve |  | `O-202609-0050` | Use only the latest version (v2) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-04` | resolve |  | `O-202609-0669` | Use only the latest version (v2) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-05` | resolve |  | `O-202609-0082` | Use only the latest version (v2) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-06` | resolve |  | `O-202609-0100` | Use only the latest version (v2) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-07` | resolve |  | `O-202609-0171` | Use only the latest version (v3) of the edited line; older versions are replaced, not additional sales. |
| `line-edit-08` | resolve |  | `O-202609-0456` | Use only the latest version (v3) of the edited line; older versions are replaced, not additional sales. |
| `label-variant-01` | resolve |  | `O-202609-0906`, `C031` | Aggregate under C031 and PIE32 despite display-label variants; no new customer or product. |
| `label-variant-02` | resolve |  | `O-202609-0711`, `C052` | Aggregate under C052 and CROISSANT21 despite display-label variants; no new customer or product. |
| `label-variant-03` | resolve |  | `O-202609-0548`, `C046` | Aggregate under C046 and GRANOLA11 despite display-label variants; no new customer or product. |
| `label-variant-04` | resolve |  | `O-202609-0624`, `C013` | Aggregate under C013 and MUFFIN15 despite display-label variants; no new customer or product. |
| `label-variant-05` | resolve |  | `O-202609-0877`, `C044` | Aggregate under C044 and MUFFIN15 despite display-label variants; no new customer or product. |
| `promotional-price-01` | preserve |  | `O-202609-0218` | Keep the recorded CROISSANT21 price of $16.80; do not replace it with the catalog price. |
| `promotional-price-02` | preserve |  | `O-202609-0891` | Keep the recorded COOKIE12 price of $10.20; do not replace it with the catalog price. |
| `promotional-price-03` | preserve |  | `O-202609-0850` | Keep the recorded CROISSANT21 price of $17.85; do not replace it with the catalog price. |
| `promotional-price-04` | preserve |  | `O-202609-0892` | Keep the recorded MUFFIN15 price of $12.00; do not replace it with the catalog price. |
| `promotional-price-05` | preserve |  | `O-202609-0319` | Keep the recorded CATER120 price of $90.00; do not replace it with the catalog price. |
| `gift-card-sale-01` | resolve |  | `O-202609-0942` | Record $25.00 as gift-card issuance with no sales or tax; it is still money received and part of the amount due. |
| `gift-card-sale-02` | resolve |  | `O-202609-0628` | Record $100.00 as gift-card issuance with no sales or tax; it is still money received and part of the amount due. |
| `gift-card-sale-03` | resolve |  | `O-202609-0104` | Record $100.00 as gift-card issuance with no sales or tax; it is still money received and part of the amount due. |
| `gift-card-sale-04` | resolve |  | `O-202609-0752` | Record $50.00 as gift-card issuance with no sales or tax; it is still money received and part of the amount due. |
| `gift-card-sale-05` | resolve |  | `O-202609-0762` | Record $25.00 as gift-card issuance with no sales or tax; it is still money received and part of the amount due. |
| `gift-card-sale-06` | resolve |  | `O-202609-0084` | Record $100.00 as gift-card issuance with no sales or tax; it is still money received and part of the amount due. |
| `gift-card-redemption-01` | resolve |  | `O-202609-0805` | The $15.00 gift-card redemption pays for merchandise; it is not new external money. Order is fully paid. |
| `gift-card-redemption-02` | resolve |  | `O-202609-0855` | The $10.00 gift-card redemption pays for merchandise; it is not new external money. Order is fully paid. |
| `gift-card-redemption-03` | resolve |  | `O-202609-0639` | The $25.00 gift-card redemption pays for merchandise; it is not new external money. Order is fully paid. |
| `gift-card-redemption-04` | resolve |  | `O-202609-0644` | The $25.00 gift-card redemption pays for merchandise; it is not new external money. Order is fully paid. |
| `gift-card-redemption-05` | resolve |  | `O-202609-0499` | The $10.00 gift-card redemption pays for merchandise; it is not new external money. Order is fully paid. |
| `declined-then-captured-01` | resolve |  | `O-202609-0435`, `P-202609-0441`, `P-202609-0442` | Declined attempts take no money and carry no fee; the accepted charge pays the order once. |
| `declined-then-captured-02` | resolve |  | `O-202609-0690`, `P-202609-0703`, `P-202609-0704` | Declined attempts take no money and carry no fee; the accepted charge pays the order once. |
| `declined-then-captured-03` | resolve |  | `O-202609-0098`, `P-202609-0100`, `P-202609-0101`, `P-202609-0102` | Declined attempts take no money and carry no fee; the accepted charge pays the order once. |
| `declined-then-captured-04` | resolve |  | `O-202609-0072`, `P-202609-0073`, `P-202609-0074` | Declined attempts take no money and carry no fee; the accepted charge pays the order once. |
| `declined-then-captured-05` | resolve |  | `O-202609-0625`, `P-202609-0635`, `P-202609-0636` | Declined attempts take no money and carry no fee; the accepted charge pays the order once. |
| `double-charge-01` | review | yes | `O-202609-0424`, `P-202609-0430`, `P-202609-0431` | Keep both accepted charges in receipts and payout and count the sale once; flag the $31.75 overpayment for the owner. Do not delete or invent a refund. |
| `double-charge-02` | review | yes | `O-202609-0928`, `P-202609-0946`, `P-202609-0947` | Keep both accepted charges in receipts and payout and count the sale once; flag the $343.66 overpayment for the owner. Do not delete or invent a refund. |
| `double-charge-03` | review | yes | `O-202609-0813`, `P-202609-0828`, `P-202609-0829` | Keep both accepted charges in receipts and payout and count the sale once; flag the $96.12 overpayment for the owner. Do not delete or invent a refund. |
| `double-charge-04` | review | yes | `O-202609-0142`, `P-202609-0145`, `P-202609-0185` | Keep both accepted charges in receipts and payout and count the sale once; flag the $121.18 overpayment for the owner. Do not delete or invent a refund. |
| `two-card-split-01` | preserve |  | `O-202609-0832`, `P-202609-0848`, `P-202609-0849` | Two accepted charges add up to the amount due; the order is paid exactly, not double-charged. |
| `two-card-split-02` | preserve |  | `O-202609-0594`, `P-202609-0604`, `P-202609-0603` | Two accepted charges add up to the amount due; the order is paid exactly, not double-charged. |
| `two-card-split-03` | preserve |  | `O-202609-0223`, `P-202609-0228`, `P-202609-0227` | Two accepted charges add up to the amount due; the order is paid exactly, not double-charged. |
| `missing-payment-01` | review | yes | `O-202609-0230` | Keep the sale and flag the $90.72 amount due as unpaid; do not invent a payment. |
| `missing-payment-02` | review | yes | `O-202609-0244` | Keep the sale and flag the $61.56 amount due as unpaid; do not invent a payment. |
| `missing-payment-03` | review | yes | `O-202609-0527`, `P-202609-0536` | Keep the sale and flag the $176.90 amount due as unpaid; do not invent a payment. |
| `missing-payment-04` | review | yes | `O-202609-0510`, `P-202609-0519` | Keep the sale and flag the $267.84 amount due as unpaid; do not invent a payment. |
| `short-payment-01` | review | yes | `O-202609-0493`, `P-202609-0501` | Keep the sale and flag the $5.00 unpaid balance. |
| `short-payment-02` | review | yes | `O-202609-0409`, `P-202609-0414` | Keep the sale and flag the $5.00 unpaid balance. |
| `short-payment-03` | review | yes | `O-202609-0851`, `P-202609-0868` | Keep the sale and flag the $8.00 unpaid balance. |
| `reference-link-01` | resolve |  | `O-202609-0554`, `P-202609-0563` | Link the charge to the order through its order:<order_id> reference; it is not unmatched. |
| `reference-link-02` | resolve |  | `O-202609-0532`, `P-202609-0541` | Link the charge to the order through its order:<order_id> reference; it is not unmatched. |
| `reference-link-03` | resolve |  | `O-202609-0844`, `P-202609-0861` | Link the charge to the order through its order:<order_id> reference; it is not unmatched. |
| `reference-link-04` | resolve |  | `O-202609-0571`, `P-202609-0581` | Link the charge to the order through its order:<order_id> reference; it is not unmatched. |
| `reference-link-05` | resolve |  | `O-202609-0505`, `P-202609-0514` | Link the charge to the order through its order:<order_id> reference; it is not unmatched. |
| `unlinked-charge-01` | review | yes | `P-202609-0249` | Keep the $38.43 charge and its fee in card receipts and payout, create no sale, and flag it. |
| `unlinked-charge-02` | review | yes | `P-202609-0052` | Keep the $37.97 charge and its fee in card receipts and payout, create no sale, and flag it. |
| `unlinked-charge-03` | review | yes | `P-202609-0452` | Keep the $67.29 charge and its fee in card receipts and payout, create no sale, and flag it. |
| `coincidental-amount-01` | review | yes | `O-202609-0299`, `P-202609-0376` | The amounts match but nothing links the charge to the order. Keep the order unpaid and the charge unmatched, and flag both for the owner to confirm. |
| `coincidental-amount-02` | review | yes | `O-202609-0101`, `P-202609-0292` | The amounts match but nothing links the charge to the order. Keep the order unpaid and the charge unmatched, and flag both for the owner to confirm. |
| `partial-refund-01` | resolve |  | `O-202609-0068`, `R-202609-003` | Deduct only the returned quantity: $10.00 sales and $0.80 tax; the rest of the order stays sold. |
| `partial-refund-02` | resolve |  | `O-202609-0095`, `R-202609-004` | Deduct only the returned quantity: $5.00 sales and $0.40 tax; the rest of the order stays sold. |
| `partial-refund-03` | resolve |  | `O-202609-0342`, `R-202609-010` | Deduct only the returned quantity: $4.25 sales and $0.34 tax; the rest of the order stays sold. |
| `partial-refund-04` | resolve |  | `O-202609-0366`, `R-202609-012` | Deduct only the returned quantity: $24.00 sales and $1.92 tax; the rest of the order stays sold. |
| `partial-refund-05` | resolve |  | `O-202609-0006`, `R-202609-002` | Deduct only the returned quantity: $16.20 sales and $1.29 tax; the rest of the order stays sold. |
| `cash-refund-01` | resolve |  | `O-202609-0637`, `R-202609-019` | Deduct $12.75 sales; the $13.77 cash refund reduces cash, not the card payout. |
| `cash-refund-02` | resolve |  | `O-202609-0682`, `R-202609-017` | Deduct $48.60 sales; the $52.49 cash refund reduces cash, not the card payout. |
| `cash-refund-03` | resolve |  | `O-202609-0402`, `R-202609-015` | Deduct $63.00 sales; the $68.04 cash refund reduces cash, not the card payout. |
| `refund-not-paid-01` | review | yes | `O-202609-0074`, `R-202609-005` | The failed $40.82 refund moved no money and does not reduce sales or units; flag it for follow-up. |
| `refund-not-paid-02` | review | yes | `O-202609-0665`, `R-202609-020` | The failed $11.88 refund moved no money and does not reduce sales or units; flag it for follow-up. |
| `refund-not-paid-03` | review | yes | `O-202609-0144`, `R-202609-007` | The failed $38.55 refund moved no money and does not reduce sales or units; flag it for follow-up. |
| `refund-not-paid-04` | review | yes | `O-202609-0311`, `R-202609-011` | The pending $11.66 refund moved no money and does not reduce sales or units; flag it for follow-up. |
| `refund-not-paid-05` | review | yes | `O-202609-0601`, `R-202609-016` | The pending $19.44 refund moved no money and does not reduce sales or units; flag it for follow-up. |
| `refund-timing-01` | resolve |  | `O-202609-0724`, `R-202609-021` | Completed in 2026-09: deduct $13.50 sales and count the refund as paid out, but it settles 2026-10-01 so it is outside 2026-09's expected payout. |
| `refund-timing-02` | resolve |  | `O-202609-0694`, `R-202609-022` | Completed in 2026-09: deduct $12.00 sales and count the refund as paid out, but it settles 2026-10-01 so it is outside 2026-09's expected payout. |
| `refund-timing-03` | resolve |  | `O-202609-0787`, `R-202609-024` | Completed in 2026-10: no 2026-09 sales deduction, refund paid out or payout effect. |
| `refund-timing-04` | resolve |  | `O-202609-0738`, `R-202609-023` | Completed in 2026-10: no 2026-09 sales deduction, refund paid out or payout effect. |
| `prior-month-return-01` | resolve |  | `O-202608-0433`, `R-202609-009` | The original 2026-08 sale and charge are not 2026-09 activity, but the $240.00 return completed in 2026-09 reduces 2026-09 net sales. |
| `prior-month-return-02` | resolve |  | `O-202608-0762`, `R-202609-008` | The original 2026-08 sale and charge are not 2026-09 activity, but the $96.00 return completed in 2026-09 reduces 2026-09 net sales. |
| `prior-month-return-03` | resolve |  | `O-202608-0406`, `R-202609-001` | The original 2026-08 sale and charge are not 2026-09 activity, but the $216.00 return completed in 2026-09 reduces 2026-09 net sales. |
| `refund-on-edited-line-01` | resolve |  | `O-202609-0706`, `R-202609-018` | The refund applies to the latest line version; deduct $10.80 sales once. |
| `refund-on-edited-line-02` | resolve |  | `O-202609-0394`, `R-202609-014` | The refund applies to the latest line version; deduct $8.10 sales once. |
| `duplicate-export-01` | resolve |  | `O-202609-0172`, `R-202609-006` | Count the refund ID once: $15.30 sales. |
| `duplicate-export-02` | resolve |  | `O-202609-0338`, `R-202609-013` | Count the refund ID once: $4.25 sales. |
| `id-from-email-01` | resolve |  | `O-202609-0503`, `C001` | The email matches exactly one loyalty member; attribute the order to C001. |
| `id-from-email-02` | resolve |  | `O-202609-0485`, `C040` | The email matches exactly one loyalty member; attribute the order to C040. |
| `id-from-email-03` | resolve |  | `O-202609-0924`, `C003` | The email matches exactly one loyalty member; attribute the order to C003. |
| `id-from-email-04` | resolve |  | `O-202609-0615`, `C010` | The email matches exactly one loyalty member; attribute the order to C010. |
| `id-from-loyalty-card-01` | resolve |  | `O-202609-0149`, `C009` | The noted loyalty card identifies C009. |
| `id-from-loyalty-card-02` | resolve |  | `O-202609-0145`, `C029` | The noted loyalty card identifies C029. |
| `id-from-loyalty-card-03` | resolve |  | `O-202609-0069`, `C046` | The noted loyalty card identifies C046. |
| `id-from-phone-01` | resolve |  | `O-202609-0122`, `C002` | The email matches no one; the phone number uniquely identifies C002. |
| `id-from-phone-02` | resolve |  | `O-202609-0256`, `C012` | The email matches no one; the phone number uniquely identifies C012. |
| `ambiguous-household-01` | review | yes | `O-202609-0174`, `C014`, `C015` | The contacts fit both C014 and C015. Keep the sale but leave it unassigned and flag it. |
| `ambiguous-household-02` | review | yes | `O-202609-0841`, `C041`, `C042` | The contacts fit both C041 and C042. Keep the sale but leave it unassigned and flag it. |
| `ambiguous-household-03` | review | yes | `O-202609-0180`, `C063`, `C064` | The contacts fit both C063 and C064. Keep the sale but leave it unassigned and flag it. |
| `conflicting-contacts-01` | review | yes | `O-202609-0560`, `C003`, `C070` | The email matches C003 but the phone matches C070. Leave it unassigned and flag it. |
| `conflicting-contacts-02` | review | yes | `O-202609-0027`, `C065`, `C055` | The email matches C065 but the phone matches C055. Leave it unassigned and flag it. |
| `household-members-01` | preserve |  | `O-202609-0213`, `O-202609-0852`, `C014`, `C015` | Explicit IDs keep C014 and C015 separate despite shared contacts. |
| `household-members-02` | preserve |  | `O-202609-0215`, `O-202609-0742`, `C041`, `C042` | Explicit IDs keep C041 and C042 separate despite shared contacts. |
| `household-members-03` | preserve |  | `O-202609-0165`, `O-202609-0511`, `C063`, `C064` | Explicit IDs keep C063 and C064 separate despite shared contacts. |
| `same-name-01` | preserve |  | `O-202609-0382`, `O-202609-0747`, `C027`, `C058` | C027 and C058 are different people with different contacts; do not merge. |
| `repeat-purchase-01` | preserve |  | `O-202609-0857`, `O-202609-0858` | Two order numbers, each separately paid: two real purchases. Keep both. |
| `repeat-purchase-02` | preserve |  | `O-202609-0613`, `O-202609-0614` | Two order numbers, each separately paid: two real purchases. Keep both. |
| `repeat-purchase-03` | preserve |  | `O-202609-0400`, `O-202609-0403` | Two order numbers, each separately paid: two real purchases. Keep both. |
| `repeat-purchase-04` | preserve |  | `O-202609-0518`, `O-202609-0519` | Two order numbers, each separately paid: two real purchases. Keep both. |
| `duplicate-export-03` | resolve |  | `O-202609-0977` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-04` | resolve |  | `O-202609-0177` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-05` | resolve |  | `O-202609-0753` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-06` | resolve |  | `O-202609-0800` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-07` | resolve |  | `O-202609-0875` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-08` | resolve |  | `O-202609-0675` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-09` | resolve |  | `O-202609-0743` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-10` | resolve |  | `O-202609-0496` | Count each line once; the repeated rows are the same line, not more sales. |
| `duplicate-export-11` | resolve |  | `O-202609-0349`, `P-202609-0354` | Count the payment ID once; it is a repeated export, not a second charge. |
| `duplicate-export-12` | resolve |  | `O-202609-0758`, `P-202609-0773` | Count the payment ID once; it is a repeated export, not a second charge. |
| `duplicate-export-13` | resolve |  | `O-202609-0117`, `P-202609-0120` | Count the payment ID once; it is a repeated export, not a second charge. |
| `duplicate-export-14` | resolve |  | `O-202609-0462`, `P-202609-0470` | Count the payment ID once; it is a repeated export, not a second charge. |
| `duplicate-export-15` | resolve |  | `O-202609-0778`, `P-202609-0792` | Count the payment ID once; it is a repeated export, not a second charge. |
| `duplicate-export-16` | resolve |  | `O-202609-0375`, `P-202609-0380` | Count the payment ID once; it is a repeated export, not a second charge. |

## Fixture integrity

The generator checks latest versions, exact duplicate IDs, all line, fee and refund arithmetic, cross-file references, product/customer totals, distinct customer order counts, the tender-to-order reconciliation bridge, unique instance anchors, each instance's intended outcome, and that no exported note labels a trap. Regeneration with the same seed is byte-for-byte deterministic. Use `python3 tasks/retail-reconciliation/generate.py --output-root /tmp/retail-fixture-check` to regenerate elsewhere, and `--seed N` for an alternate fixture with its own key.
