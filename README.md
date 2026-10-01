# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost?

The current task (v0.4) gives an AI the code for a bakery's online ordering site and the owner's to-do list for the month, five tickets written only in the owner's words. Hidden tests use the finished site in a real browser, as customers, staff and a nosy stranger would. Nobody has to read code; the question is whether the site works.

**Status: calibration started.** [The first v0.4 Sol Medium run](results/sol-medium-v0.4-01.md) scored **0.000** in **12m 18s** for an estimated **$0.3654**. A checkout script error blocked ordering and all 30 ticket checks; 4/6 regression checks passed. More solo attempts are needed before comparing models or the split.

- **[v0.3](results/sol-medium-v0.3-01.md):** three tickets plus "Notes from Sam" that pinned down every interface. Sol solo scored 1.000 in 6m 36s for about $0.22.
- **[v0.2](tasks/retail-reconciliation/):** retail reconciliation. Sol also reached the ceiling.

Both earlier tasks handed the solver a specification. v0.4 doesn't: it removes the notes, adds two tickets, and plants traps the owner never mentions.

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
> *There are five things I need done this month. They're in the tickets folder.*
>
> *Please make the changes and keep everything that already works working. Customers have already placed orders that are saved in data/bakery.db, so please don't lose any of those.*
>
> *When you're done, tell me what you changed and anything I should check before I put it live.*

| In the workspace | Contents |
|---|---|
| `bakery/` | The site: Python standard library only (`http.server`, `sqlite3`), about 700 lines |
| `tests/` | Sam's smoke tests |
| `README.md` | Sam's developer notes: how to run and test the site, and its existing API |
| `tickets/` | [Tax and coupons](tasks/ordering-site/tickets/01-tax-and-coupons.md) · [Pickup times](tasks/ordering-site/tickets/02-pickup-times.md) · [Daily limits](tasks/ordering-site/tickets/03-daily-limits.md) · [Gift cards](tasks/ordering-site/tickets/04-gift-cards.md) · [Online cancellation](tasks/ordering-site/tickets/05-online-cancellation.md) |
| `data/bakery.db` | The live database: 30 customer orders created by the old version of the site |

Each ticket is a few sentences from the owner. There are no field names, endpoints or edge-case lists. The solver decides how the site should behave and how it should look.

## What makes it hard

**Traps the owner never mentions.** A careful engineer would catch each of these; the tickets don't point to any of them.

| Trap | Ticket |
|---|---|
| Paying with a gift card is payment, not a discount, so it must not reduce the tax | 1 × 4 |
| A customer cancelling must give back the pickup slot, the cakes and any gift-card money, and only once | 5 × 2, 3, 4 |
| Cancelling an order that bought a gift card must void that card | 5 × 4 |
| Order numbers count up, so anyone can type in someone else's. A stranger must not be able to cancel an order that way | 5 |
| Gift card codes must be distinct and long enough not to be guessed | 4 |
| Existing orders keep their original totals and still count toward today's cake limit | 1, 3 |
| A refused over-limit order must not use up a pickup slot | 3 × 2 |
| Opening hours (Tuesday–Sunday, 7–3) appear only in the site footer | 2 |

**Graded through the browser.** 36 hidden tests drive headless Chromium against the submitted site. They add items to the cart, check out, choose a pickup time and enter codes, finding controls by visible labels. Pickup times can be a dropdown, radio buttons or buttons, written "10:00", "10:00 AM" or "10am". Amounts are read from the admin orders API, which existed before the tickets. Each ticket's tests use other tickets' features only where the tickets interact, so skipping one ticket doesn't sink the others.

The [reference solution](tasks/ordering-site/reference/) passes all 36 hidden tests, and the untouched starter fails every ticket test. A deliberately different UI (radio buttons with 12-hour times, 16-digit numeric gift cards) also passes the pickup-time and gift-card tests.

## Run and grade

1. Package a fresh workspace per attempt and give the solver only that folder and the prompt. Keep `hidden_tests/`, `reference/` and `evaluators/` out of reach.
2. Record the configuration, workspace hashes and limits in a [scorecard](results/scorecard-ordering-site.md). Use medium throughout and keep tools, time limits and permitted help the same. In the split, Opus writes briefs and reviews; Sol makes every code change.
3. When the solver finishes, freeze the workspace and record usage and cost for every task-agent call.
4. Grade the frozen copy in a sandbox, because the tests run the submitted code. Grading needs Playwright for Python and Chromium (`pip install playwright && playwright install chromium`); it takes about 4 minutes.

```sh
python3 evaluators/ordering_site.py --site /path/to/frozen/attempt-01 --report /path/to/report.json
```

The **quality score** is the mean of the five ticket pass rates, multiplied by the regression pass rate (existing behavior still working). It ranges from 0 to 1. Report per-ticket results, time and cost alongside it.

For video, the moments to capture are visual ones: checkout offering pickup times, a full slot disappearing, a sold-out cake, a gift card paying part of an order, and a stranger failing to cancel someone else's order. Run the graded site with `python3 -m bakery.server` and record the browser.

## Calibrate first

1. Run Sol solo and Opus solo, 3 fresh attempts each.
2. The task is useful if Sol solo lands well below Opus solo with a spread smaller than the gap. Per-ticket results show which kinds of judgment separate them.
3. If Sol still scores near 1.0, treat that as the finding: for jobs like this, the cheap model alone is enough.
4. Track the size of each run, too. The split saves money only when building and debugging make up most of the tokens.

## Check the benchmark

The site and evaluator use Python 3.10+ and the standard library. Grading also needs Playwright; without it, the browser-dependent repository tests are skipped. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 evaluators/ordering_site.py --site tasks/ordering-site/reference
```
