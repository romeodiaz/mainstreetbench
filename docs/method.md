# Run a fair comparison

Compare Sol solo, Opus solo, and Opus planning/review with Sol implementing. Use **medium for every task agent**. This measures complete configurations, including their apps, tools and orchestration.

## Prepare

Give each configuration the exact [owner's prompt](../tasks/retail-reconciliation/prompt.md) and the same [input files](../tasks/retail-reconciliation/inputs/). Start a fresh chat and clean workspace for each attempt. Keep the repository, answer keys, generator and evaluator outside the task agents' accessible workspace. Record any access boundary that cannot be enforced.

Record prompt/input hashes, actual model identifiers, confirmed reasoning settings, app versions, tools, instructions and skills in the [scorecard](../results/scorecard-template.md). Keep tool access, libraries, time limits, retries and permitted human help consistent. Record settings that cannot be verified.

In the split, Opus writes briefs, reviews results and requests corrections. Sol implements all deliverables. Set the review limit before starting and preserve the delegation messages.

## Run and freeze

Record elapsed time and human interventions. Capture usage and cost for every task-agent call, including planning, implementation, reviews, corrections, failures and retries. Save the usage sources and distinguish input/output tokens and cache reads/writes where available.

Save the completed submission, hash the original inputs and outputs, and freeze them before exposing grading feedback or the answer key. Record incomplete work when a limit is reached.

Each attempt covers September only. The owner's future-update request remains in the prompt, but monthly reuse is not tested or scored.

## Grade externally

Use a separate grader after the submission is frozen. If AI assists grading, use medium and record its actual model and usage separately:

1. Give the grader the prompt, bookkeeping notes and submitted outputs, without the key. Extract the figures actually reported and cite their file, sheet/cell, table or dashboard location. Freeze this extraction. Never derive a missing submitted result from the original inputs.
2. Reveal the [answer key](../answer-keys/retail-reconciliation.md). Compare the frozen figures, review the keyed cases and inspect the spreadsheet, dashboard and exceptions. Add reviewer verdicts in a separate copy without changing the extracted values.

The solver does not need to produce evaluator JSON. The grader creates it using the [evidence format](../evaluators/README.md), then runs:

```sh
python3 evaluators/retail_reconciliation.py \
  --key answer-keys/retail-reconciliation.json \
  --evidence /path/to/independent-evidence.json \
  --inputs /path/to/frozen/inputs \
  --report /path/to/grading-report.json
```

Keep extraction and report files outside the frozen submission. Review submitted scripts before executing them. The comparator checks extracted numbers; separate review establishes whether the extraction is faithful and the artifacts work.

Report these dimensions separately:

- Business figures: seven primary amounts, product net units/sales, and the displayed biggest customers' values and ranking.
- Decisions: supported resolutions, justified owner-review requests, and preservation of valid records and separate customers.
- Artifacts: a reviewable spreadsheet, an agreeing dashboard, traceable exceptions and unchanged inputs.
- Resources: elapsed time, human help, total task-agent usage and cost.

Count false matches, merges, deletions and unnecessary flags. Missing evidence stays unverified. There is no combined weighted score.

## Compare the results

Sum every task-agent call and report external grading cost separately. Distinguish actual API charges, estimated API-equivalent cost and subscription spending. Preserve dated pricing and cache-counter assumptions. Missing cost is unknown, not zero.

A solo agent also uses a harness. To isolate a harness effect, compare the same model and setting across harnesses. Repeat fresh attempts across configurations before making a quality/cost claim; report the number of attempts and variation. This single fixture has no model results yet and cannot establish a general ranking by itself.
