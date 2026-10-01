# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost?

The current task (v0.3) gives an AI the code for a bakery's online ordering site and the owner's to-do list for the month: fix the tax on coupon orders, let customers choose pickup times, and stop selling more cakes than the kitchen can bake. Hidden tests act like customers and staff using the finished site. The owner never has to read code, and neither do viewers. The question is simply whether the site works.

**Status: pilot.** One [Sol solo medium attempt](results/sol-medium-v0.3-01.md) passed all 32 hidden tests, scoring **1.000** in 6m 36s at an estimated **$0.2198** API-equivalent cost. This attempt leaves no quality headroom for the split. Calibrate further before running it. The previous task, [retail reconciliation (v0.2)](tasks/retail-reconciliation/), also reached the ceiling on accounting and planted-instance checks.

## Three configurations

| Configuration | Work | Reasoning |
|---|---|---|
| GPT-6.1 Sol solo | Sol does the whole job | Medium |
| Claude Opus 5.5 solo | Opus does the whole job | Medium |
| Opus + Sol | Opus plans and reviews; Sol implements | Medium for both |

Record the actual model identifiers and settings. Compare quality, time and the total cost of every task agent. The results can show that Sol already handles the job well, or that delegation adds more cost than value.

## The task

Build a fresh workspace and send the owner's prompt unchanged:

```sh
python3 tasks/ordering-site/package.py --out /path/to/runs/attempt-01
```

That creates `attempt-01/`, which is the solver's whole workspace, and `attempt-01-prompt.txt`:

> *I run Corner Loaf Bakery. This folder is our online ordering site. My nephew Sam built it last year and he's away at college now, so I can't ask him to change it.*
>
> *There are three things I need done this month. They're in the tickets folder, with the notes Sam left me about how the site works.*
>
> *Please make the changes and keep everything that already works working. Customers have already placed orders that are saved in data/bakery.db, so please don't lose any of those.*
>
> *When you're done, tell me what you changed and anything I should check before I put it live.*

| In the workspace | Contents |
|---|---|
| `bakery/` | The site: Python standard library only (`http.server`, `sqlite3`), about 700 lines |
| `tests/` | Sam's smoke tests |
| `tickets/` | [Tax and coupons](tasks/ordering-site/tickets/01-tax-and-coupons.md) · [Pickup times](tasks/ordering-site/tickets/02-pickup-times.md) · [Daily limits](tasks/ordering-site/tickets/03-daily-limits.md) |
| `data/bakery.db` | The live database: 30 customer orders created by the old version of the site |

Each ticket is the owner's request in plain language, followed by "Notes from Sam" that pin down the details the tests rely on (field names, status codes, rounding). The notes don't say how to build anything.

## What makes it hard

- **The tickets interact.** Pickup times and daily limits both change order creation, the database schema, the admin page and the menu. A rejected over-limit order must not use up a pickup slot, and cancelling must free both. A plan that treats the tickets separately pays for it later.
- **Existing data must survive.** The live database has the old schema and orders priced under the old tax rules. The site has to upgrade it in place, keep those orders and their recorded totals, and count them toward today's limits.
- **Subtle correctness.** Half-cent rounding that floating point gets wrong, the 2-hour vs 48-hour notice boundary, Monday closures, the same item on two lines, and all-or-nothing orders.
- **Black-box grading.** The 32 hidden tests start the submitted site and use it over HTTP: the API, pages, admin and restarts. They don't care how the code is organised.

The [reference solution](tasks/ordering-site/reference/) passes every hidden test and the untouched starter passes none of the ticket tests. The repository tests check both.

## Run and grade

1. Package a fresh workspace per attempt and give the solver only that folder and the prompt. Keep `hidden_tests/`, `reference/` and `evaluators/` out of reach.
2. Record the configuration, workspace hashes and limits in a [scorecard](results/scorecard-ordering-site.md). Use medium throughout and keep tools, time limits and permitted help the same. In the split, Opus writes briefs and reviews; Sol makes every code change.
3. When the solver finishes, freeze the workspace and record usage and cost for every task-agent call.
4. Grade the frozen copy in a sandbox, because the tests run the submitted code:

```sh
python3 evaluators/ordering_site.py --site /path/to/frozen/attempt-01 --report /path/to/report.json
```

The **quality score** is the mean of the three ticket pass rates, multiplied by the regression pass rate (existing behavior still working). It ranges from 0 to 1. Report per-ticket results, time and cost alongside it.

For video, the moments to capture are visual ones: checkout offering pickup times, a full slot disappearing, "Sold out" on the menu, and a coupon receipt with the right tax. Run the graded site with `python3 -m bakery.server` and record the browser.

## Calibrate first

1. Run Sol solo and Opus solo, 3 fresh attempts each.
2. The pilot is useful if Sol solo lands well below Opus solo with a spread smaller than the gap. If Sol scores near 1.0, extend the backlog toward 8–12 tickets before spending on the split: gift-card balances, loyalty points reversed on refunds, holiday hours, a bookkeeper's export. Prefer tickets that cut across the code, since those reward planning.
3. Track the size of each run, too. The split saves money only when building and debugging make up most of the tokens.

## Check the benchmark

Python 3.10+ standard library only. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 evaluators/ordering_site.py --site tasks/ordering-site/reference
```
