# Run 2: fresh chat, separate grader

September 30, 2026. GPT-6.1 Sol at medium reasoning did the task in Codex. GPT-6 Astra at high reasoning graded a saved copy in a separate chat.

| Measure | Result |
|---|---|
| Task time | 4 min 41 sec |
| Grading time | 5 min 15 sec |
| Problems fixed or flagged | 12/12 |
| Original strict grading score | 10/12 |
| Money received after refunds | $14,223.00 |
| Answer key total | $14,196.00 |
| Difference | $27 too high |
| Customers | 64 |
| Customers away for over 90 days | 32 |
| Help during the task | None |

The four disputed amounts were flagged but kept. The strict score also deducted a point for “Coffee Beans 1 lb” instead of “Coffee Beans 1lb.” That spelling difference does not lose a point under the current main scoring rule.

The dashboard worked offline and matched the cleaned file. It showed $12,039 as earned revenue, with gift-card money separate. It was readable on a 390-pixel-wide phone screen; two tables needed some sideways scrolling at 320 pixels.

## Was it blind?

The task chat received only the spreadsheet and prompt. Reviewing its activity found no access to the key or previous results. Files were saved before grading and remained unchanged. Access outside the task folder was not physically blocked.

The grader could not check access itself because it did not receive the task chat’s history. A [separate access review](artifacts/codex-sol-medium-02/controller-audit.md) records that check.

[Output files](artifacts/codex-sol-medium-02/frozen/output/) · [Detailed grading](artifacts/codex-sol-medium-02/grading-report.md) · [Original run report](../docs/archive/run-2-details.md)

This run used [prompt v0.1](artifacts/codex-sol-medium-02/reference/task-prompt.md). Future runs use v0.2.
