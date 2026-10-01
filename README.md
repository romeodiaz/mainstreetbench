# Main Street Bench v0.1

A benchmark for AI coding setups on the kind of work small businesses actually have. Instead of comparing models, Main Street Bench keeps the models fixed and compares the **harnesses** (the apps and workflows) that run them.

v0.1 setup: **Claude Opus 5.5 plans, GPT 6.1 Sol builds.**

## Task 1: The Messy Spreadsheet

Corner Loaf Bakery (fictional) has a year of orders in `customer_orders.csv`: 300 rows with 12 planted problems. Each harness gets the same file and the same prompt and must produce a clean orders file, a merged customer list, a cleaning log, a single-file dashboard, and a check script.

| File | Purpose |
|---|---|
| [`tasks/01-messy-spreadsheet/customer_orders.csv`](tasks/01-messy-spreadsheet/customer_orders.csv) | The test data |
| [`tasks/01-messy-spreadsheet/prompt.md`](tasks/01-messy-spreadsheet/prompt.md) | The exact prompt, pasted word for word into every harness |
| [`tasks/01-messy-spreadsheet/generate.py`](tasks/01-messy-spreadsheet/generate.py) | Regenerates the CSV and answer key exactly (fixed seed) |
| [`answer-keys/01-messy-spreadsheet.md`](answer-keys/01-messy-spreadsheet.md) | Planted problems by order ID and the correct results |
| [`results/scorecard-template.md`](results/scorecard-template.md) | Scoring sheet |

## How to run a harness

1. Copy **only** `tasks/01-messy-spreadsheet/customer_orders.csv` into a fresh project folder. Never give an agent this repo or the answer key.
2. Configure Opus 5.5 as planner and GPT 6.1 Sol as builder (see [`setups/`](setups/) and [`docs/harness-options.md`](docs/harness-options.md)).
3. Paste `prompt.md` and start a timer.
4. Stop when the check script passes and all five deliverables exist.
5. Score against the answer key with the scorecard template.

## Scoring rules

- Only the 12 planted problems count. Extra fixes are noted, not scored.
- A problem scores 1 if it is fixed or correctly flagged, 0 otherwise. No partial credit.
- Grade blind where possible, and run each harness more than once if time allows.

## Credits

Grading approach inspired by [Bug Hunt Bench](https://github.com/phuryn/bug-hunt-bench) by Pawel Huryn.
