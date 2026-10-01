# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost?

This benchmark asks AI to close September 2026 for a fictional bakery. It must reconcile orders, payments, refunds and customers, then deliver a spreadsheet, dashboard and actionable exception list.

**No model runs or measured costs have been recorded yet. Task difficulty is uncalibrated.**

## Three configurations

| Configuration | Work | Reasoning |
|---|---|---|
| GPT-6.1 Sol solo | Sol does the whole job | Medium |
| Claude Opus 5.5 solo | Opus does the whole job | Medium |
| Opus + Sol | Opus plans and reviews; Sol implements | Medium for both |

Record the actual model identifiers and settings. Compare quality, time and the total cost of every task agent. The results can show that Sol already handles the job well, or that delegation adds more cost than value.

## The task

Paste the [owner's prompt](tasks/retail-reconciliation/prompt.md) unchanged and attach these [inputs](tasks/retail-reconciliation/inputs/):

| File | Contents |
|---|---|
| [orders.csv](tasks/retail-reconciliation/inputs/orders.csv) | Register line items and export revisions |
| [payments.csv](tasks/retail-reconciliation/inputs/payments.csv) | Tenders, fees and settlement dates |
| [refunds.csv](tasks/retail-reconciliation/inputs/refunds.csv) | Refund requests and processing outcomes |
| [customers.csv](tasks/retail-reconciliation/inputs/customers.csv) | Customer records and contact details |
| [products.csv](tasks/retail-reconciliation/inputs/products.csv) | Price list and product categories |
| [bookkeeping_notes.md](tasks/retail-reconciliation/inputs/bookkeeping_notes.md) | Reporting rules and source roles |

Each run evaluates September only. The owner's request for easy future updates stays in the prompt; monthly reuse is not tested or scored.

## Run and grade

1. Use a fresh chat and workspace containing only the prompt and inputs. Keep the key, generator and evaluator inaccessible to task agents.
2. Record the configuration in a [scorecard](results/scorecard-template.md), use medium throughout, and keep tools and limits consistent.
3. Save the finished work and usage/cost records, then freeze the submission before grading.
4. Have a separate grader extract the submitted results before seeing the [answer key](answer-keys/retail-reconciliation.md). Check business figures, decisions and usable artifacts separately.

See the [method](docs/method.md) and [grader instructions](evaluators/README.md).

## Check the benchmark

The fixture generator and evaluator use Python's standard library. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tasks/retail-reconciliation/generate.py --output-root /tmp/mainstreetbench-reproduction
```

The second command reproduces the synthetic inputs and reference answers in a separate directory.
