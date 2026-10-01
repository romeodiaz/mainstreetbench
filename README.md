# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost?

The current task (v0.5) gives an AI the code for a bakery's online ordering site and the owner's to-do list for the month: eight tickets written only in the owner's words. Hidden tests use the finished site in a real browser, as customers, staff and a nosy stranger would. Scores run from 0 to 100.

**Status: recalibrating.**
- **[First fresh v0.5 Sol Medium run](results/sol-medium-v0.5-01.md):** raw score **1.3/100**, **9m 22s**, estimated **$0.3107**. The driver tries Add before selecting a menu pickup day; Sol's date-first menu requires that choice. This shared flow assumption prevents meaningful feature scoring and needs correcting before model comparisons.
- **[v0.4](results/sol-medium-v0.4-01.md), five tickets:** Sol solo scored 0. A script-order bug inherited from the starter broke checkout once Sol edited it.
  - v0.5 fixes that bug, accepts both gift-card policies (live at once, or activated by staff after payment), and fixes a harness bug with greyed-out times.
  - Graded under v0.5, Sol's v0.4 code with only the inherited bug fixed scores **62.5**: tickets 1–5 perfect, tickets 6–8 not attempted then. A fresh run will differ.
- **Earlier tasks:** [v0.3](results/sol-medium-v0.3-01.md) (three tickets with interface notes) and [v0.2](tasks/retail-reconciliation/) (reconciliation) both hit the ceiling.

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
> *There are eight things I need done this month. They're in the tickets folder.*
>
> *Please make the changes and keep everything that already works working. Customers have already placed orders that are saved in data/bakery.db, so please don't lose any of those.*
>
> *When you're done, tell me what you changed and anything I should check before I put it live.*

| In the workspace | Contents |
|---|---|
| `bakery/` | The site: Python standard library only (`http.server`, `sqlite3`), about 700 lines |
| `tests/` | Sam's smoke tests |
| `README.md` | Sam's developer notes: how to run and test the site, and its existing API |
| `tickets/` | [Tax and coupons](tasks/ordering-site/tickets/01-tax-and-coupons.md) · [Pickup times](tasks/ordering-site/tickets/02-pickup-times.md) · [Daily limits](tasks/ordering-site/tickets/03-daily-limits.md) · [Gift cards](tasks/ordering-site/tickets/04-gift-cards.md) · [Online cancellation](tasks/ordering-site/tickets/05-online-cancellation.md) · [Sold out on the menu](tasks/ordering-site/tickets/06-sold-out-on-the-menu.md) · [Change the cart](tasks/ordering-site/tickets/07-change-the-cart.md) · [Total before ordering](tasks/ordering-site/tickets/08-total-before-ordering.md) |
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
| Staff must see what's left to collect when a gift card pays part of an order | 4 |
| Gift card codes must not be readable by typing in someone's order number | 4 × 5 |
| A refused order must not take money off the gift card | 3 × 4 |
| Staff cancellations must refund gift cards too, not just customer ones | 5 × 4 |
| The total shown before ordering must match the charge exactly: half-cent rounding, tax after coupon, no coupon on gift cards | 8 × 1 |
| The shown total must follow cart edits | 8 × 7 |

**Graded through the browser.** 57 hidden tests drive headless Chromium against the submitted site. They add items to the cart, edit it, check out, choose a pickup time, pick a day on the menu and enter codes, finding controls by visible labels. Pickup times can be a dropdown, radio buttons or buttons, written "10:00", "10:00 AM" or "10am". Cart lines can use number boxes, +/− buttons or a remove button. If a gift card code isn't live yet, the tests do what staff would: press the order's activate or mark-paid button on the orders page, then try again. Amounts are read from the admin orders API, which existed before the tickets. Each ticket's tests use other tickets' features only where the tickets interact, so skipping one ticket doesn't sink the others.

The [reference solution](tasks/ordering-site/reference/) scores 100 and the untouched starter scores 0. A deliberately different UI also scores 100: radio buttons with 12-hour times, +/− cart buttons and 16-digit numeric gift cards.

## Run and grade

1. Package a fresh workspace per attempt and give the solver only that folder and the prompt. Keep `hidden_tests/`, `reference/` and `evaluators/` out of reach.
2. Record the configuration, workspace hashes and limits in a [scorecard](results/scorecard-ordering-site.md). Use medium throughout and keep tools, time limits and permitted help the same. In the split, Opus writes briefs and reviews; Sol makes every code change.
3. When the solver finishes, freeze the workspace and record usage and cost for every task-agent call.
4. Grade the frozen copy in a sandbox, because the tests run the submitted code. Grading needs Playwright for Python and Chromium (`pip install playwright && playwright install chromium`); it takes about 6 minutes.

```sh
python3 evaluators/ordering_site.py --site /path/to/frozen/attempt-01 --report /path/to/report.json
```

The **score** runs from 0 to 100. It is the mean of the eight ticket pass rates, times the regression pass rate (existing behavior still working), times 100. Each ticket counts equally. Report per-ticket scores, time and cost alongside it.

For video, the moments to capture are visual ones: checkout offering pickup times, a full slot disappearing, a sold-out cake, a gift card paying part of an order, and a stranger failing to cancel someone else's order. Run the graded site with `python3 -m bakery.server` and record the browser.

## Calibrate first

1. Run Sol solo and Opus solo, 3 fresh attempts each.
2. The task is useful if Sol solo lands well below Opus solo with a spread smaller than the gap. Per-ticket results show which kinds of judgment separate them.
3. If Sol still scores near 100, treat that as the finding: for jobs like this, the cheap model alone is enough.
4. Track the size of each run, too. The split saves money only when building and debugging make up most of the tokens.

## Check the benchmark

The site and evaluator use Python 3.10+ and the standard library. Grading also needs Playwright; without it, the browser-dependent repository tests are skipped. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 evaluators/ordering_site.py --site tasks/ordering-site/reference
```
