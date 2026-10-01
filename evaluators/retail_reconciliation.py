#!/usr/bin/env python3
"""Grade independently extracted submission values without executing a submission.

The extraction is made by a separate grader from frozen outputs. This program
compares numeric evidence with the reference, scores every keyed instance and
the submitted exception list, and reports human-reviewed checks separately. It
cannot certify that a grader extracted the outputs faithfully.
"""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal, DecimalException, InvalidOperation
from pathlib import Path


PRIMARY_METRICS = (
    "merchandise_sales_before_refunds", "successful_refund_sales", "net_sales",
    "total_successful_refunds", "card_processing_fees", "expected_card_payout",
    "net_external_receipts",
)
ORDER_FIELDS = ("customer_id", "sales_before_refunds", "amount_due", "captured_tenders")
REFUND_FIELDS = ("deducted_sales",)
CUSTOMER_BUCKETS = {"UNASSIGNED", "WALK_IN"}
ARTIFACT_CHECKS = ("spreadsheet", "dashboard", "source_preservation")
LINE_SUFFIX = re.compile(r"-L\d+$")
# Fixed, pre-registered weights: business figures, keyed instances, exception list.
QUALITY_COMPONENTS = ("business_figures", "instances", "exception_f1")


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("Expected a finite JSON number or decimal string")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Expected a finite JSON number or decimal string") from exc
    if not result.is_finite():
        raise ValueError("Non-finite numbers are not evidence")
    return result


def equal_number(actual, expected, integer=False):
    actual, expected = number(actual), number(expected)
    try:
        return actual == expected if integer else abs(actual - expected) < Decimal("0.005")
    except DecimalException as exc:
        raise ValueError("Numeric evidence exceeds supported arithmetic range") from exc


def normalized_customer(value):
    return value.strip().upper() if isinstance(value, str) else value


def same_value(field, actual, expected):
    if field == "customer_id":
        return normalized_customer(actual) == normalized_customer(expected)
    return equal_number(actual, expected, integer=field in {"net_units", "order_count"})


def value_check(label, actual, expected, integer=False):
    if actual is None:
        return {"check": label, "status": "missing", "expected": expected}
    passed = equal_number(actual, expected, integer)
    return {"check": label, "status": "pass" if passed else "fail",
            "actual": actual, "expected": expected}


def indexed_rows(rows, identity, label):
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be a list")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(identity), str) or not row[identity]:
            raise ValueError(f"Each {label} row needs a nonempty {identity}")
        if row[identity] in result:
            raise ValueError(f"Duplicate {identity} in {label}: {row[identity]}")
        result[row[identity]] = row
    return result


def summary(checks):
    return {"passed": sum(c["status"] == "pass" for c in checks),
            "total": len(checks), "checks": checks}


def table_checks(expected_rows, actual_rows, identity, fields, label, optional_zero_rows=False):
    expected = indexed_rows(expected_rows, identity, f"reference {label}")
    actual = indexed_rows(actual_rows, identity, label)
    checks = []
    required = set(expected)
    for key, row in expected.items():
        if optional_zero_rows and all(number(row[field]) == 0 for field in fields):
            required.discard(key)
            if key not in actual:
                continue
        for field in fields:
            checks.append(value_check(f"{label}.{key}.{field}", actual.get(key, {}).get(field),
                                      row[field], integer=field in {"net_units", "order_count"}))
    # Keep the denominator fixed even when rows are missing or invented.
    checks.append({"check": f"{label}.membership", "status": "pass"
                   if required <= actual.keys() <= expected.keys() else "fail",
                   "missing": sorted(required - actual.keys()),
                   "unexpected": sorted(actual.keys() - expected.keys())})
    return checks


