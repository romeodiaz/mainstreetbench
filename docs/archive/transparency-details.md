# Inspect and reuse Main Street Bench

Main Street Bench shows how I curate a personal benchmark around work a small business might actually ask AI to do. It makes my choices, outputs and grading inspectable. One fictional bakery task is a practical example, not a claim about every model or every business.

The [GitHub repository](https://github.com/romeodiaz/mainstreetbench) is the audience's entry point. The answer key is available alongside the task. Viewers can inspect it before watching a result, rerun the task, check my scoring and suggest changes.

## What to open

| Material | What you can check |
|---|---|
| [Input CSV](../../tasks/01-messy-spreadsheet/customer_orders.csv) | The exact fictional business data given to a solver |
| [Current prompt, v0.2](../../tasks/01-messy-spreadsheet/prompt.md) | The approved bakery-owner request, without grading hints |
| [Public answer key](../../answer-keys/01-messy-spreadsheet.md) | Every planted issue, affected order IDs and generated reference totals |
| [Generator](../../tasks/01-messy-spreadsheet/generate.py) | How the fixture and ground truth were created |
| [Original key](../answer-key-history/task01-original.md) | The initially incorrect reference, preserved with corrections explained in the current key |
| [Run 1 report](../../results/codex-sol-medium-01.md) and [artifacts](../../results/artifacts/codex-sol-medium-01) | The informed, self-graded baseline and its exact outputs |
| [Run 2 report](../../results/codex-sol-medium-02.md) and [artifacts](../../results/artifacts/codex-sol-medium-02) | The fresh blind solver, different-model grader, frozen outputs and detailed scoring evidence |
| [Blind-run workflow](../blind-evaluation.md) | How inputs are separated, submissions frozen and access reviewed |

Both completed runs used the original v0.1 prompt. Future runs use v0.2. The recorded prompt version travels with each artifact package. Compare runs using the same prompt, task, model settings and declared tools.

## Public key, blind solver

Public judging materials and a blind run serve different purposes. The key lets viewers inspect the result. During a run, a fresh solver receives only the input and task prompt. It is instructed not to look up the benchmark, grading material or previous runs. The submission is frozen before a separate grader receives the key. Any correctness help or intervention is disclosed.

This is procedural blindness: recorded solver access is reviewed, but the local filesystem was not an enforced sandbox. The second run's grader did not receive the solver transcript, so its own report marks access evidence inconclusive. The separate controller audit documents the observed accesses and verified model settings. Both reports are preserved.

The purpose is to demonstrate a repeatable way to check AI work on a task I care about. I am not asking viewers to treat this fixture as a permanently hidden test or a universal leaderboard. If a later run already knows the key, it should be labeled informed and kept separate from blind runs.

## How scoring works

- Primary score: 12 planted issue types, one point each when every affected row is fixed or correctly flagged. Missing emails are one combined item. No partial credit.
- Financial accuracy: compare equivalent receipt measures with the generated reference independently of the issue score. A run can flag every issue and still have totals that differ.
- Functional checks: inspect requested outputs, the check method, offline behavior and phone readability separately.
- Exact-reference comparisons: disclose differences without turning harmless product-label spacing into a primary-score failure. Historical exact-key secondary scores remain recorded as originally judged.

The key exposes the generator's hidden ground truth. A solver cannot infer every fact from the messy input with certainty. For example, a mismatched receipt might be a typo or an undocumented discount. Correctly explaining that uncertainty can earn the issue-handling point; it does not mean the resulting receipts match the generated truth.

## Reproduce the fixture

The generator writes customer_orders.csv and the current answer key. Run it in a disposable copy of the repository so historical files and run packets remain intact:

```sh
python3 tasks/01-messy-spreadsheet/generate.py
```

It uses seed 20260930 and the Python standard library. The corrected generator was tested in a temporary directory: its CSV matched the checked-in source byte for byte. Expected input SHA-256:

```text
0fe0da134f5e16a426225741e42d3053c6d04f650342de147205119ada5f3e3d
```

Record your Python version and verify this hash when reproducing the fixture. The expected reference is 293 real transactions including 3 refunds, 64 customers and $14,196.00 in net receipts. Excluding both future-dated rows instead yields $14,075.00.

## Inspect the published submissions

The artifact packages contain task-specific files, not full chat transcripts or unrelated account data. Their manifests let you verify that the submitted outputs match the frozen copies. The reports disclose prompt versions, model settings, grading limits and the observed access conditions. Some historical reports include local evidence paths; use the adjacent artifact packages to inspect those files on GitHub.

From a clone, check the submitted outputs with:

```sh
python3 results/artifacts/codex-sol-medium-01/output/check.py
python3 results/artifacts/codex-sol-medium-02/frozen/output/check_dashboard.py
```

Inspect scripts before running them. A passing submitted checker establishes internal consistency, not correctness against ground truth. The independent grading report provides that separate comparison.

## Copy for the video or post

> I’m sharing the whole process: the spreadsheet, the prompt, the answer key, the outputs and how I scored them. You can check my work or try it with your own setup. This is an example of building a personal benchmark around a real kind of task, and showing what it takes to get useful work out of these tools. Everything is linked in the repository.

Link the repository directly in the description, caption or first comment. Show the key during the grading segment and keep the link available throughout. The scorecard can remain a convenient summary; access to the evidence should not require a comment, email address or private message.
