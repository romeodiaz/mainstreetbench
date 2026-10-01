# Sol medium — v0.5 attempt 1

One fresh `gpt-6.1-sol` solo attempt at **medium** received a **raw score of 1.3/100**, passing **1/50 ticket checks** and **3/7 regression checks**. The task took **9m 22s** and an estimated **$0.3107** at standard API-equivalent rates. A shared menu-flow assumption dominates the grade: Sol requires customers to choose their pickup day before adding items, while the test driver attempts to add items first. This score needs that qualification before it can support model or harness comparisons.

| Check | Passed / total | Score |
|---|---:|---:|
| Raw overall score | | 1.3/100 |
| Regression: existing behavior | 3/7 | 42.9 |
| Ticket 1: tax and coupons | 0/5 | 0 |
| Ticket 2: pickup times | 0/8 | 0 |
| Ticket 3: daily limits | 0/6 | 0 |
| Ticket 4: gift cards | 0/10 | 0 |
| Ticket 5: online cancellation | 0/8 | 0 |
| Ticket 6: sold out on the menu | 0/4 | 0 |
| Ticket 7: change the cart | 1/4 | 25 |
| Ticket 8: total before ordering | 0/5 | 0 |
| Solver's own automated tests | 13/13 | |
| Existing live orders / items preserved | 30/30 and 60/60 | |

## What the grade measures here

The menu says **"Choose your pickup day, then add items."** With no day selected, `menu.js` disables every Add button. Selecting a day fetches availability and enables available products. This is a plausible reading of ticket 6, which asks for a pickup-day choice and sold-out information before filling the cart.

The unchanged `Shopper.order()` driver opens the menu and immediately requires an enabled Add button. It chooses the pickup date later, at checkout. Its separate `menu_for_day()` helper supports date selection on the menu, but ordinary order creation does not use it. **52 failures** stop at "could not add SKU"; the remaining failure expects a promo-code error although the shopper is still on the menu. There are no setup errors. Most ticket behavior is never reached.

The sole passing ticket check, emptying the cart, is also a false positive here: the driver returns before adding or editing, and that test accepts an unplaced order unless the reason says it could not change the cart. It therefore does not verify cart removal in this attempt. Both the menu-day step and that check's failure handling need correction.

A targeted, read-only [sandboxed browser diagnostic](sol-medium-v0.5-01/menu-flow-diagnostic.json) confirmed that a fresh visitor cannot add before selecting a day, then can add after choosing Saturday. Its checkout probe hit an exact-label mismatch in the diagnostic helper; that initial evidence is preserved. A [short continuation using a flexible label](sol-medium-v0.5-01/menu-flow-continuation.json) completed a normal order in a fresh database/context: two loaves, pickup at 10:00, a $19.44 preview and matching customer confirmation, with no page errors or failed requests. This proves one working date-first flow, not all ticket behavior or a replacement score. The original submission and grading evidence remain unchanged.

Before using this run for calibration, the driver should accommodate menu-day selection before adding items, then the same frozen submission can be regraded under the recorded corrected grader version. Another Sol run is unnecessary for that correction. This record retains the original v0.5 score; neither the benchmark nor the submission was repaired.

## Configuration and verification

Source commit: `bee5fa06f3c15cba120e75271470f89911ba818f`. Codex CLI: `0.159.0`. Explicit **`gpt-6.1-sol`** and **`model_reasoning_effort="medium"`**, one ephemeral session/turn, 45-minute limit. No task retries, coaching, grader feedback or delegation. All self-debugging and verification are included in task usage.

`package.py --out runs/sol-v0.5-01` created 25 files, seed 20261008 and the unchanged owner prompt. Same-byte copies were preserved outside the checkout; the prompt went unchanged to stdin. An outer macOS sandbox denied the repository, controller/evidence directory, prior sessions, memories, skills/plugins and selected private paths, including Data-volume aliases. The previous temporary benchmark workspace was held out before launch. Other host reads and network remained available, so this was not a full container.

User config/rules, task subagents, web search, apps, plugins, memories, hooks and fast mode were disabled. Host skill discovery still attempted access and emitted warnings; the sandbox denied those reads. The inner Codex sandbox was disabled to avoid unsupported nested macOS sandboxes. Packaging/grading used Python 3.12.14; Sol's login shell selected Python 3.9. Sol used installed host Playwright and Chromium headless shell build 1223 for its own browser checks, after correcting an initial missing-browser path. Those checks passed in the saved task trace.

