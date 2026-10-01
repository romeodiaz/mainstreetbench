# Grade the reconciliation task

The evaluator compares values extracted from a frozen submission. It does not run the solver's files or require a particular workbook layout, filename, chart or programming language. The extraction JSON is a grader adapter, not a required solver output.

## Review workflow

1. **Extract without the answer key.** Give a separate grader the [owner's prompt](../README.md#the-task), bookkeeping notes and frozen outputs. Record:
   - the submitted figures and their file/location;
   - the per-order and per-refund values;
   - every entry on the owner's check list.

   Product, customer and per-order values may be derived from a submitted line-level or order-level table; document that derivation. Do not calculate missing results from the original inputs. Record any conflict between dashboard and workbook values. Freeze the extraction and its provenance before revealing the key.
2. **Compare and review.** Reveal the key, run the comparator and inspect the artifacts. Put verdicts in a separate copy of the extraction, preserving its original values and hashes. Give file/location evidence for each verdict. Do not repair the submission or replace extracted values with reference values.

With about 1,000 orders, an AI grader should script the conversion from the submitted spreadsheet to JSON rather than transcribe it. Record the script with the provenance.

## Evidence format

This empty template contains no reference answers. Leave missing figures `null` or omitted.

```json
{
  "metrics": {
    "merchandise_sales_before_refunds": null,
    "successful_refund_sales": null,
    "net_sales": null,
    "total_successful_refunds": null,
    "card_processing_fees": null,
    "expected_card_payout": null,
    "net_external_receipts": null
  },
  "products": [],
  "top_customers": [],
  "orders": [],
  "refunds": [],
  "exceptions": [],
  "artifacts": {
    "spreadsheet": {"verdict": "unverified", "evidence": ""},
    "dashboard": {"verdict": "unverified", "evidence": ""},
    "source_preservation": {"verdict": "unverified", "evidence": ""}
  },
  "scope_review": {"verdict": "unverified", "evidence": ""},
  "provenance": []
}
```

### Number formats

Amounts are finite JSON numbers or decimal strings, without currency symbols or commas. Booleans and `NaN` are invalid. Counts and units must match exactly. Money must differ by less than half a cent.

### Products and customers

- **`products`** rows contain `sku`, `net_units` and `net_sales`. Map harmless label variations to the supplied SKU. Gift-card issuance is separate from merchandise.
- **`top_customers`** rows contain `customer_id` and `net_sales`, sorted descending.
  - Check the largest N actually displayed; any positive display count is valid.
  - Equal-value ties may appear in either order or substitute at the cutoff.
  - Exclude the `UNASSIGNED` and `WALK_IN` buckets.

### Orders

**`orders`** has one row per September order the submission reports:

| Field | Meaning |
|---|---|
| `order_id` | The order number |
| `customer_id` | The loyalty ID the submission attributes the order to. Use `NONE` when it shows no customer: walk-in, unassigned, unknown or blank. |
| `sales_before_refunds` | Merchandise sales after discounts, excluding tax and gift cards |
| `amount_due` | All latest line totals, including tax and gift cards |
| `captured_tenders` | All accepted tenders the submission links to the order |

Leave a field out if the submission does not show it. Only rows for orders the submission reports as September orders belong here.

### Refunds

**`refunds`** has one row per refund ID with `deducted_sales`: the sales amount the submission deducts in September, or `0` if it deducts nothing.

### Exceptions

**`exceptions`** has one row per item on the owner's check list, with `record_ids` (the order, payment or refund numbers cited) and an optional `summary`.
- Extract the action list only. Leave out notes the submission presents as already resolved.
- A line ID counts as its order.

### Optional diagnostics

Extra named metrics from the key and a full `customers` table are diagnostics. Full customer rows contain `customer_id`, `order_count` and `net_sales`; zero-activity roster rows may be included or omitted. Missing diagnostics do not reduce the quality score.

### Provenance

`provenance` records extraction locations, derivations and scripts. Human review checks that the extraction faithfully represents the submission.

## What is reported

| Group | Checks |
|---|---|
| Quality score | Mean of the business-figure pass rate, the instance pass rate averaged across types, and the exception-list F1 |
| Business outcomes | Seven headline amounts, product units/sales, and customer summary presence, values and ranking |
| Instances | Each keyed instance passes when all of its per-order/per-refund values match and, if it needs review, one of its anchor IDs appears on the check list |
| Exceptions | Recall over review instances; precision over entries that name a review instance or no keyed record at all |
| Diagnostics | Optional metrics, full customer rollup, and whole-table order/refund accuracy |
| Artifacts | Reviewable spreadsheet, consistent dashboard, source preservation and scope review |
| Input preservation | Original input hashes, if `--inputs` is supplied |

### How the exception list is scored

An entry that names only records from `resolve` or `preserve` instances is neutral. It neither helps nor hurts, because a solver may reasonably mention them. An entry that names none of the keyed records counts against precision; listing every walk-in order is an example. So flooding the list cannot reach a high F1.

### Instance types

Instance types are reported separately, so you can see which kinds of judgment a configuration handles. Because the instance rate is averaged across types, the 16 duplicate-export instances don't outweigh the 2 coincidental-amount instances.

### What the score leaves out

The quality score omits artifacts, input preservation, extraction faithfulness and cost; report them alongside it. Review the spreadsheet for accessible records, figures and exceptions. Check that dashboard measures agree with the spreadsheet and are clearly labeled.

Use `scope_review` to assess unsupported deletions, customer merges, invented information and unnecessary flags beyond the keyed instances. Every reviewed verdict needs file/location evidence.

Score the September reconciliation and its delivered artifacts. The prompt's request for an easy future update process does not add a monthly reuse test. Do not add layout or feature requirements absent from the prompt. A submission that shows no order-level detail at all will score its per-order checks as missing. The owner asked for something they can review by order number, so that is a real gap, not a layout preference.

## Commands

Use Python 3. Keep evidence and reports outside the frozen submission:

```sh
python3 evaluators/retail_reconciliation.py \
  --key answer-keys/retail-reconciliation.json \
  --evidence /path/to/independent-evidence.json \
  --report /path/to/grading-report.json
```

Add `--inputs /path/to/frozen/inputs` to compare input hashes. If the run used an alternate seed, pass that fixture's key.

Exit code 0 means the comparison completed, even with failed checks. Exit code 2 means invalid evidence or command inputs. Missing figures and unverified reviews remain explicit.

Run grading-integrity and fixture tests without model calls or submitted scripts:

```sh
python3 -m unittest discover -s tests -v
```

`tests/reference_solver.py` is an independent solver used only by these tests. Like the key, keep it out of solver workspaces.
