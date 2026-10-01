#!/usr/bin/env python3
"""Grade a submitted ordering site with the hidden acceptance tests.

The tests start the submitted site as a separate process and use it through a real
browser (Playwright + Chromium) and the pre-existing admin API, so they don't depend
on how the solver structured the code or named its fields. This RUNS SUBMITTED
CODE: grade inside a sandbox or disposable container with no secrets.

A test method passes only if all of its subtests pass. Each ticket scores the
fraction of its tests that pass. The score, from 0 to 100, is the mean ticket
pass rate times the fraction of regression tests (existing behavior) still
passing, times 100.
Each ticket counts equally, whatever its number of tests.
"""

import argparse
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIDDEN = ROOT / "tasks" / "ordering-site" / "hidden_tests"
GROUPS = {
    "test_regression": "regression",
    "test_t1_tax_and_coupons": "ticket_1_tax_and_coupons",
    "test_t2_pickup_times": "ticket_2_pickup_times",
    "test_t3_daily_limits": "ticket_3_daily_limits",
    "test_t4_gift_cards": "ticket_4_gift_cards",
    "test_t5_online_cancellation": "ticket_5_online_cancellation",
    "test_t6_sold_out_on_menu": "ticket_6_sold_out_on_menu",
    "test_t7_change_the_cart": "ticket_7_change_the_cart",
    "test_t8_total_before_ordering": "ticket_8_total_before_ordering",
}
TICKETS = [g for g in GROUPS.values() if g.startswith("ticket_")]
SUITE_TIMEOUT = 1800


class Collector(unittest.TestResult):
    """Record one outcome per test method; any failing subtest fails the method."""

    def __init__(self):
        super().__init__()
        self.outcomes = {}

    def _record(self, test, status, detail=""):
        key = test.id()
        previous = self.outcomes.get(key)
        if previous is None or previous["status"] == "pass":
            self.outcomes[key] = {"status": status, "detail": detail[-1500:]}

    def addSuccess(self, test):
        self._record(test, "pass")

    def addFailure(self, test, err):
        self._record(test, "fail", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self._record(test, "fail", f"{subtest._subDescription()}\n" + self._exc_info_to_string(err, test))


def run_suite() -> dict:
    sys.path.insert(0, str(HIDDEN))
    suite = unittest.defaultTestLoader.discover(str(HIDDEN), pattern="test_*.py", top_level_dir=str(HIDDEN))
    names = []

    def walk(item):
        for child in item:
            if isinstance(child, unittest.TestSuite):
                walk(child)
            else:
                names.append(child.id())

    walk(suite)
    result = Collector()
    suite.run(result)
    # A class-level setup failure (the legacy database is built from the starter, so it is a
    # grading-environment fault) leaves its tests unrecorded; count them as errors.
    for name in names:
        result.outcomes.setdefault(name, {"status": "error", "detail": "Test did not run: class setup failed"})
    return {name: result.outcomes[name] for name in names}


def grade(site: Path) -> dict:
    env = {**os.environ, "SITE_ROOT": str(site.resolve())}
    child = subprocess.run([sys.executable, __file__, "--_run-suite"], env=env, capture_output=True,
                           text=True, timeout=SUITE_TIMEOUT)
    if child.returncode != 0:
        raise RuntimeError("Hidden test runner failed:\n" + child.stderr[-3000:])
    outcomes = json.loads(child.stdout.strip().splitlines()[-1])
    groups = {}
    for name, outcome in outcomes.items():
        group = GROUPS[name.split(".", 1)[0]]
        entry = groups.setdefault(group, {"passed": 0, "total": 0, "tests": {}})
        entry["total"] += 1
        entry["passed"] += outcome["status"] == "pass"
        entry["tests"][name.split(".", 1)[1]] = outcome
    for entry in groups.values():
        entry["rate"] = round(entry["passed"] / entry["total"], 4)
        entry["score"] = round(100 * entry["passed"] / entry["total"], 1)
    ticket_mean = sum(groups[t]["rate"] for t in TICKETS) / len(TICKETS)
    regression = groups["regression"]["rate"]
    return {
        "site": str(site),
        "score": round(100 * ticket_mean * regression, 1),
        "quality": {"score": round(100 * ticket_mean * regression, 1), "ticket_mean": round(100 * ticket_mean, 1),
                    "regression": round(100 * regression, 1),
                    "definition": "0–100: mean of the eight ticket pass rates × regression pass rate × 100."},
        "groups": groups,
    }


def main() -> None:
    if "--_run-suite" in sys.argv:
        print(json.dumps(run_suite()))
        return
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site", type=Path, required=True,
                        help="Frozen submission folder containing the bakery package")
    parser.add_argument("--report", type=Path, help="Write the full JSON report here (outside the submission)")
    args = parser.parse_args()
    if not (args.site / "bakery" / "server.py").is_file():
        parser.exit(2, f"Cannot grade: {args.site} has no bakery/server.py\n")
    try:
        report = grade(args.site)
    except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        parser.exit(2, f"Cannot grade: {exc}\n")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    quality = report["quality"]
    print(f"score: {quality['score']:.1f}/100 (tickets {quality['ticket_mean']:.1f} × "
          f"regression {quality['regression']:.1f}%)")
    for group, entry in report["groups"].items():
        print(f"{group}: {entry['passed']}/{entry['total']} ({entry['score']:.0f})")
        for name, outcome in entry["tests"].items():
            if outcome["status"] != "pass":
                print(f"  {outcome['status']}: {name}")


if __name__ == "__main__":
    main()