def customer_ranking(reference, submitted):
    expected_all = indexed_rows(reference["customers"], "customer_id", "reference customers")
    actual = indexed_rows(submitted, "customer_id", "top_customers")
    roster = sorted((row for key, row in expected_all.items() if key not in CUSTOMER_BUCKETS),
                    key=lambda row: number(row["net_sales"]), reverse=True)
    count = len(submitted)
    present = 0 < count <= len(roster)
    cutoff = number(roster[count - 1]["net_sales"]) if present else None
    eligible = {key for key, row in expected_all.items()
                if present and key not in CUSTOMER_BUCKETS and number(row["net_sales"]) >= cutoff}
    required = {key for key, row in expected_all.items()
                if present and key not in CUSTOMER_BUCKETS and number(row["net_sales"]) > cutoff}
    details, sales = [], []
    for row in submitted:
        key = row["customer_id"]
        target = expected_all.get(key) if key not in CUSTOMER_BUCKETS else None
        label = f"top_customers.{key}.net_sales"
        if target is None:
            details.append({"check": label, "status": "fail",
                            "reason": "Unknown customer, walk-in or unassigned bucket in ranking"})
        else:
            details.append(value_check(label, row.get("net_sales"), target["net_sales"]))
        if row.get("net_sales") is not None:
            sales.append(number(row["net_sales"]))
    membership = present and required <= actual.keys() <= eligible
    descending = len(sales) == count and sales == sorted(sales, reverse=True)
    return [
        {"check": "top_customers.present", "status": "pass" if present else "fail", "count": count},
        {"check": "top_customers.values", "status": "pass"
         if present and all(check["status"] == "pass" for check in details) else "fail", "details": details},
        {"check": "top_customers.ranking", "status": "pass" if membership and descending else "fail",
         "reason": "Check the largest N shown, with equal-value ties allowed; no display count is required"},
    ]


def reviewed_check(label, entry):
    if entry is None:
        return {"check": label, "status": "unverified", "evidence": ""}
    if not isinstance(entry, dict) or entry.get("verdict") not in {"pass", "fail", "unverified"}:
        raise ValueError(f"{label} needs verdict pass, fail or unverified")
    evidence = entry.get("evidence", "")
    if not isinstance(evidence, str) or (entry["verdict"] != "unverified" and not evidence.strip()):
        raise ValueError(f"{label} needs specific file/location evidence for a reviewed verdict")
    return {"check": label, "status": entry["verdict"], "evidence": evidence}


def record_key(value):
    """Map a line ID to its order ID so a flag on any line of an order counts for that order."""
    return LINE_SUFFIX.sub("", value.strip().upper())


def exception_sets(evidence):
    entries = evidence.get("exceptions", [])
    if not isinstance(entries, list):
        raise ValueError("exceptions must be a list")
    result = []
    for entry in entries:
        ids = entry.get("record_ids") if isinstance(entry, dict) else None
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i.strip() for i in ids):
            raise ValueError("Each exception needs a nonempty record_ids list of strings")
        result.append({record_key(i) for i in ids})
    return result


def validate_evidence(evidence):
    if not isinstance(evidence, dict):
        raise ValueError("Evidence must be a JSON object")
    for name in ("metrics", "artifacts"):
        if name in evidence and not isinstance(evidence[name], dict):
            raise ValueError(f"{name} must be an object")
    # Reject malformed numeric evidence even when a field is diagnostic only.
    for value in evidence.get("metrics", {}).values():
        if value is not None:
            number(value)
    for name, identity, fields in (
        ("products", "sku", ("net_units", "net_sales")),
        ("customers", "customer_id", ("order_count", "net_sales")),
        ("top_customers", "customer_id", ("order_count", "net_sales")),
        ("orders", "order_id", ORDER_FIELDS[1:]),
        ("refunds", "refund_id", REFUND_FIELDS),
    ):
        rows = evidence.get(name, [])
        indexed_rows(rows, identity, name)
        for row in rows:
            for field in fields:
                if row.get(field) is not None:
                    number(row[field])
    for row in evidence.get("orders", []):
        if row.get("customer_id") is not None and not isinstance(row["customer_id"], str):
            raise ValueError("orders.customer_id must be a string: a customer ID or NONE")
    exception_sets(evidence)


