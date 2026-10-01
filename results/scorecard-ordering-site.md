# Ordering site scorecard

Run ID: [ ] · Date: [ ] · Configuration: [Sol solo / Opus solo / Opus + Sol]

Source commit: [ ] · Workspace file hashes (from `package.py`): [ ] · Frozen submission hashes: [ ]

| Configuration | Recorded value |
|---|---|
| App/version and actual model identifiers | |
| Solo/lead reasoning: verified medium | |
| Sol worker reasoning: verified medium, if used | |
| Tools, instructions and enabled skills | |
| Time, retry and review limits | |
| Isolation limits or unverified settings | |

## Results

Grade the frozen copy in a sandbox with `evaluators/ordering_site.py`.

| Check | Passed / total | Failing tests |
|---|---|---|
| **Score (0–100)** | | |
| Regression (existing behavior) | /7 | |
| Ticket 1: tax and coupons | /5 | |
| Ticket 2: pickup times | /8 | |
| Ticket 3: daily limits | /6 | |
| Ticket 4: gift cards | /10 | |
| Ticket 5: online cancellation | /8 | |
| Ticket 6: sold out on the menu | /4 | |
| Ticket 7: change the cart | /4 | |
| Ticket 8: total before ordering | /5 | |

Unmentioned traps caught (gift card vs tax, cancel undoes slot/stock/gift money, voided purchased cards, stranger cancellation, code strength, staff see amount due, shown total matches charge): [ ]

Gift card policy chosen (live immediately / staff activation after payment): [ ]

Did the solver's own tests pass? Did it change or delete the live database's existing orders? [ ]

What the owner was told (summary of the final message, and whether it matches the work): [ ]

## Time and cost

Include every planning, building, review, correction and retry call. Missing usage or cost is unknown.

| Agent | Input tokens | Cache reads/writes | Output tokens | API charges | Usage source |
|---|---|---|---|---|---|
| Solo or Opus lead | | | | | |
| Sol worker, if used | | | | | |

| Measure | Recorded value |
|---|---|
| Task elapsed time | |
| Human help: actions and minutes | |
| Review rounds and retries | |
| Total task API charges or API-equivalent estimate | |

Dated price source and cache-counter treatment: [ ]
