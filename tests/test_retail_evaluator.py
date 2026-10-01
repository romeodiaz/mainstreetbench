"""Regression checks for grading integrity, not simulated model results."""

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("retail_evaluator", ROOT / "evaluators/retail_reconciliation.py")
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def reference():
    customers = [
        {"customer_id": "C1", "order_count": 5, "net_sales": 100},
        {"customer_id": "C2", "order_count": 4, "net_sales": 80},
        {"customer_id": "C3", "order_count": 3, "net_sales": 80},
        {"customer_id": "C4", "order_count": 2, "net_sales": 80},
        {"customer_id": "UNASSIGNED", "order_count": 1, "net_sales": 200},
    ]
    orders = [
        {"order_id": "O-1", "customer_id": "C1", "sales_before_refunds": 50, "amount_due": 54, "captured_tenders": 108},
        {"order_id": "O-2", "customer_id": "NONE", "sales_before_refunds": 40, "amount_due": 43.2,
         "captured_tenders": 43.2},
        {"order_id": "O-3", "customer_id": "C2", "sales_before_refunds": 10, "amount_due": 10.8,
         "captured_tenders": 10.8},
    ]
    def order_checks(order):
        return [{"table": "orders", "id": order["order_id"], "field": field, "expected": order[field]}
                for field in EVALUATOR.ORDER_FIELDS]
    return {
        "metrics": {**{name: 100 for name in EVALUATOR.PRIMARY_METRICS}, "order_count": 15},
        "products": [{"sku": "LOAF", "net_units": 10, "net_sales": 90}],
        "customers": customers,
        "top_customers": customers[:3],
        "orders": orders,
        "refunds": [{"refund_id": "R-1", "deducted_sales": 0}],
        "instances": [
            {"id": "double-charge-01", "type": "double-charge", "kind": "review", "flag_required": True,
             "anchor_ids": ["O-1", "P-1", "P-2"], "checks": order_checks(orders[0])},
            {"id": "ambiguous-01", "type": "ambiguous", "kind": "review", "flag_required": True,
             "anchor_ids": ["O-2"], "checks": order_checks(orders[1])},
            {"id": "refund-not-paid-01", "type": "refund-not-paid", "kind": "review", "flag_required": True,
             "anchor_ids": ["R-1"], "checks": [{"table": "refunds", "id": "R-1", "field": "deducted_sales",
                                                "expected": 0}]},
            {"id": "repeat-01", "type": "repeat", "kind": "preserve", "flag_required": False,
             "anchor_ids": ["O-3"], "checks": order_checks(orders[2])},
        ],
        "input_hashes": {},
    }


def extraction(key):
    evidence = {name: copy.deepcopy(key[name]) for name in ("metrics", "products", "top_customers", "orders",
                                                             "refunds")}
    evidence["exceptions"] = [{"record_ids": ["O-1"]}, {"record_ids": ["O-2-L01"]}, {"record_ids": ["R-1"]}]
    return evidence


class EvaluatorIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.key = reference()
        self.evidence = extraction(self.key)

    def numeric_report(self, evidence=None):
        return EVALUATOR.grade(self.key, self.evidence if evidence is None else evidence)["business_outcomes"]

    def test_missing_or_extra_rows_cannot_shrink_denominator(self):
        full = self.numeric_report()
        empty = self.numeric_report({})
        self.assertEqual(full["total"], empty["total"])
        self.assertEqual(empty["passed"], 0)
        self.evidence["products"].append({"sku": "INVENTED", "net_units": 10, "net_sales": 90})
        extra = self.numeric_report()
        self.assertEqual(full["total"], extra["total"])
        self.assertLess(extra["passed"], extra["total"])

    def test_money_error_is_visible_even_when_other_totals_match(self):
        self.evidence["metrics"]["net_sales"] = 100.01
        report = self.numeric_report()
        failures = [c for c in report["checks"] if c["status"] == "fail"]
        self.assertEqual([c["check"] for c in failures], ["metrics.net_sales"])

    def test_half_cent_is_not_accepted_as_equal(self):
        self.assertFalse(EVALUATOR.equal_number("100.005", 100))
        self.assertTrue(EVALUATOR.equal_number("100.004", 100))

    def test_unit_counts_cannot_use_money_tolerance(self):
        self.evidence["products"][0]["net_units"] = "10.001"
        self.assertLess(self.numeric_report()["passed"], self.numeric_report()["total"])

    def test_equal_value_customer_at_cutoff_is_interchangeable(self):
        self.evidence["top_customers"][2] = copy.deepcopy(self.key["customers"][3])
        report = self.numeric_report()
        self.assertEqual(report["passed"], report["total"])

    def test_owner_can_choose_display_count_without_hidden_requirement(self):
        full = self.numeric_report()
        self.evidence["top_customers"] = [copy.deepcopy(self.key["customers"][0])]
        del self.evidence["top_customers"][0]["order_count"]
        short = self.numeric_report()
        self.assertEqual(short["passed"], short["total"])
        self.assertEqual(full["total"], short["total"])

    def test_tie_does_not_allow_omitting_a_higher_customer(self):
        self.evidence["top_customers"] = copy.deepcopy(self.key["customers"][1:4])
        self.assertTrue(any(c["check"] == "top_customers.ranking" and c["status"] == "fail"
                            for c in self.numeric_report()["checks"]))

    def test_unassigned_bucket_is_not_a_customer(self):
        self.evidence["top_customers"][0] = copy.deepcopy(self.key["customers"][-1])
        self.assertLess(self.numeric_report()["passed"], self.numeric_report()["total"])

    def test_ranking_must_be_descending(self):
        self.evidence["top_customers"].reverse()
        self.assertTrue(any(c["check"] == "top_customers.ranking" and c["status"] == "fail"
                            for c in self.numeric_report()["checks"]))

    def test_omitted_diagnostics_do_not_change_primary(self):
        before = self.numeric_report()
        del self.evidence["metrics"]["order_count"]
        self.assertEqual(before, self.numeric_report())

    def test_full_roster_and_activity_only_customer_views_are_valid(self):
        inactive = {"customer_id": "CZERO", "order_count": 0, "net_sales": 0}
        self.key["customers"].append(inactive)
        self.evidence["customers"] = copy.deepcopy(self.key["customers"])
        full = EVALUATOR.grade(self.key, self.evidence)["diagnostics"]
        self.assertEqual(full["passed"], full["total"])
        self.evidence["customers"].remove(inactive)
        activity = EVALUATOR.grade(self.key, self.evidence)["diagnostics"]
        self.assertEqual(activity["passed"], activity["total"])

    def test_nonfinite_boolean_and_duplicate_evidence_are_rejected(self):
        for bad in (True, float("nan"), float("inf"), "NaN", "$100", "1e1000000"):
            with self.subTest(value=str(bad)):
                evidence = extraction(self.key)
                evidence["metrics"]["net_sales"] = bad
                with self.assertRaises(ValueError):
                    self.numeric_report(evidence)
        self.evidence["top_customers"].append(copy.deepcopy(self.evidence["top_customers"][0]))
        with self.assertRaises(ValueError):
            self.numeric_report()

    def test_review_requires_location_evidence(self):
        self.evidence["artifacts"] = {"dashboard": {"verdict": "pass", "evidence": ""}}
        with self.assertRaises(ValueError):
            self.numeric_report()
        self.evidence["artifacts"] = {}
        reviewed = EVALUATOR.grade(self.key, self.evidence)["artifacts"]
        self.assertEqual(reviewed["checks"][0]["status"], "unverified")

    def test_unknown_names_do_not_silently_disappear(self):
        self.evidence["metrics"]["net_salse"] = 100
        with self.assertRaises(ValueError):
            self.numeric_report()
        del self.evidence["metrics"]["net_salse"]
        self.evidence["artifacts"] = {"dashbord": {"verdict": "pass", "evidence": "dashboard.html: total"}}
        with self.assertRaises(ValueError):
            self.numeric_report()

    def test_source_hash_detects_changed_and_missing_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "orders.csv"
            source.write_bytes(b"order_id,total\nA1,10.00\n")
            self.key["input_hashes"] = {source.name: hashlib.sha256(source.read_bytes()).hexdigest()}
            self.assertEqual(EVALUATOR.grade(self.key, self.evidence, folder)["input_preservation"]["passed"], 1)
            source.write_bytes(b"order_id,total\nA1,11.00\n")
            self.assertEqual(EVALUATOR.grade(self.key, self.evidence, folder)["input_preservation"]["passed"], 0)
            source.unlink()
            self.assertEqual(EVALUATOR.grade(self.key, self.evidence, folder)["input_preservation"]["passed"], 0)

    def test_perfect_extraction_scores_one(self):
        report = EVALUATOR.grade(self.key, self.evidence)
        self.assertEqual(report["quality"]["score"], 1.0)
        self.assertEqual(report["instances"]["passed"], report["instances"]["total"])

    def test_review_instance_needs_a_flag_even_with_correct_values(self):
        self.evidence["exceptions"] = [{"record_ids": ["O-2"]}, {"record_ids": ["R-1"]}]
        report = EVALUATOR.grade(self.key, self.evidence)
        failed = [c["check"] for c in report["instances"]["checks"] if c["status"] == "fail"]
        self.assertEqual(failed, ["instances.double-charge-01"])
        self.assertAlmostEqual(report["exceptions"]["recall"], 2 / 3, places=4)

    def test_flagging_any_anchor_or_line_counts_for_the_instance(self):
        self.evidence["exceptions"][0] = {"record_ids": ["p-2"]}
        self.assertEqual(EVALUATOR.grade(self.key, self.evidence)["exceptions"]["recall"], 1.0)

    def test_unnecessary_flags_cost_precision_but_neutral_flags_do_not(self):
        self.evidence["exceptions"].append({"record_ids": ["O-3"]})
        report = EVALUATOR.grade(self.key, self.evidence)
        self.assertEqual(report["exceptions"]["precision"], 1.0)
        self.assertEqual(report["instances"]["passed"], report["instances"]["total"])
        self.evidence["exceptions"].append({"record_ids": ["O-999"]})
        report = EVALUATOR.grade(self.key, self.evidence)
        self.assertEqual(report["exceptions"]["unnecessary_entries"], 1)
        self.assertLess(report["exceptions"]["precision"], 1.0)
        self.assertLess(report["quality"]["score"], 1.0)

    def test_flooding_the_exception_list_cannot_reach_a_perfect_score(self):
        self.evidence["exceptions"] += [{"record_ids": [f"O-{n}"]} for n in range(100, 200)]
        report = EVALUATOR.grade(self.key, self.evidence)
        self.assertEqual(report["exceptions"]["recall"], 1.0)
        self.assertLess(report["exceptions"]["f1"], 0.1)

    def test_instance_fails_on_wrong_or_missing_order_values(self):
        self.evidence["orders"][0]["captured_tenders"] = 54
        del self.evidence["orders"][2]
        report = EVALUATOR.grade(self.key, self.evidence)
        failures = {c["check"]: c["failures"] for c in report["instances"]["checks"] if c["status"] == "fail"}
        self.assertEqual(set(failures), {"instances.double-charge-01", "instances.repeat-01"})
        self.assertTrue(all(f.startswith("missing") for f in failures["instances.repeat-01"]))

    def test_customer_attribution_compares_ids_case_insensitively(self):
        self.evidence["orders"][1]["customer_id"] = " none "
        self.assertEqual(EVALUATOR.grade(self.key, self.evidence)["instances"]["passed"], 4)
        self.evidence["orders"][1]["customer_id"] = "C1"
        self.assertEqual(EVALUATOR.grade(self.key, self.evidence)["instances"]["passed"], 3)

    def test_instance_rate_is_averaged_across_types(self):
        self.key["instances"] += [dict(self.key["instances"][3], id=f"repeat-{n:02d}") for n in range(2, 10)]
        self.evidence["orders"][0]["captured_tenders"] = 54
        instances = EVALUATOR.grade(self.key, self.evidence)["instances"]
        self.assertAlmostEqual(instances["macro_rate"], 3 / 4)

    def test_walk_in_bucket_is_not_a_customer(self):
        walk_in = {"customer_id": "WALK_IN", "order_count": 9, "net_sales": 500}
        self.key["customers"].append(walk_in)
        self.evidence["top_customers"][0] = copy.deepcopy(walk_in)
        self.assertLess(self.numeric_report()["passed"], self.numeric_report()["total"])

    def test_malformed_exceptions_are_rejected(self):
        for bad in ([{"record_ids": []}], [{"record_ids": "O-1"}], [{"summary": "no ids"}], {"record_ids": ["O-1"]}):
            with self.subTest(value=str(bad)):
                self.evidence["exceptions"] = bad
                with self.assertRaises(ValueError):
                    self.numeric_report()

    def test_nonstandard_json_and_duplicate_object_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            for content in ('{"metrics":{"net_sales":NaN}}', '{"metrics":{},"metrics":{"net_sales":100}}'):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    EVALUATOR.load_json(path)


if __name__ == "__main__":
    unittest.main()
