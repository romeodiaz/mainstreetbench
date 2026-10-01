# Ordering site task (v0.4)

| Path | Who sees it | What it is |
|---|---|---|
| `starter/` | Solver | The site as Sam left it; copied into each workspace |
| `tickets/` | Solver | The owner's five requests, in the owner's words only |
| `prompt.txt` | Solver | The owner's message, sent unchanged |
| `package.py` | Operator | Builds a workspace, including a live `data/bakery.db` with 30 orders from the old site |
| `hidden_tests/` | Grader only | 36 browser tests: 6 regression, then 5, 7, 6, 5 and 7 for tickets 1–5 |
| `reference/` | Grader only | A complete solution; proves the hidden tests are passable |

The starter computes tax before the coupon, taxes and discounts gift cards, and rounds with floats. It has no pickup times, limits, gift card codes or customer cancellation. Its order pages are public by sequential number.

`hidden_tests/harness.py` drives Chromium through Playwright and finds controls by visible label. `hidden_tests/sitectl.py` starts sites and builds the legacy database without a browser; packaging uses it too. Set `CHROMIUM_PATH` to use a specific browser binary. The v0.3 tickets, "Notes from Sam" and HTTP-only tests are in commit `f962bb5`.

The hidden harness builds its legacy database with `starter/`, never with the submission, so the migration tests are the same for every attempt. Tests pin the server clock with `CORNERLOAF_NOW=2026-10-08T09:10:00` (a Thursday) and the browser clock to the same time, and set `ADMIN_PASSWORD`. Sam's README documents both, so a solver keeps them working.

Grade with [`evaluators/ordering_site.py`](../../evaluators/ordering_site.py). See the [main README](../../README.md#run-and-grade).
