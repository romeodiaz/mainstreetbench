# Grade the reconciliation task

The evaluator compares values extracted from a frozen submission. It does not run the solver's files or require a particular workbook layout, filename, chart or programming language. The extraction JSON is a grader adapter, not a required solver output.

## Review workflow

1. **Extract without the answer key.** Give a separate grader the owner's prompt, bookkeeping notes and frozen outputs. Record submitted figures and their file/location. Product and customer summaries may be derived from the submitted reconciliation table; document that derivation. Do not calculate missing results from the original inputs. Record conflicting dashboard/workbook values. Freeze the extraction and provenance before revealing the key.
2. **Compare and review.** Reveal the key, run the comparator and review the keyed cases against the submission. Put verdicts in a separate copy of the extraction, preserving its original values and hashes. Give file/location and affected transaction/customer IDs for each verdict. Do not repair the submission or replace extracted values with reference values.

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
  "cases": [],
  "artifacts": {
    "spreadsheet": {"verdict": "unverified", "evidence": ""},
    "dashboard": {"verdict": "unverified", "evidence": ""},
    "source_preservation": {"verdict": "unverified", "evidence": ""}
  },
  "scope_review": {"verdict": "unverified", "evidence": ""},
  "provenance": []
}
```

- Amounts are finite JSON numbers or decimal strings, without currency symbols or commas. Booleans and `NaN` are invalid. Counts/units must match exactly; money must differ by less than half a cent.
- `products` rows contain `sku`, `net_units` and `net_sales`. Map harmless label variations to the supplied SKU. Gift-card issuance is separate from merchandise.
- `top_customers` rows contain `customer_id` and `net_sales`, sorted descending. Check the largest N actually displayed; any positive display count is valid. Equal-value ties may appear in either order or substitute at the cutoff. Exclude `UNASSIGNED`, which is an unresolved bucket.
- Optional `order_count` values, extra named metrics from the key and a full `customers` table are diagnostics. Full customer rows contain `customer_id`, `order_count` and `net_sales`; zero-activity roster rows may be included or omitted. Missing diagnostics do not reduce the primary score.
- `cases` rows contain a key-supplied `id`, `verdict` (`pass`, `fail` or `unverified`) and specific `evidence`. Check the key's expected behavior against the actual work. Correct unresolved flags and preservation of legitimate records can pass.
- `provenance` records extraction locations and derivations. Human review checks that the extraction faithfully represents the submission.

## What is reported

| Group | Checks |
|---|---|
| Business outcomes | Seven headline amounts, product units/sales, and customer summary presence, values and ranking |
| Diagnostics | Optional metrics, counts and full customer rollup |
| Reviewed cases | Resolution, uncertainty handling and preservation with evidence |
| Artifacts | Reviewable spreadsheet, consistent dashboard, source preservation and scope review |
| Input preservation | Original input hashes, if `--inputs` is supplied |

These are assertion counts, not independent samples or a combined task score. Report the groups and failures alongside runtime and cost. Numeric passes do not establish faithful extraction or successful human review.

Review the spreadsheet for accessible records, figures and exceptions. Check that dashboard measures agree with the spreadsheet and are clearly labeled. Use `scope_review` to assess unsupported deletions, customer merges, invented information and unnecessary flags beyond the keyed cases; passing known cases is insufficient. Every reviewed verdict needs file/location evidence.

Score the September reconciliation and its delivered artifacts. The prompt's request for an easy future update process does not add a monthly reuse test. Do not add layout or feature requirements absent from the prompt.

## Commands

Use Python 3. Keep evidence and reports outside the frozen submission:

```sh
python3 evaluators/retail_reconciliation.py \
  --key answer-keys/retail-reconciliation.json \
  --evidence /path/to/independent-evidence.json \
  --report /path/to/grading-report.json
```

Add `--inputs /path/to/frozen/inputs` to compare input hashes. Exit code 0 means comparison completed, even with failed checks; code 2 means invalid evidence or command inputs. Missing figures and unverified reviews remain explicit.

Run grading-integrity tests without model calls or submitted scripts:

```sh
python3 -m unittest discover -s tests -v
```
