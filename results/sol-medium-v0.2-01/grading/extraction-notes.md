# Frozen submission extraction

Only files within this grader workspace were accessed. Submitted solver/verification/refresh code and dashboard JavaScript were not executed. XLSX stored values were read with standard-library ZIP/XML; there are no worksheet formulas. `extract.py` reproduces evidence.json. File hashes in evidence record the frozen submitted artifacts, not independent confirmation of original input preservation.

## Primary metric mapping

- `merchandise_sales_before_refunds` = 108150.50; submitted label “Sales after discounts”; `summary.csv` row 4, workbook `Summary!B4`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.
- `successful_refund_sales` = 799.75; submitted label “Completed merchandise returns”; `summary.csv` row 5, workbook `Summary!B5`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.
- `net_sales` = 107350.75; submitted label “Net sales”; `summary.csv` row 8, workbook `Summary!B8`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.
- `total_successful_refunds` = 863.73; submitted label “Completed refunds incl tax”; `summary.csv` row 18, workbook `Summary!B18`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.
- `card_processing_fees` = 2852.74; submitted label “Card processing fees by payment date”; `summary.csv` row 15, workbook `Summary!B15`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.
- `expected_card_payout` = 84108.06; submitted label “Expected card payout”; `summary.csv` row 27, workbook `Summary!B27`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.
- `net_external_receipts` = 116375.11; submitted label “Net external receipts before fees”; `summary.csv` row 21, workbook `Summary!B21`. Also present in `results.json` metrics and dashboard embedded `const data.metrics`.

## Rows and exact mappings

All report filenames below are relative to `submission/reports/2026-09/`; workbook is `Corner_Loaf_2026-09.xlsx`. CSV row numbers include the header and match worksheet row numbers. Per-order and per-refund provenance is recorded in evidence; exception source locations are attached to individual entries.

- Products: 10 rows, `products_ranked.csv` rows 2–11 / `Products ranked!A2:K11`. SKU A, net sales G, net units K. Both net fields are directly submitted; no aggregation was needed.
- Customers: all 82 rows, `customers_ranked.csv` rows 2–83 / `Customers ranked!A2:G83`. Customer key A, name B, sales C, returns D, net sales E, September order count F, returned-order count G. All submitted summary fields are also preserved under `submitted_summaries`. The diagnostic customers table contains both pools.
- Top customers: 80 identified rows from that full workbook ranking, sorted by submitted net sales descending. This is the largest N actually displayed. Excluded pools: WALK-IN ($20,163.55, 179 orders) and UNRESOLVED ($640.30, 5 orders). Dashboard source specifies `.slice(0,10)` after filtering these pools, and defaults to net sales. No JavaScript was run. Its alternative product view uses gross `units_sold`; the evidence uses explicit workbook `net_units` as required.
- Orders: 1,000 September rows from `order_reconciliation.csv` / `Order reconciliation` (1,029 data rows total); filter submitted `order_in_month=True` (B). Map order_id A, customer_key D, sales F → sales_before_refunds, order_total I → amount_due, accepted_payments J → captured_tenders. Other 29 rows are submitted August orders and excluded. WALK-IN and UNRESOLVED map to NONE: 184 September orders. No payment matching or line recalculation was performed.
- Refunds: all 24 rows, `refund_ledger.csv` rows 2–25 / `Refund ledger!A2:R25`. ID A, refund_sales H, included_in_month O. Deducted sales is H if O=True, otherwise zero, following the submitted `Read me` Returns rule. This is the sole required conditional derivation. There are 17 included refunds and 7 zeros (3 failed, 2 pending, 2 October completions). September-completed refunds settling in October still have their reported merchandise deduction. Included deductions sum to 799.75, agreeing internally with the submitted Completed merchandise returns metric; this is an internal check only.
- Exceptions: 215 separate rows, `action_items.csv` rows 2–216 / `Action items!A2:G216`. IDs B/C/D, amount E, detail F and action G. Semicolon-separated payment IDs become separate IDs within the same entry. Customer candidate IDs in detail are retained in summary, not turned into order/payment/refund IDs. All action rows are actionable as presented, including 179 anonymous-customer checks and 8 declined-attempt checks explicitly asking for replacement-tender review. They are not reclassified as resolved based on reconciliation results. `close_notes.md` Priority checks repeats 28 of these entries; the dashboard priority filter excludes anonymous customers and declined attempts and likewise shows 28. Neither subset is counted again. Dedup audit and timing differences are informational and are not exceptions.

