# Ordering site task (v0.3 pilot)

| Path | Who sees it | What it is |
|---|---|---|
| `starter/` | Solver | The site as Sam left it; copied into each workspace |
| `tickets/` | Solver | The owner's three requests with Sam's notes |
| `prompt.txt` | Solver | The owner's message, sent unchanged |
| `package.py` | Operator | Builds a workspace, including a live `data/bakery.db` with 30 orders from the old site |
| `hidden_tests/` | Grader only | 32 black-box tests: 5 regression, 7 for ticket 1, 11 for ticket 2, 9 for ticket 3 |
| `reference/` | Grader only | A complete solution; proves the hidden tests are passable |

The starter has three deliberate gaps, one per ticket. It computes tax before the coupon, taxes and discounts gift cards, and rounds with floats. It has no pickup times. It has no limits.

The hidden harness builds its legacy database with `starter/`, never with the submission, so the migration tests are the same for every attempt. Tests pin the clock with `CORNERLOAF_NOW=2026-10-08T09:10:00` (a Thursday) and set `ADMIN_PASSWORD`. Sam's README documents both, so a solver keeps them working.

Grade with [`evaluators/ordering_site.py`](../../evaluators/ordering_site.py). See the [main README](../../README.md#run-and-grade).
