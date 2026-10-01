# Main Street Bench

A personal test of AI tools on everyday small-business work. I share the task, prompt, answer key and results so you can check my work or try it yourself.

## The task

A fictional bakery has 300 order records with 12 types of problems. Can AI clean them up, organize the customers and build a useful sales dashboard?

[See the spreadsheet](tasks/01-messy-spreadsheet/customer_orders.csv) · [Read the prompt](tasks/01-messy-spreadsheet/prompt.md) · [Check the answer key](answer-keys/01-messy-spreadsheet.md)

## Results so far

Both runs used GPT-6.1 Sol at medium reasoning.

| Run | How it was tested | Time | Problems fixed or flagged | Money totals match? |
|---|---|---|---|---|
| [1](results/codex-sol-medium-01.md) | AI saw the problem list before starting and graded its own work | About 4 minutes | 12/12 | No: $27 too high |
| [2](results/codex-sol-medium-02.md) | Fresh AI chat, then a separate GPT-6 Astra/high grader | 4 min 41 sec | 12/12 | No: $27 too high |

Catching every problem does not mean every number is correct. Each report links to the actual outputs and grading details.

## Try it yourself

1. Start a fresh AI chat with only the spreadsheet attached.
2. Paste the prompt exactly as written and start a timer.
3. Let the AI finish. Record any help you give it.
4. Save its work before sharing the answer key with a separate grader.
5. Record the time, problems fixed or flagged, and whether the money totals match.

Use the [scorecard](results/scorecard-template.md) to keep track. [See the full process](docs/blind-evaluation.md).

**Current prompt: v0.2.** The two completed runs used the [older prompt](docs/prompt-history/task01-v0.1.md). Keep runs with different prompts separate when comparing them.

## Check the work

[Outputs and evidence](docs/transparency.md) · [How the test data was made](tasks/01-messy-spreadsheet/generate.py) · [AI setups](docs/harness-options.md)

This is one example of building a useful personal test. It does not show which AI is best at every task.

Inspired by Pawel Huryn’s [Bug Hunt Bench](https://github.com/phuryn/bug-hunt-bench).
