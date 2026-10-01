# Sol medium — v0.3 attempt 1

One fresh `gpt-6.1-sol` solo attempt at **medium** scored **1.000**, passing all 32 hidden tests. The task took **6m 36s** and an estimated **$0.2198** at standard API-equivalent rates. This attempt leaves no quality headroom for Opus or the split to improve on. It does not establish variance or a model ranking; the pilot needs more difficulty before a quality-gap comparison can be useful.

| Check | Passed / total |
|---|---:|
| Quality score | 1.000 |
| Regression: existing behavior | 5/5 |
| Ticket 1: tax and coupons | 7/7 |
| Ticket 2: pickup times | 11/11 |
| Ticket 3: daily limits | 9/9 |
| Solver's own tests | 11/11 |
| Existing live orders / items preserved | 30/30 and 60/60 |

## Configuration and isolation

Source commit: `f962bb5094fc040b91cefcbb669fb4fd66e4636d`. Codex CLI: `0.159.0`. One new ephemeral session with explicit model `gpt-6.1-sol` and `model_reasoning_effort="medium"`. Limit: 45 minutes; no task retries, coaching, grader feedback or task-agent delegation. All debugging and repeated self-tests are included in the recorded usage.

`package.py --out runs/sol-v0.3-01` produced 20 starter files and a separate prompt. Its default seed was 20261008; its live database contained 30 orders. The exact packaged files were copied outside the checkout and the prompt was supplied unchanged on stdin. An outer macOS sandbox blocked the whole checkout, controller/evidence directory, prior sessions, memories, skills/plugins and selected private directories. Probes confirmed that hidden tests, reference and controller files were denied, including the Data-volume path alias. The task trace shows no reference access or delegation. Other host reads and network remained possible; this was not a full container boundary.

User config/rules, task subagents, web search, apps, plugins, memories and hooks were disabled. Host skill discovery was requested off and its directories were blocked; CLI skill-loader warnings occurred, but no skill contents reached the task. The inner Codex tool sandbox was disabled to avoid unsupported nested macOS sandboxes. Packaging and grading used Python 3.12.14. The task's login shell selected Python 3.9.6 despite the requested PATH; this observed runtime is recorded for future comparisons.

The 22 submitted files were frozen before grading, excluding bytecode caches and installed runtime folders. The unchanged evaluator and hidden tests ran with a clean environment. Every submitted server process ran in a deny-default macOS sandbox allowing its code, temporary databases, Python runtime and local HTTP; host credentials, hidden tests, evaluator and external network were blocked from that process. The trusted controller intercepts server launches; it does not change the evaluator, tests or submission. All 36 launches were logged and the frozen file hashes remained unchanged.

Controls confirmed the reference passes 32/32, the starter retains 5/5 regression checks and passes 0/27 ticket checks, and all 35 repository tests pass. A separate read-only database audit confirms all original orders, items, products, promos and columns/values remain present, with SQLite integrity checks passing. These diagnostics do not change the acceptance score.

## Usage and cost

| Agent | Input tokens | Cache reads | Cache writes | Output tokens | Estimated API equivalent |
|---|---:|---:|---:|---:|---:|
| Sol solo | 379,803 | 344,576 | 0 | 11,489 | $0.219802 |

Input includes cache reads, leaving 35,227 uncached input tokens. Output includes 1,001 reasoning tokens. Usage comes from the completed CLI turn in the saved event log. Task elapsed time was 396.252 seconds. Human task interventions: zero. External grading made no model calls; controller/audit model usage is outside task usage and its cost is unknown.

The [dated cost basis](sol-medium-v0.3-01/pricing.json) uses [OpenAI's Sol model pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol), checked September 30, 2026: $2/M uncached input, $0.10/M cache reads, $2.50/M cache writes and $10/M output. The estimate assumes standard short-context processing with no fast/regional uplift; per-request context counters are unavailable. This used ChatGPT authentication, so actual API charges and subscription allocation are unknown.

## Submission and evidence

- [Frozen site README and launch checklist](sol-medium-v0.3-01/submission/README.md) · [Owner's final message](sol-medium-v0.3-01/final-response.md) · [Exact prompt](sol-medium-v0.3-01/prompt.txt)
- [Run settings, usage and cost](sol-medium-v0.3-01/run.json) · [Task event log](sol-medium-v0.3-01/events.jsonl) · [Initial hashes](sol-medium-v0.3-01/initial-manifest.json) · [Frozen hashes](sol-medium-v0.3-01/frozen-manifest.json)
- [Acceptance report](sol-medium-v0.3-01/grading/report.json) · [Grading sandbox and integrity record](sol-medium-v0.3-01/grading/run.json) · [Server launches](sol-medium-v0.3-01/grading/server-launches.jsonl)
- [Live database preservation](sol-medium-v0.3-01/database-preservation.json) · [Repository tests](sol-medium-v0.3-01/verification/repo-tests.json) · [Reference control](sol-medium-v0.3-01/verification/reference-report.json) · [Starter control](sol-medium-v0.3-01/verification/starter-report.json)

Saved paths describe the original machine; the [publication record](sol-medium-v0.3-01/publication.json) explains the layout. The frozen submission is the scored artifact. `runs/sol-v0.3-01` contains a separate editable copy of the finished site and is excluded from Git.

For a fresh regrade on macOS with Python 3.10+, use the saved controller runner against a checkout of the recorded source commit and a new output directory:

```sh
python3 results/sol-medium-v0.3-01/grading/grade_sandbox.py \
  --site results/sol-medium-v0.3-01/submission \
  --source . --out /tmp/sol-v0.3-01-regrade
```
