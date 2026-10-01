#!/usr/bin/env python3
"""Grade a submitted ordering site with the hidden acceptance tests.

The tests start the submitted site as a separate process and use HTTP only, so
they don't depend on how the solver structured the code. This RUNS SUBMITTED
CODE: grade inside a sandbox or disposable container with no secrets.

A test method passes only if all of its subtests pass. Each ticket scores the
fraction of its tests that pass. The quality score is the mean ticket score
times the fraction of regression tests (existing behavior) still passing.
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
}
TICKETS = [g for g in GROUPS.values() if g.startswith("ticket_")]
SUITE_TIMEOUT = 600


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
    ticket_mean = sum(groups[t]["rate"] for t in TICKETS) / len(TICKETS)
    regression = groups["regression"]["rate"]
    return {
        "site": str(site),
        "quality": {"score": round(ticket_mean * regression, 4), "ticket_mean": round(ticket_mean, 4),
                    "regression_rate": regression,
                    "definition": "Mean of the three ticket pass rates, multiplied by the regression pass rate."},
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
    print(f"quality score: {quality['score']:.3f} (ticket mean {quality['ticket_mean']:.3f} × "
          f"regression {quality['regression_rate']:.3f})")
    for group, entry in report["groups"].items():
        print(f"{group}: {entry['passed']}/{entry['total']}")
        for name, outcome in entry["tests"].items():
            if outcome["status"] != "pass":
                print(f"  {outcome['status']}: {name}")


if __name__ == "__main__":
    main()
