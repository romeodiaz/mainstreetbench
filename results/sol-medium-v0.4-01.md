# Sol medium — v0.4 attempt 1

One fresh `gpt-6.1-sol` solo attempt at **medium** scored **0.000**. It took **12m 18s** and an estimated **$0.3654** at standard API-equivalent rates. All 30 ticket checks and two regression checks stopped at the same broken checkout. This attempt supplies headroom, but a shared blocker dominates the result; repeat solo baselines before drawing a model or harness ranking.

| Check | Passed / total |
|---|---:|
| Quality score | 0.000 |
| Regression: existing behavior | 4/6 |
| Ticket 1: tax and coupons | 0/5 |
| Ticket 2: pickup times | 0/7 |
| Ticket 3: daily limits | 0/6 |
| Ticket 4: gift cards | 0/5 |
| Ticket 5: online cancellation | 0/7 |
| Solver's own tests | 17/17 |
| Existing live orders / items preserved | 30/30 and 60/60 |

## What failed

The checkout template loads `checkout.js` before the layout loads `cart.js`. Calling `renderLines()` throws **`readCart is not defined`** before the pickup-date listener is registered. The required pickup-time selector stays at **"Choose a date first"**, even after selecting a date. Customers cannot place orders.

A separate read-only [sandboxed browser diagnostic](sol-medium-v0.4-01/checkout-diagnostic.json) confirmed the error, script order and absent pickup-time request. All 32 acceptance failures report an unavailable pickup time; there were no setup errors. Sol's API tests and JavaScript syntax checks missed the browser runtime failure. The submission was neither repaired nor regraded.

There is also an unresolved gift-card policy choice: the starter says customers pay at pickup, so Sol requires staff activation after payment; the hidden tests redeem newly ordered cards immediately. The scored failures occur before redemption and do not establish the impact of that choice.

## Configuration and verification

Source commit: `e3631f08a3b306829f05fb4903da9143a756d435`. Codex CLI: `0.159.0`. Explicit model **`gpt-6.1-sol`**, **`model_reasoning_effort="medium"`**, one ephemeral task session, 45-minute limit. No coaching, retries, grader feedback or task-agent delegation. All task debugging and self-tests are included in usage.

`package.py --out runs/sol-v0.4-01` produced 22 files, seed 20261008 and the unchanged owner prompt. A same-byte copy outside the checkout was the solver's workspace. The outer macOS sandbox denied the repository, hidden tests, reference, controller evidence, prior sessions, memories, skills/plugins and selected private directories, including Data-volume aliases. Earlier temporary benchmark artifacts were moved behind that boundary during the run; the trace shows no access to them. Other host reads and network remained possible, so this was not a full container.

User config/rules, task subagents, web search, apps, plugins, memories, hooks and fast mode were disabled. Skill-loader warnings occurred for blocked directories; no skill contents reached the task. The inner Codex sandbox was disabled to avoid unsupported nested macOS sandboxes. Packaging and grading used Python 3.12.14; the task's login shell selected Python 3.9.6, as in v0.3.

The 26 submitted files were frozen before grading, excluding bytecode and installed runtimes. The unchanged evaluator and hidden suite ran in a clean environment; every submitted server ran in a deny-default macOS sandbox with temporary databases and loopback HTTP. Hidden tests, evaluator, host credentials and external network were denied to those server processes. Playwright 1.63.0 used Chromium 153.0.8010.12 with its built-in sandbox enabled and fresh browser profiles/contexts. Grading took **148.719 seconds**, logged 39 server launches and nine browser launches, and left all frozen bytes unchanged.

Controls passed: reference **36/36**; starter regression **6/6**, tickets **0/30**. Repository tests: **32 passed, three browser-dependent tests skipped** in the base environment; the separate browser controls above ran with Playwright. The live database is byte-identical to its initial copy, and a read-only audit confirms every original row/value remains present with SQLite integrity checks passing.

## Usage and cost

| Agent | Input tokens | Cache reads | Cache writes | Output tokens | Estimated API equivalent |
|---|---:|---:|---:|---:|---:|
| Sol solo | 604,111 | 549,632 | 0 | 20,149 | $0.365411 |

Input includes cache reads, leaving **54,479 uncached tokens**. Output includes **3,187 reasoning tokens**. Task time was 737.599 seconds, with zero human task interventions. Grading made no model calls; controller/audit model usage is outside these task totals and its cost is unknown.

The [dated cost basis](sol-medium-v0.4-01/pricing.json) uses [OpenAI's Sol pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol): $2/M uncached input, $0.10/M cache reads, $2.50/M cache writes and $10/M output. This assumes standard short-context processing with no fast/regional uplift; per-request context counters are unavailable. The run used ChatGPT authentication, so actual API charges and subscription allocation are unknown.

## Submission and evidence

- [Frozen site and launch checklist](sol-medium-v0.4-01/submission/README.md) · [Owner's final message](sol-medium-v0.4-01/final-response.md) · [Exact prompt](sol-medium-v0.4-01/prompt.txt)
- [Settings, usage and cost](sol-medium-v0.4-01/run.json) · [Task event log](sol-medium-v0.4-01/events.jsonl) · [Initial hashes](sol-medium-v0.4-01/initial-manifest.json) · [Frozen hashes](sol-medium-v0.4-01/frozen-manifest.json)
- [Acceptance report](sol-medium-v0.4-01/grading/report.json) · [Grading integrity record](sol-medium-v0.4-01/grading/run.json) · [Checkout screenshot](sol-medium-v0.4-01/diagnostic-checkout.png)
- [Database preservation](sol-medium-v0.4-01/database-preservation.json) · [Reference control](sol-medium-v0.4-01/verification/reference-report.json) · [Starter control](sol-medium-v0.4-01/verification/starter-report.json) · [Repository tests](sol-medium-v0.4-01/verification/repo-tests.json)

Recorded absolute paths describe the original machine; the [publication record](sol-medium-v0.4-01/publication.json) explains the saved layout. The frozen submission is the scored artifact. `runs/sol-v0.4-01` holds a separate editable copy and is excluded from Git. For a sandboxed regrade on macOS with Python 3.10+, install the saved [grader requirements](sol-medium-v0.4-01/grading/requirements-grader.txt) and Chromium, then run [grade_sandbox.py](sol-medium-v0.4-01/grading/grade_sandbox.py) with a checkout of the recorded source commit, a new output directory, and explicit Chromium executable/browser-installation paths (`--help` lists the arguments).