def instance_results(reference, evidence):
    tables = {"orders": indexed_rows(evidence.get("orders", []), "order_id", "orders"),
              "refunds": indexed_rows(evidence.get("refunds", []), "refund_id", "refunds")}
    flagged = exception_sets(evidence)
    instances = reference["instances"]
    anchors = {entry["id"]: {record_key(a) for a in entry["anchor_ids"]} for entry in instances}
    review_anchors = set().union(*(anchors[e["id"]] for e in instances if e["flag_required"]))
    other_anchors = set().union(*(anchors[e["id"]] for e in instances if not e["flag_required"]))

    checks, by_type = [], defaultdict(lambda: {"passed": 0, "total": 0})
    detected_review = 0
    for entry in instances:
        failures = []
        for check in entry["checks"]:
            row = tables[check["table"]].get(check["id"])
            actual = None if row is None else row.get(check["field"])
            if actual is None:
                failures.append(f"missing {check['table']}.{check['id']}.{check['field']}")
            elif not same_value(check["field"], actual, check["expected"]):
                failures.append(f"{check['table']}.{check['id']}.{check['field']}: {actual} != {check['expected']}")
        detected = any(found & anchors[entry["id"]] for found in flagged)
        if entry["flag_required"]:
            detected_review += detected
            if not detected:
                failures.append("not in the exception list")
        status = "pass" if not failures else "fail"
        checks.append({"check": f"instances.{entry['id']}", "status": status, "type": entry["type"],
                       "kind": entry["kind"], "failures": failures})
        by_type[entry["type"]]["total"] += 1
        by_type[entry["type"]]["passed"] += status == "pass"

    # An entry naming a review instance is useful; one naming only resolve/preserve
    # records is neutral; one naming none of the keyed records is an unnecessary flag.
    useful = sum(bool(found & review_anchors) for found in flagged)
    unnecessary = [sorted(found) for found in flagged if not found & (review_anchors | other_anchors)]
    review_total = sum(e["flag_required"] for e in instances)
    precision = useful / (useful + len(unnecessary)) if useful + len(unnecessary) else 0.0
    recall = detected_review / review_total if review_total else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    type_rates = {name: counts["passed"] / counts["total"] for name, counts in sorted(by_type.items())}
    instance_summary = summary(checks)
    instance_summary.update(by_type=dict(sorted(by_type.items())),
                            macro_rate=sum(type_rates.values()) / len(type_rates) if type_rates else 0.0)
    exception_summary = {
        "submitted_entries": len(flagged), "entries_naming_review_items": useful,
        "unnecessary_entries": len(unnecessary), "unnecessary_examples": unnecessary[:20],
        "review_instances_detected": detected_review, "review_instances": review_total,
        "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
    }
    return instance_summary, exception_summary


def full_table_check(label, expected_rows, actual_rows, identity, fields):
    actual = indexed_rows(actual_rows, identity, label)
    matched = 0
    for row in expected_rows:
        submitted = actual.get(row[identity])
        matched += submitted is not None and all(
            submitted.get(field) is not None and same_value(field, submitted[field], row[field]) for field in fields)
    return {"check": f"{label}.all_rows", "status": "pass" if matched == len(expected_rows) else "fail",
            "matched": matched, "total": len(expected_rows)}


