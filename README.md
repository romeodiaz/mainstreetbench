# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost?

This benchmark asks AI to close September 2026 for a fictional bakery. It must reconcile orders, payments, refunds and customers, then deliver a spreadsheet, dashboard and actionable exception list.

**No model runs or measured costs have been recorded yet. v0.2 difficulty is uncalibrated; see [Calibrate first](#calibrate-first).**

## Three configurations

| Configuration | Work | Reasoning |
|---|---|---|
| GPT-6.1 Sol solo | Sol does the whole job | Medium |
| Claude Opus 5.5 solo | Opus does the whole job | Medium |
| Opus + Sol | Opus plans and reviews; Sol implements | Medium for both |

Record the actual model identifiers and settings. Compare quality, time and the total cost of every task agent. The results can show that Sol already handles the job well, or that delegation adds more cost than value.

## The task

Copy this prompt unchanged and attach the [inputs](tasks/retail-reconciliation/inputs/):

> *I run Corner Loaf Bakery and I’m trying to close out September. I’ve attached our register orders, card payments, refunds, and customer list. I also included our price list and some notes from our bookkeeper.*
>
> *The numbers don’t seem to line up. Can you put this together and help me understand what happened?*
>
> *I want to know how much we sold, how much we refunded, what we paid in card fees, and how much money we should have received. Please show those separately so I can see why the totals differ.*
>
> *Please look for orders that weren’t paid, payments that don’t match an order, refunds that weren’t processed correctly, and anything that looks like it was counted twice. The customer names sometimes look different between systems, so please check those too.*
>
> *Give me a spreadsheet I can review and a simple dashboard showing the totals, our best-selling products, and our biggest customers. Include a short list of anything I need to check, with the order or payment numbers so I can find it. If something can’t be worked out from these files, tell me what’s missing.*
>
> *Please leave the original files alone. I’d like to do this every month, so give me an easy way to add next month’s exports and update the results.*

| File | Contents |
|---|---|
| [orders.csv](tasks/retail-reconciliation/inputs/orders.csv) | ~2,260 register line rows for 1,000 September orders, with edits, overlapping exports and late-August supporting orders |
| [payments.csv](tasks/retail-reconciliation/inputs/payments.csv) | ~1,060 tenders and terminal attempts, fees and settlement dates |
| [refunds.csv](tasks/retail-reconciliation/inputs/refunds.csv) | Refund requests and processing outcomes |
| [customers.csv](tasks/retail-reconciliation/inputs/customers.csv) | 80-member loyalty register, including shared households |
| [products.csv](tasks/retail-reconciliation/inputs/products.csv) | Current catalog and product categories |
| [bookkeeping_notes.md](tasks/retail-reconciliation/inputs/bookkeeping_notes.md) | What each export means and how the bakery reports a month |

Each run evaluates September only. The owner's request for easy future updates stays in the prompt; monthly reuse is not tested or scored.

## What makes it hard

v0.1 had about 20 traps, one of each, all within the first 21 order numbers. The bookkeeper's notes spelled out a rule for each, and the `notes` column labelled several of them. A capable mid-tier model could translate the rules into a short script and score near the ceiling. That left no room to measure what a stronger planner adds.

v0.2 changes the task so that judgment, not rule transcription, decides the score:

- **The notes describe, they don't prescribe.** They explain each export and define the reported figures. They don't list the edge cases or say how to treat them. The solver has to recognise that a declined attempt, an edited line or a household email needs special handling.
- **Edge cases repeat, vary and are scattered.** There are 118 keyed instances across 28 types among 1,000 orders, placed by timestamp so they don't cluster by ID. Most types come in variants: a voided line, a three-version edit, a declined-only "payment", a double charge on the next day, a refund on an edited line, a mistyped email with a reformatted phone.
- **Decoys punish over-correction.** Identical repeat purchases, two-card splits, promotional prices, household members with explicit IDs and two different Chris Lees must be left alone. An unlinked charge exactly equal to an unpaid order must not be matched on amount alone.
- **No row labels the answer.** The `notes` columns carry only harmless register noise, such as pickup instructions and card entry mode. About 18% of orders are walk-ins with no customer details, so flagging every order without an ID costs precision.
- **Timing matters at scale.** Card charges settle the next business day, skipping weekends and Labor Day. Late-August charges land in September's payout and late-September charges land in October's. Some refunds complete or settle after month end.

Every instance is scored on its own, so results form a gradient instead of a handful of pass/fail checks. The test suite includes an independent reference solver that reads only the inputs and scores 1.0, which shows the key is derivable from the packet. A naive solver that skips de-duplication, version handling and settlement dates scores below 0.5.

## Run and grade

1. Use a fresh chat and workspace containing only the prompt and inputs. Keep the key, generator and evaluator inaccessible to task agents.
2. Record the configuration in a [scorecard](results/scorecard-template.md), use medium throughout, and keep tools and limits consistent.
3. Save the finished work and usage/cost records, then freeze the submission before grading.
4. Have a separate grader extract the submitted results before seeing the [answer key](answer-keys/retail-reconciliation.md): headline figures, per-order and per-refund values, and the exception list. Check usable artifacts separately.

The evaluator reports a **quality score** from 0 to 1. It is the unweighted mean of three parts:
- the business-figure pass rate;
- the keyed-instance pass rate, averaged across instance types;
- the exception-list F1.

Those weights are fixed in advance so configurations can be placed on a cost/quality plot. Report artifacts, input preservation, time and cost alongside the score.

See the [method](docs/method.md) and [grader instructions](evaluators/README.md).

## Calibrate first

Before comparing harnesses, confirm the task separates the baselines:

1. Run Sol solo and Opus solo, at least 3 fresh attempts each, on the same fixtures. To get fixture variety without changing difficulty, generate alternate seeds with `--seed N --output-root DIR`, and use the same seed set for every configuration.
2. The task is useful for the split comparison if Sol solo lands well below Opus solo, roughly 0.3–0.6 against 0.75–0.9, with attempt-to-attempt spread smaller than the gap.
3. If Sol is still near the ceiling, raise difficulty before spending on the split: more orders (`--orders`), more variants per instance type, or new evidence such as a bank statement to match deposits against.

## Check the benchmark

The fixture generator and evaluator use Python's standard library. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tasks/retail-reconciliation/generate.py --output-root /tmp/mainstreetbench-reproduction
python3 tasks/retail-reconciliation/generate.py --seed 7 --output-root /tmp/mainstreetbench-seed-7
```

The second command reproduces the committed inputs and key byte for byte in a separate directory. The third builds an alternate fixture with its own key.
