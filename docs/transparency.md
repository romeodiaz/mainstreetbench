# Check my work

Everything needed to inspect this test is included here.

| Start here | What you’ll find |
|---|---|
| [Spreadsheet](../tasks/01-messy-spreadsheet/customer_orders.csv) | The original fictional bakery orders |
| [Prompt](../tasks/01-messy-spreadsheet/prompt.md) | The exact request for future runs |
| [Answer key](../answer-keys/01-messy-spreadsheet.md) | The planted problems and correct figures |
| [Run 1](../results/codex-sol-medium-01.md) | Results and files from the first attempt |
| [Run 2](../results/codex-sol-medium-02.md) | Results, files and a separate AI’s grading |
| [Generator](../tasks/01-messy-spreadsheet/generate.py) | The code that creates the spreadsheet and key |

The answer key is public. During a blind run, the AI doing the task receives only the spreadsheet and prompt. The grader gets the key after the work is saved.

## What the score means

There are 12 types of planted problems. Each earns one point if every affected order is fixed or correctly flagged. The money totals are checked separately: flagging an uncertain amount can be sensible even when it leaves the total different from the answer key.

Both runs’ output files were saved before grading and checked for changes afterward. The full grading reports are linked from their results pages.

Two mistakes in the original key have been corrected. The current key explains them, and the [original key](answer-key-history/task01-original.md) remains available. The spreadsheet has not changed.

[Technical checks and reproduction steps](archive/transparency-details.md) · [How to run your own test](blind-evaluation.md)