The 29 submitted files were frozen before grading, excluding bytecode and installed runtimes. The unchanged trusted evaluator/hidden suite ran in a clean environment; every submitted server ran in a deny-default macOS sandbox with scratch databases and loopback HTTP. Hidden tests, evaluator, host credentials and external network were denied to server processes. Playwright 1.63.0 used Chromium 153.0.8010.12 with its built-in sandbox enabled and fresh profiles/contexts. The acceptance grade took **16.609 seconds**, with **60 server launches and 12 browser launches**. Its early failures explain the short duration; reference and starter controls took 337.155 and 305.225 seconds respectively.

Controls passed: reference **100/100, 57/57 checks**; starter **0/100**, regressions **7/7**, tickets **0/50**. Repository tests: **32 passed, three browser-dependent tests skipped** in the base environment; the separate browser controls ran with Playwright. Frozen/site/source hashes stayed unchanged. The live database is byte-identical to its initial copy; a read-only audit confirms every original schema, column and row is preserved with SQLite integrity checks passing. Sol also saved a logically identical database backup.

Sol's final owner message describes all eight features, the live-database preservation and startup upgrade, and checks for hours, lead time, existing orders without pickup times and old gift-card balances. Its chosen gift-card policy is **immediate redemption on ordering**, with payment still collected at pickup; it explicitly flags that operating choice to the owner. The raw hidden grade does not validate these feature claims because its shopper generally stops on the menu.

## Usage and cost

| Agent | Input tokens | Cache reads | Cache writes | Output tokens | Estimated API equivalent |
|---|---:|---:|---:|---:|---:|
| Sol solo | 478,745 | 419,968 | 0 | 15,111 | $0.310661 |

Input includes cache reads, leaving **58,777 uncached tokens**. Output includes **1,298 reasoning tokens**. Task time was 562.044 seconds, with zero human task interventions. Grader and diagnostic code execution used no model calls; controller/audit model usage is outside these task totals and its cost is unknown.

The [dated cost basis](sol-medium-v0.5-01/pricing.json) uses [OpenAI's Sol pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol), checked October 1, 2026: $2/M uncached input, $0.10/M cache reads, $2.50/M cache writes and $10/M output. This assumes standard short-context processing with no fast/regional uplift; per-request context counters are unavailable. The run used ChatGPT authentication, so actual API charges and subscription allocation are unknown.

## Submission and evidence

- [Frozen site and launch checklist](sol-medium-v0.5-01/submission/README.md) · [Owner's final message](sol-medium-v0.5-01/final-response.md) · [Exact prompt](sol-medium-v0.5-01/prompt.txt)
- [Settings, usage and cost](sol-medium-v0.5-01/run.json) · [Task event log](sol-medium-v0.5-01/events.jsonl) · [Initial hashes](sol-medium-v0.5-01/initial-manifest.json) · [Frozen hashes](sol-medium-v0.5-01/frozen-manifest.json)
- [Original acceptance report](sol-medium-v0.5-01/grading/report.json) · [Independent grade audit](sol-medium-v0.5-01/grade-review.json) · [Grading integrity record](sol-medium-v0.5-01/grading/run.json) · [Before selecting a day](sol-medium-v0.5-01/diagnostic-menu-before.png) · [After selecting a day](sol-medium-v0.5-01/diagnostic-menu-after.png)
- [Date-first order proof](sol-medium-v0.5-01/menu-flow-continuation.json) · [Customer confirmation screenshot](sol-medium-v0.5-01/diagnostic-continuation-order-confirmation.png)
- [Database preservation](sol-medium-v0.5-01/database-preservation.json) · [Independent task audit](sol-medium-v0.5-01/final-task-review.json) · [Sol's own browser check](sol-medium-v0.5-01/solver-browser-check.cjs)
- [Reference control](sol-medium-v0.5-01/verification/reference-report.json) · [Starter control](sol-medium-v0.5-01/verification/starter-report.json) · [Repository tests](sol-medium-v0.5-01/verification/repo-tests.json)

Recorded paths describe the original machine; the [publication record](sol-medium-v0.5-01/publication.json) explains the layout. The frozen submission is the scored artifact. `runs/sol-v0.5-01` holds a separate editable copy and is excluded from Git. For a sandboxed regrade on macOS with Python 3.10+, install the saved [grader requirements](sol-medium-v0.5-01/grading/requirements-grader.txt) and Chromium, then run [grade_sandbox.py](sol-medium-v0.5-01/grading/grade_sandbox.py) with a checkout of the relevant grader commit, a new output directory and explicit Chromium executable/browser-installation paths (`--help` lists arguments). A changed grader must be recorded separately from this original v0.5 report.