def grade(reference, evidence, inputs=None):
    validate_evidence(evidence)
    metrics = evidence.get("metrics", {})
    unknown_metrics = metrics.keys() - reference["metrics"].keys()
    if unknown_metrics:
        raise ValueError(f"Unknown metric names: {', '.join(sorted(unknown_metrics))}")
    unknown_artifacts = evidence.get("artifacts", {}).keys() - set(ARTIFACT_CHECKS)
    if unknown_artifacts:
        raise ValueError(f"Unknown artifact checks: {', '.join(sorted(unknown_artifacts))}")
    primary = [value_check(f"metrics.{name}", metrics.get(name), reference["metrics"][name])
               for name in PRIMARY_METRICS]
    primary.extend(table_checks(reference["products"], evidence.get("products", []),
                                "sku", ("net_units", "net_sales"), "products"))
    primary.extend(customer_ranking(reference, evidence.get("top_customers", [])))
    diagnostics = [value_check(f"metrics.{name}", metrics[name], expected,
                              integer=name == "order_count")
                   for name, expected in reference["metrics"].items()
                   if name not in PRIMARY_METRICS and metrics.get(name) is not None]
    expected_customers = indexed_rows(reference["customers"], "customer_id", "reference customers")
    for row in evidence.get("top_customers", []):
        if row.get("order_count") is not None and row["customer_id"] in expected_customers:
            diagnostics.append(value_check(f"top_customers.{row['customer_id']}.order_count", row["order_count"],
                                           expected_customers[row["customer_id"]]["order_count"], integer=True))
    if "customers" in evidence:
        diagnostics.extend(table_checks(reference["customers"], evidence["customers"],
                                         "customer_id", ("order_count", "net_sales"), "customers",
                                         optional_zero_rows=True))
    if "orders" in evidence:
        diagnostics.append(full_table_check("orders", reference["orders"], evidence["orders"],
                                            "order_id", ORDER_FIELDS))
    if "refunds" in evidence:
        diagnostics.append(full_table_check("refunds", reference["refunds"], evidence["refunds"],
                                            "refund_id", REFUND_FIELDS))
    instances, exceptions = instance_results(reference, evidence)
    artifacts = [reviewed_check(f"artifacts.{name}", evidence.get("artifacts", {}).get(name))
                 for name in ARTIFACT_CHECKS]
    artifacts.append(reviewed_check("scope_review", evidence.get("scope_review")))
    preserved = []
    if inputs is not None:
        for name, digest in reference["input_hashes"].items():
            path = Path(inputs) / name
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            preserved.append({"check": f"input.{name}", "status": "pass" if actual == digest else "fail",
                              "actual": actual, "expected": digest})
    business = summary(primary)
    components = {"business_figures": business["passed"] / business["total"],
                  "instances": instances["macro_rate"], "exception_f1": exceptions["f1"]}
    return {
        "quality": {"score": round(sum(components.values()) / len(components), 4),
                    "components": {name: round(components[name], 4) for name in QUALITY_COMPONENTS},
                    "definition": "Unweighted mean of the business-figure pass rate, the instance pass rate "
                                  "averaged across instance types, and the exception-list F1."},
        "business_outcomes": business,
        "instances": instances,
        "exceptions": exceptions,
        "diagnostics": summary(diagnostics),
        "artifacts": summary(artifacts),
        "input_preservation": summary(preserved),
        "limitations": [
            "Numeric checks rely on a grader's faithful extraction from frozen submitted outputs.",
            "Usability and false changes outside keyed instances are reviewer verdicts, not automated certification.",
            "The quality score excludes artifacts, input preservation and cost; report those alongside it.",
        ],
    }


def load_json(path):
    def invalid_constant(value):
        raise ValueError(f"Invalid non-finite JSON constant: {value}")
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON object key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid_constant,
                      object_pairs_hook=unique_keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True,
                        help="Independent grader extraction, never a solver-required output")
    parser.add_argument("--inputs", type=Path, help="Frozen original input folder for hash comparison")
    parser.add_argument("--report", type=Path, help="Save full comparison JSON outside frozen outputs")
    args = parser.parse_args()
    try:
        key = load_json(args.key)
        report = grade(key, load_json(args.evidence), args.inputs)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Cannot grade: {exc}\n")
    report["reporting_period"] = key["reporting_period"]
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    quality = report["quality"]
    print(f"quality score: {quality['score']:.3f} " + " ".join(f"{k}={v:.3f}" for k, v in quality["components"].items()))
    exceptions = report["exceptions"]
    print(f"exceptions: recall {exceptions['recall']:.3f}, precision {exceptions['precision']:.3f}, "
          f"{exceptions['unnecessary_entries']} unnecessary of {exceptions['submitted_entries']} entries")
    print("instances by type: " + ", ".join(f"{name} {c['passed']}/{c['total']}"
                                             for name, c in report["instances"]["by_type"].items()))
    for group in ("business_outcomes", "instances", "diagnostics", "artifacts", "input_preservation"):
        result = report[group]
        print(f"{group}: {result['passed']}/{result['total']}")
        for check in result["checks"]:
            if check["status"] != "pass":
                print(f"  {check['status']}: {check['check']}")
    # A grading run can complete successfully while the submission earns failures.
    # Nonzero exit codes indicate invalid evidence or command errors, not a low score.


if __name__ == "__main__":
    main()
