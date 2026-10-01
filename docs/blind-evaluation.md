# Run a fair test

A blind run means the AI doing the task has not seen the answer key or previous results.

1. Start a new chat, not a continuation of an old one. Give it only the [spreadsheet](../tasks/01-messy-spreadsheet/customer_orders.csv) and [current prompt](../tasks/01-messy-spreadsheet/prompt.md).
2. Record the AI model, reasoning setting, app version and prompt version. Set a time limit before starting; our second run allowed 30 minutes.
3. Start a timer. Let the AI work without hints. Count any help you give it, and stop when it finishes or reaches the limit.
4. Save an unchanged copy of its work, including anything unfinished. Do not let it revise the submission after grading starts.
5. Use a separate chat to grade it. Give the grader the task, saved outputs and answer key. Ask for evidence for each score, a separate check of the money totals, and a check that the dashboard works offline and on a phone. The grader should review submitted scripts before running them.
6. Record the result with the [scorecard](../results/scorecard-template.md). Review the task chat’s activity for access to the key or earlier results; disclose any access or uncertainty.

## Our setup

GPT-6.1 Sol at medium reasoning did the work. GPT-6 Astra at high reasoning graded the saved submission. They had separate chats and did not help each other.

The key was outside the task folder. We found no key access in the recorded activity, but the computer did not physically block access to other files. That limit is disclosed in the [run 2 report](../results/codex-sol-medium-02.md).

Grade against the prompt used for that run. The current prompt allows different filenames and ways of checking the numbers. Keep old and new prompt versions separate in comparisons.

[Detailed method and technical limits](archive/blind-run-details.md)
