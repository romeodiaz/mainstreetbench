# Codex solo baseline — Task 1

Recorded September 30, 2026 (America/Los_Angeles). Repository starting revision: `532f3a6`.

One Codex desktop chat ran **GPT-6.1 Sol, medium reasoning** for planning, implementation, checks and grading. Model and effort were verified from this chat's local `turn_context`. No other model, subagent, worker, or API inference call was used.

## Result

All five deliverables exist. `output/check.py` passes, and a one-cent dashboard mutation fails. The source CSV is unchanged. Offline rendering passed at 1280 px and 390 px, with no JavaScript errors or horizontal page overflow. The agent visually inspected both rendered screenshots.

| Measurement | Result |
|---|---|
| Setup / inspection | Approximately 1 minute |
| Task execution through frozen outputs | 2 min 58 sec |
| Total from chat start through freeze | Approximately 4 minutes |
| User interventions after initial request | 0 |
| Retained transactions | 293, including 3 refunds |
| Customers | 64 |
| Inactive customers | 32 |
| Net receipts produced | $14,223.00 |
| Key's full-data net revenue | $14,196.00 |
| Totals match key? | No, $27.00 higher |
| Issue discovery / flagging rule | 12/12 |
| Conservative answer-key handling score | 10/12 |
| Exact account usage / dollar cost | Not measured |

Task clock: 2026-10-01 00:40:42 UTC through 00:43:40 UTC, equivalent to September 30, 5:40:42–5:43:40 PM Pacific. This measures task execution plus included skill reads and verification, not model-only latency. Setup and grading are separate. Only one trial was run.

## Scoring

The README awards a point when a planted problem is fixed **or correctly flagged**. The answer key additionally asks for total recomputation and future-date correction or exclusion. Report both interpretations rather than silently resolving this conflict in favor of the run. The conservative score assigns zero when the frozen output does not take one of the answer key's explicit handling paths.

| # | Problem | Fixed or flagged | Strict handling | Evidence |
|---|---|---|---|---|
| 01 | Customer name variants | 1 | 1 | Maria Lopez, James Chen and Priya Patel merged through contact matches |
| 02 | Name whitespace | 1 | 1 | Trimmed/collapsed and logged by order ID |
| 03 | Mixed dates | 1 | 1 | Every date formatted YYYY-MM-DD |
| 04 | Currency text | 1 | 1 | Dollar signs and USD removed from numeric fields |
| 05 | Missing emails | 1 | 1 | Contact-supported recovery, otherwise explicit missing-email flags |
| 06 | Product variants | 1 | 1 | All variants mapped to six canonical names |
| 07 | Total mismatches | 1 | 0 | All four flagged, but recorded totals retained rather than recalculated |
| 08 | Phone formats | 1 | 1 | All phones formatted (555) 123-4567 |
| 09 | Refunds | 1 | 1 | All three retained as negative quantities and revenue |
| 10 | Future dates | 1 | 0 | Both flagged and excluded from monthly/recency calculations, but retained in cleaned orders and overall receipts |
| 11 | Test orders | 1 | 1 | 90001, 90002, 90003 removed |
| 12 | Duplicate rows | 1 | 1 | One retained copy per repeated order |

Tessa Park and Lena Park remain separate. Product unit totals match the key. Customer count and inactive customer list match the key. Most top-customer totals match; Lena Park is $544.50 instead of $549.00. Recorded mismatches account for the overall $27.00 difference. Two future-dated receipts totaling $121.00 appear in a separate date-unconfirmed bucket, changing monthly allocation.

## Validity and grading caveats

This is an **informed, self-graded harness baseline**, not a blind independent model evaluation. The agent read the repository README, prompt, harness notes and scorecard problem list before implementation. The answer key and generator were not read during implementation. The answer key was first read after deliverable hashes were frozen in `manifest.json`. Existing chat instructions and available skills were present; OpenAI Docs and Spreadsheets skill instructions were read. An official model/reasoning documentation lookup occurred during setup. Task business data came only from the supplied CSV.

Outputs were produced in a separate folder, but the same agent retained repository setup context. A fresh folder did not reset the chat context. The requested configuration differs from the repo's Opus-plans/Sol-builds comparison, so this serves as a solo control row rather than a direct matched-model harness comparison.

The answer key has two source inconsistencies:

- Orders 10058 (Gideon Petrov) and 10215 (Mei Weber) are listed as recoverable emails, but each has only one source row and no email. Flagging them is correct under the prompt's no-invention rule.
- Excluding both future-dated rows removes $121.00. Starting with the key's corrected full-data total of $14,196.00 yields $14,075.00, not the stated $14,175.00. The alternate key total is arithmetically inconsistent.

Neither the benchmark nor frozen deliverables were altered to match the key. Use the 10/12 conservative score and failed total match for comparisons requiring explicit answer-key handling.

## Artifacts and reproduction

The [shareable artifact package](../../results/artifacts/codex-sol-medium-01) contains the frozen five deliverables, exact v0.1 prompt, source and SHA-256 manifest. Output hashes match the original run. The local `runs/codex-sol-medium-01/` folder also holds the plan, builder, HTML template and screenshots and remains ignored by Git.

```sh
python3 runs/codex-sol-medium-01/output/check.py
```

Run this command to recheck the frozen outputs. Rebuilding is unnecessary for grading. Any later correction should go in a separate run folder and must not overwrite this baseline.
