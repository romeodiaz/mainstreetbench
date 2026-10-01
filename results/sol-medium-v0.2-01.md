# Sol medium — v0.2 attempt 1

One fresh `gpt-6.1-sol` solo attempt at **medium** on the committed fixture (seed 20260930). The published quality score is **0.7635**. Accounting and planted-instance checks were perfect; excessive anonymous-customer flags lowered exception precision. The solver-visible flagging instructions are ambiguous, so this is not evidence of a broad accounting capability gap.

| Measure | Result |
|---|---:|
| Quality score | 0.7635 |
| Business figures | 31/31 (100%) |
| Planted instances | 118/118, all 28 types (100%) |
| Exception recall / precision / F1 | 100% / 16.99% / 0.2905 |
| Required review instances detected | 26/26 |
| Entries scored unnecessary | 171 of 215 |
| Whole-table order / refund checks | 1,000/1,000 and 24/24 |
| Input preservation | 6/6 hashes match |
| Spreadsheet / dashboard | Pass / pass |
| Scope review | Unverified because of flagging ambiguity |
| Task runtime | 10m 15s (614.652s) |
| Estimated task API-equivalent cost | $0.3619 |

## What affected the score

The submitted Action items sheet contains 179 anonymous-customer checks, 28 priority checks, and 8 declined-attempt checks. The dashboard defaults to the 28 priority entries; its all-checks view and workbook expose all 215. The independent grader extracted the full actionable list, not just the default view. Under the published rule, 171 entries name no keyed record and reduce precision. Resolve/preserve-only entries are neutral.

The packet says [walk-ins usually give no details](../tasks/retail-reconciliation/inputs/bookkeeping_notes.md), but also asks to flag sales that cannot be tied to a customer. The [scoring instructions](../evaluators/README.md#how-the-exception-list-is-scored) penalize ordinary walk-in flags. Clarify that distinction before using the score to calibrate difficulty or compare planners. This attempt leaves no numerical or planted-instance headroom; repeated baselines are still needed.

Optional customer diagnostics are 162/167 because the extraction retained the submitted bucket labels `WALK-IN` and `UNRESOLVED`, while the key uses `WALK_IN` and `UNASSIGNED`. Both pools and their correct values are present in the workbook. These adapter-label differences do not affect quality. The frozen extraction was retained without edits to its numbers or IDs.

## Run controls and cost

Source commit: `068dd07d411105bd7dec086a9595bb5765b0cc1f`. Codex CLI: `0.159.0`. Model and medium reasoning were explicitly configured in the saved invocation. One task agent; no retries, coaching or grading feedback. Time limit: 45 minutes. The exact README prompt was sent on stdin to a fresh, ephemeral CLI session with only six copied input files in its workspace. Subagents, web search, apps, plugins, memories and hooks were disabled. The solver read the frontend design skill and declined it as inapplicable.

An outer macOS sandbox blocked local repository/reference files, controller files, prior sessions and memories. Codex's inner sandbox was disabled to avoid unsupported nesting. Other host reads and network package installs remained possible; this was not a full container boundary. No reference access or task-model delegation appears in the recorded commands.

Submission and inputs were frozen before a separate Sol medium grader extracted figures, rows and actionable checks without the key. That extraction was frozen before reference access. A separate review copy adds artifact verdicts without changing extracted values. Independent browser checks confirmed totals, ID search, 28/215 check filters, workbook links, no JavaScript errors and no mobile horizontal overflow. Monthly reuse was not tested.

| Role | Input tokens | Cached input | Cache writes | Output tokens | Estimated API equivalent |
|---|---:|---:|---:|---:|---:|
| Task Sol | 547,653 | 481,536 | 0 | 18,152 | $0.3619 |
| Independent extraction grader | 294,342 | 252,160 | 0 | 6,240 | $0.1720 |
| Invalid sandbox startup, excluded | 46,064 | 22,400 | 0 | 434 | $0.0539 |

Costs use [OpenAI's standard Sol pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol), checked September 30, 2026: $2/M uncached input, $0.10/M cache reads, $2.50/M cache writes, $10/M output. Input counts include cache reads; output includes reasoning. Estimates assume short-context standard processing with no fast/regional uplift; per-request context counters are unavailable. This used ChatGPT authentication, so these are API-equivalent estimates, not actual API charges. Grading and invalid startup are excluded from task cost; controller/audit usage and subscription allocation are unavailable.

The initial 29-second launch could not read inputs because nested tool sandboxing failed. It produced no deliverables and is an infrastructure failure, not a scored task attempt. The valid attempt started fresh with the unchanged prompt and inputs.

## Artifacts and evidence

The frozen submission and grading evidence are included with this result:

- [Spreadsheet](sol-medium-v0.2-01/submission/reports/2026-09/Corner_Loaf_2026-09.xlsx) · [Dashboard](sol-medium-v0.2-01/submission/reports/2026-09/dashboard.html) · [Owner check list](sol-medium-v0.2-01/submission/reports/2026-09/close_notes.md) · [Assistant response](sol-medium-v0.2-01/submission/assistant-response.md)
- [Run metadata and hashes](sol-medium-v0.2-01/run.json) · [Task event log](sol-medium-v0.2-01/events.jsonl) · [Frozen submission manifest](sol-medium-v0.2-01/frozen-manifest.json) · [Cost basis](sol-medium-v0.2-01/pricing.json)
- [Frozen extraction](sol-medium-v0.2-01/grading/evidence.json) · [Extraction script](sol-medium-v0.2-01/grading/extract.py) · [Extraction notes](sol-medium-v0.2-01/grading/extraction-notes.md)
- [Reviewed grading report](sol-medium-v0.2-01/grading/report.json) · [Reference reveal order](sol-medium-v0.2-01/grading/reference-reveal.json) · [Independent dashboard checks](sol-medium-v0.2-01/verification/dashboard-checks.json) · [Desktop screenshot](sol-medium-v0.2-01/verification/desktop.png) · [Mobile screenshot](sol-medium-v0.2-01/verification/mobile.png)

Verify the frozen hashes and reproduce the saved score with Python's standard library, without running the submitted solver or making model calls:

```sh
python3 results/sol-medium-v0.2-01/verify.py
```

Original machine paths in metadata, logs and historical scripts describe the recorded execution. The [publication map](sol-medium-v0.2-01/publication.json) maps them to the included files. Runtime environments and duplicate workspaces are omitted. The archived extraction and browser-review scripts are evidence, not in-place rerun commands; the extractor requires a scratch directory containing a sibling `submission/` copy and writes a new `evidence.json` there.

All 30 benchmark tests passed on the pulled source. This single attempt does not establish a model or harness ranking.
