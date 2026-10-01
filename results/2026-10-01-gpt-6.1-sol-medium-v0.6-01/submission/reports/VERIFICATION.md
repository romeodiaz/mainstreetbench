Verified locally after the final changes:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`, from `website/`: **14 tests passed**. HTTP tests use disposable databases and local temporary servers, never the live database. Checks cover pricing/tax/coupon rules, quantities, dates/hours/notice/season, capacity, privacy, protected exports, gift-card paid activation and cancellation, and simultaneous orders/retries.
- `node reports/verify_browser_scripts.js`: passed. Covers JavaScript syntax and simulated DOM interactions for cart persistence/removal, coupon quote payloads, one submission per click sequence with a retry identifier, newsletter opt-in and October 3 displaying Saturday in America/Chicago. This is script-level verification, not a visual browser test.
- `python3 reports/reconcile.py`: reconstructs review CSVs from unchanged transaction sources. No financial transfers, customer refunds, supplier payments, messages or tax filings are made by this script.
- All 26 historical orders and 53 item records match the pre-change SQLite backup exactly; the empty historical gift-card table is unchanged. SQLite integrity check is `ok`. See `preservation_check.json`.
- Live database changes are limited to coffee catalog name/regular price, disabling any expired/staff-only online codes, and adding an empty gift-card payment-attestation table. Historical totals, customers, dates, statuses and private keys were preserved.
- Other corrected local files include menu/allergens/register prices, listing, policies, sign, current costs, gift-card liability, newsletter removal/suppression and unsent drafts. Originals are in `backups/original/`.

Not verified or performed: production hosting deployment/restart, real POS configuration, publication of the public listing, newsletter service changes, later bank/processor records, actual collection of orders, and item-level refund tax reversals. Tax summaries remain review estimates where explicitly labelled. The original inaccurate sales report and draft return remain unchanged as evidence; use the review CSVs for bookkeeper reconciliation.

The sandbox initially blocked local HTTP ports; the tests subsequently ran successfully with the allowed local-server permission. Python's default bytecode cache path was outside the writable workspace; tests use PYTHONDONTWRITEBYTECODE=1 to avoid that cache.
