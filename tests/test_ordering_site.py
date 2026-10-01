"""Ordering-site task checks: the hidden tests are passable, the starter fails them, packaging is clean."""

import importlib.util
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "ordering-site"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR = load("ordering_evaluator", ROOT / "evaluators" / "ordering_site.py")


class OrderingSiteTests(unittest.TestCase):
    def test_reference_passes_every_hidden_test(self):
        report = EVALUATOR.grade(TASK / "reference")
        self.assertEqual(report["quality"]["score"], 1.0, report["quality"])
        self.assertEqual({g: e["passed"] == e["total"] for g, e in report["groups"].items()},
                         {g: True for g in EVALUATOR.GROUPS.values()})

    def test_starter_keeps_existing_behavior_but_solves_no_ticket(self):
        report = EVALUATOR.grade(TASK / "starter")
        self.assertEqual(report["groups"]["regression"]["rate"], 1.0)
        for ticket in EVALUATOR.TICKETS:
            self.assertEqual(report["groups"][ticket]["passed"], 0, ticket)
        self.assertEqual(report["quality"]["score"], 0.0)

    def test_site_that_fails_to_start_scores_zero_without_crashing_the_grader(self):
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder) / "site"
            shutil.copytree(TASK / "starter", broken, ignore=shutil.ignore_patterns("__pycache__"))
            (broken / "bakery" / "server.py").write_text("raise SystemExit('broken')\n")
            report = EVALUATOR.grade(broken)
            self.assertEqual(report["quality"]["score"], 0.0)
            self.assertEqual(report["groups"]["regression"]["passed"], 0)

    def test_visible_starter_tests_pass(self):
        for site in ("starter", "reference"):
            with self.subTest(site=site):
                run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                                     cwd=TASK / site, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr[-2000:])

    def test_workspace_contains_only_solver_material(self):
        package = load("ordering_package", TASK / "package.py")
        with tempfile.TemporaryDirectory() as folder:
            result = package.package(Path(folder) / "workspace")
            files = set(result["files"])
            self.assertIn("data/bakery.db", files)
            self.assertIn("tickets/02-pickup-times.md", files)
            self.assertFalse([f for f in files if "hidden" in f or "reference" in f or "harness" in f
                              or f.endswith(".pyc")])
            self.assertTrue((Path(folder) / "workspace-prompt.txt").is_file())
            db = sqlite3.connect(Path(folder) / "workspace" / "data" / "bakery.db")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 30)
            columns = {row[1] for row in db.execute("PRAGMA table_info(orders)")}
            self.assertNotIn("pickup_slot", columns)


if __name__ == "__main__":
    unittest.main()
