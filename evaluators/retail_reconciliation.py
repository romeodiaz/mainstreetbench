#!/usr/bin/env python3
"""Grade independently extracted submission values without executing a submission.

The extraction is made by a separate grader from frozen outputs. This program
compares numeric evidence with the reference and reports human-reviewed checks
separately. It cannot certify that a grader extracted the outputs faithfully.
"""

import argparse
import hashlib
import json
from decimal import Decimal, DecimalException, InvalidOperation
from pathlib import Path


PRIMARY_METRICS = (
    "merchandise_sales_before_refunds", "successful_refund_sales", "net_sales",
    "total_successful_refunds", "card_processing_fees", "expected_card_payout",
    "net_external_receipts",
)
ARTIFACT_CHECKS = ("spreadsheet", "dashboard", "source_preservation")


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
    roster = sorted((row for key, row in expected_all.items() if key != "UNASSIGNED"),
                    key=lambda row: number(row["net_sales"]), reverse=True)
    count = len(submitted)
    present = 0 < count <= len(roster)
    cutoff = number(roster[count - 1]["net_sales"]) if present else None
    eligible = {key for key, row in expected_all.items()
                if present and key != "UNASSIGNED" and number(row["net_sales"]) >= cutoff}
    required = {key for key, row in expected_all.items()
                if present and key != "UNASSIGNED" and number(row["net_sales"]) > cutoff}
    details, sales = [], []
    for row in submitted:
        key = row["customer_id"]
        target = expected_all.get(key) if key != "UNASSIGNED" else None
        label = f"top_customers.{key}.net_sales"
        if target is None:
            details.append({"check": label, "status": "fail",
                            "reason": "Unknown or unassigned customer in ranking"})
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
    ):
        rows = evidence.get(name, [])
        indexed_rows(rows, identity, name)
        for row in rows:
            for field in fields:
                if row.get(field) is not None:
                    number(row[field])
    indexed_rows(evidence.get("cases", []), "id", "cases")


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
    cases = indexed_rows(evidence.get("cases", []), "id", "cases")
    reference_cases = indexed_rows(reference["cases"], "id", "reference cases")
    unknown = cases.keys() - reference_cases.keys()
    if unknown:
        raise ValueError(f"Unknown case IDs: {', '.join(sorted(unknown))}")
    reviewed = [reviewed_check(f"cases.{key}", cases.get(key)) for key in reference_cases]
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
    return {
        "business_outcomes": summary(primary),
        "diagnostics": summary(diagnostics),
        "reviewed_cases": summary(reviewed),
        "artifacts": summary(artifacts),
        "input_preservation": summary(preserved),
        "limitations": [
            "Numeric checks rely on a grader's faithful extraction from frozen submitted outputs.",
            "Cases, usability and false changes are reviewer verdicts, not automated certification.",
            "There is no combined task score. Omitted diagnostics do not reduce the primary score.",
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
    for group in ("business_outcomes", "diagnostics", "reviewed_cases", "artifacts", "input_preservation"):
        result = report[group]
        print(f"{group}: {result['passed']}/{result['total']}")
        for check in result["checks"]:
            if check["status"] != "pass":
                print(f"  {check['status']}: {check['check']}")
    print("No combined score; manual verdicts and extraction require separate review.")
    # A grading run can complete successfully while the submission earns failures.
    # Nonzero exit codes indicate invalid evidence or command errors, not a low score.


if __name__ == "__main__":
    main()
