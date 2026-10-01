# Corner Loaf monthly close

Start with [September dashboard](reports/2026-09/dashboard.html) or [September workbook](reports/2026-09/Corner_Loaf_2026-09.xlsx). The dashboard opens directly in a browser, works offline, and has searchable checks, ranking controls and print-to-PDF. The workbook is a reviewable snapshot with filters, record-level ledgers, customer matching evidence, rankings, duplicate audit and two reconciliation bridges. [Close notes](reports/2026-09/close_notes.md) explain the findings and list the relevant IDs.

Original exports are read only. Each report includes source paths and SHA-256 hashes. Monetary calculations use decimal arithmetic; rounding is to cents per merchandise line, as the bookkeeper specified. Today's catalog identifies products by SKU, but never replaces charged prices. Output cells cannot execute formulas from source text.

## Next month: easiest option on this Mac

1. Create a folder such as `inputs/2026-10` and put **copies** of the exports there: `orders.csv`, `payments.csv`, `refunds.csv`, `customers.csv`, and `products.csv`. Include earlier orders referenced by refunds and earlier payments settling in October. Keep previous months' input folders.
2. Double-click `run_month.command`. Enter `2026-10`, then the folder `inputs/2026-10` (or drag the folder path into Terminal and remove any surrounding quotes if needed). Python 3 and internet access are needed for first-time installation of the single spreadsheet dependency.
3. Review `reports/2026-10/dashboard.html` and `Corner_Loaf_2026-10.xlsx`, then resolve the checks using original receipts. The dashboard's spreadsheet link opens/downloads the adjacent workbook depending on the browser.

If macOS prevents double-click execution, open Terminal in this project and run `./run_month.command`.

## Terminal option

```sh
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 reconcile.py --input inputs/2026-10 --month 2026-10
```

Optional: `--output path/to/report-folder`. Without it, reports go to `reports/YYYY-MM`. Re-running a month replaces that month's generated report files; other months and input files are preserved. Both `reconcile.py` and `dashboard_template.html` must stay together.

For overlapping exports, use `orders_*.csv`, `payments_*.csv`, or `refunds_*.csv` alongside or instead of the base file. Every matching file in that input folder is read. Use one current customer list and product catalog for the close. The headers must match the supplied exports; statuses are `captured`/`declined` for payments and `succeeded`/`failed`/`pending` for refunds. Additional statuses or export formats require updating the rules before use. The script stops on conflicting rows with the same ID/version rather than choosing an arbitrary record. Resolve those conflicts in input copies after checking the source systems.

## Review rules

- Highest `record_version` wins per order `line_id`; identical repeats are removed. Payments and refunds count once per ID. Distinct IDs with identical amounts remain in actual receipts, and order overpayments flag possible double charging.
- Match payment to an explicit order ID, or exact `order:` reference. Standalone terminal amounts remain unmatched. A payment with the same amount as an unpaid order is not proof of a match.
- Customer ID or loyalty reference is authoritative. Otherwise, exact normalized contacts and names must agree on one customer. Case and phone formatting are normalized. Misspelled emails can still resolve through a unique phone/name. No fuzzy-name merging. Shared household contacts and conflicting email/phone pairs stay unresolved. Anonymous walk-ins remain a separate pool.
- Sales use order dates. Returns and card/cash refunds use successful completion dates. Card charge fees use payment dates. Expected payout uses card settlement dates. Completed returns of August orders reduce September net sales; October completions are excluded from September even if requested in September.
- Sales exclude tax and gift cards; refund cash totals include tax. Redemption is payment from stored value, not fresh money. Gift-card liability movement is issuance less redemption; the closing balance requires the opening balance.
- Product and customer rankings use net merchandise sales. Orders count once within a product or customer. A multi-product order may appear in several product counts, so product order counts are not additive. Anonymous and unresolved pools are not individual customers.
- Order reconciliation compares all known accepted tenders with the original order amount, before refunds. Returns do not mean the original order was underpaid. Failed payment attempts stay in the ledger and are never receipts.
- Flag amounts overlap across check types; they are not a second financial ledger. Neither overpayments nor unresolved refunds should be automatically corrected or refunded without receipt/processor confirmation.

The dashboard and workbook are generated outputs. To correct evidence, add corrected export records to input copies (higher order version for line edits) and regenerate. Do not overwrite originals or hand-edit computed totals. There is no confirmed bank balance, deposit verification, cash drawer reconciliation, or opening gift-card balance in the supplied files.

## Files

- `reconcile.py`: reusable calculation and export program.
- `dashboard_template.html`: offline dashboard template.
- `requirements.txt` and `run_month.command`: setup and monthly refresh.
- `reports/YYYY-MM`: workbook, dashboard, close notes, JSON totals and individual sheet CSVs.
- `verify_report.py`: independent September total, source integrity, workbook and timing checks. Run `.venv/bin/python3 verify_report.py` after generating September.
