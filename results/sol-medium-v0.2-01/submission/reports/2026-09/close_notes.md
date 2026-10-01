# Corner Loaf Bakery — 2026-09 close

Sales after discounts: **$108,150.50**. Completed merchandise returns: **$799.75**. Net sales: **$107,350.75**.

Completed refunds including tax: **$863.73**. Card charge fees by payment date: **$2,852.74**. Net external receipts before fees: **$116,375.11**. Expected card payout: **$84,108.06**. The payout is an expectation; there is no bank statement to confirm deposits.

## Why totals differ

Sales exclude tax and gift-card sales. Gift-card redemption pays for an order but brings in no new money. Refund totals include returned tax; only the merchandise portion reduces net sales. Returns of earlier orders reduce this month's sales. Declined attempts and failed/pending refunds do not count as money movements. Card payouts use settlement dates, including earlier charges and excluding charges or refunds settling next month. See the workbook Bridges sheet for the exact arithmetic.

29 overlapping or superseded export rows were removed. Distinct payment IDs remain money movements even when they look like repeated charges. They are flagged for review rather than silently removed.

## Priority checks

### Unpaid order

- O-202609-0101   — $68.04. Order due 68.04; accepted tenders 0. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0230   — $90.72. Order due 90.72; accepted tenders 0. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0244   — $61.56. Order due 61.56; accepted tenders 0. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0299   — $55.08. Order due 55.08; accepted tenders 0. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0510   — $267.84. Order due 267.84; accepted tenders 0. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0527   — $176.90. Order due 176.90; accepted tenders 0. Check receipt and tender history; standalone charges remain unmatched until confirmed.

### Underpaid order

- O-202609-0409 P-202609-0414  — $5.00. Order due 146.45; accepted tenders 141.45. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0493 P-202609-0501  — $5.00. Order due 188.14; accepted tenders 183.14. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0851 P-202609-0868  — $8.00. Order due 167.99; accepted tenders 159.99. Check receipt and tender history; standalone charges remain unmatched until confirmed.

### Overpaid / possible duplicate charge

- O-202609-0142 P-202609-0145; P-202609-0185  — $121.18. Order due 121.18; accepted tenders 242.36. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0424 P-202609-0430; P-202609-0431  — $31.75. Order due 31.75; accepted tenders 63.50. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0813 P-202609-0828; P-202609-0829  — $96.12. Order due 96.12; accepted tenders 192.24. Check receipt and tender history; standalone charges remain unmatched until confirmed.
- O-202609-0928 P-202609-0946; P-202609-0947  — $343.66. Order due 343.66; accepted tenders 687.32. Check receipt and tender history; standalone charges remain unmatched until confirmed.

### Unmatched accepted payment

-  P-202609-0052  — $37.97. terminal:1dc2cd Find terminal receipt / order number. Amount retained in receipts and payout; no guessed match.
-  P-202609-0249  — $38.43. terminal:38c628 Find terminal receipt / order number. Amount retained in receipts and payout; no guessed match.
-  P-202609-0292  — $68.04. terminal:6c474e Find terminal receipt / order number. Amount retained in receipts and payout; no guessed match.
-  P-202609-0376  — $55.08. terminal:2a11a2 Find terminal receipt / order number. Amount retained in receipts and payout; no guessed match.
-  P-202609-0452  — $67.29. terminal:d6e8fc Find terminal receipt / order number. Amount retained in receipts and payout; no guessed match.

### Refund failed

- O-202609-0074  R-202609-005 — $40.82. Excluded from completed refunds. Check processor status; retry or complete only after confirming no successful refund.
- O-202609-0144  R-202609-007 — $38.55. Excluded from completed refunds. Check processor status; retry or complete only after confirming no successful refund.
- O-202609-0665  R-202609-020 — $11.88. Excluded from completed refunds. Check processor status; retry or complete only after confirming no successful refund.

### Refund pending

- O-202609-0311  R-202609-011 — $11.66. Excluded from completed refunds. Check processor status; retry or complete only after confirming no successful refund.
- O-202609-0601  R-202609-016 — $19.44. Excluded from completed refunds. Check processor status; retry or complete only after confirming no successful refund.

### Customer needs review

- O-202609-0027   — $235.65. Conflicting contacts; candidates C055; C065 Add a loyalty ID if available; do not merge household members by shared contacts.
- O-202609-0174   — $74.20. Shared household contact; person ambiguous; candidates C014; C015 Add a loyalty ID if available; do not merge household members by shared contacts.
- O-202609-0180   — $108.00. Shared household contact; person ambiguous; candidates C063; C064 Add a loyalty ID if available; do not merge household members by shared contacts.
- O-202609-0560   — $96.00. Conflicting contacts; candidates C003; C070 Add a loyalty ID if available; do not merge household members by shared contacts.
- O-202609-0841   — $126.45. Shared household contact; person ambiguous; candidates C041; C042 Add a loyalty ID if available; do not merge household members by shared contacts.

## Missing information

Bank statements or processor deposit records are needed to verify actual deposits. Terminal receipts are needed to connect standalone payments to orders. Customer IDs or loyalty evidence are needed for unresolved contacts and anonymous walk-ins. Processor follow-up is needed for failed/pending refunds. The opening gift-card balance is needed for the ending liability; till counts and cash deposits are needed to confirm cash on hand or banked cash.

See Action items for every affected order, including anonymous sales and declined attempts. Customer pools are excluded from the biggest-person ranking on the dashboard.