## All readable workbook sheets

- `Summary`: 31 data rows; matching emitted `summary.csv`.
- `Counts`: 4 data rows; matching emitted `counts.csv`.
- `Timing differences`: 39 data rows; matching emitted `timing_differences.csv`.
- `Bridges`: 18 data rows; matching emitted `bridges.csv`.
- `Action items`: 215 data rows; matching emitted `action_items.csv`.
- `Order reconciliation`: 1029 data rows; matching emitted `order_reconciliation.csv`.
- `Order lines`: 2229 data rows; matching emitted `order_lines.csv`.
- `Payment ledger`: 1048 data rows; matching emitted `payment_ledger.csv`.
- `Refund ledger`: 24 data rows; matching emitted `refund_ledger.csv`.
- `Customer matching`: 1029 data rows; matching emitted `customer_matching.csv`.
- `Products ranked`: 10 data rows; matching emitted `products_ranked.csv`.
- `Customers ranked`: 82 data rows; matching emitted `customers_ranked.csv`.
- `Dedup audit`: 29 data rows; matching emitted `dedup_audit.csv`.
- `Source files`: 5 data rows; matching emitted `source_files.csv`.
- `Read me`: 11 data rows; matching emitted `read_me.csv`.

Action-list categories: Unidentified customer: 179, Customer needs review: 5, Unmatched accepted payment: 5, Unpaid order: 6, Overpaid / possible duplicate charge: 4, Underpaid order: 3, Declined payment attempt: 8, Refund failed: 3, Refund pending: 2.

## Agreement, ambiguities, artifacts and omissions

Every cell in the 15 stored workbook tables was compared with its emitted CSV, allowing equivalent numeric formatting and workbook Boolean storage. Every summary metric, product, customer, action, count and bridge CSV field was compared with results.json; the dashboard embedded JSON was compared with results.json. Raw value differences found: 618. All are workbook floating-point storage differences below 0.000000001, with the same displayed cents; no displayed monetary disagreement was found. The complete raw values and cell addresses are preserved in evidence.json display_conflicts.

`close_notes.md` headline amounts and `assistant-response.md` displayed amounts agree with the mapped submitted metrics. The assistant response does not display merchandise returns as a separate headline, but close notes, workbook and dashboard all-metrics data do. Dashboard's default six cards omit that separate return-sales metric, retaining it in embedded all-totals data. Net external receipts maps to the explicitly labeled before-fees amount, 116375.11; the separately reported after-fees-and-credits amount, 113522.67, is preserved under submitted_summaries and is not treated as a contradiction.

Workbook has 15 named sheets and autofilter ranges. Its full order/payment/refund/customer/line/audit detail is present. Dashboard contains an embedded JSON snapshot, empty runtime-rendered table/ranking containers, controls for ranking/checks, and workbook/close-note links. Static data and display instructions were read; browser behavior was not tested. `dashboard_desktop.png` and `dashboard_mobile.png` are present but not used as numeric sources. README describes future-month refresh; refresh was not tested. Source files table has five source names, SHA-256 hashes and byte counts. Original source CSVs are absent, so preservation claims cannot be independently verified here. Artifact and scope_review verdicts remain unverified.

No required submitted metric, product net field, September order field, refund ID or actionable entry was omitted. Exclusions are the 29 August orders from the September-order array, the two customer pools from top_customers, duplicate priority-list presentations, and resolved/informational audit/timing notes from exceptions. No original-input-derived or reference-derived results, scores or correctness claims are included.
