"""Shop health check: the 100 problems are planted, keyed and graded the way the catalog says."""

import importlib.util
import json
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "health-check"
sys.path.insert(0, str(TASK))
sys.path.insert(0, str(TASK / "grading"))
sys.path.insert(0, str(ROOT / "evaluators"))

import books_generator  # noqa: E402
import build  # noqa: E402
import documents  # noqa: E402
import health_check  # noqa: E402
import reference_fix  # noqa: E402
import site_problems  # noqa: E402

HAS_BROWSER = importlib.util.find_spec("playwright") is not None
NO_SITE = {}   # grade without running the site checks (they are covered by the isolation check)


class HealthCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.shipped = cls.tmp / "shipped"
        build.build(cls.shipped)
        cls.key = cls.tmp / "shipped-key"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self, name):
        target = self.tmp / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.shipped, target)
        return target

    def test_catalog_has_100_problems_each_keyed_once(self):
        key = json.loads((self.key / "answer_key.json").read_text())
        ids = [entry["id"] for entry in key["problems"]]
        self.assertEqual(len(ids), 100)
        self.assertEqual(sorted(ids), sorted(build.catalog()))

    def test_site_problems_apply_alone_and_together(self):
        site_problems.check_patches()
        self.assertEqual(len(site_problems.SITE_PROBLEMS), 39)

    def test_books_are_deterministic(self):
        self.assertEqual(books_generator.generate(), books_generator.generate())

    def test_workspace_holds_only_solver_material(self):
        files = [p.relative_to(self.shipped).as_posix() for p in self.shipped.rglob("*") if p.is_file()]
        self.assertFalse([f for f in files if re.search(r"grading|answer|key|reference|site_problems|shop/", f)])
        self.assertTrue((self.tmp / "shipped-prompt.txt").is_file())
        db = sqlite3.connect(self.shipped / "website" / "data" / "bakery.db")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 26)

    def test_readme_shows_the_prompt_and_folder_guide_word_for_word(self):
        readme = (ROOT / "README.md").read_text()
        prompt = (TASK / "prompt.txt").read_text().strip()
        for paragraph in prompt.split("\n\n"):
            self.assertIn("> " + paragraph.replace("\n", " "), readme)
        for line in build.FOLDER_GUIDE.strip().splitlines()[2:]:
            self.assertIn(line, readme)

    def test_untouched_workspace_finds_nothing(self):
        graded = health_check.grade(self.shipped, self.key, "", None, site=NO_SITE)
        self.assertEqual(graded["score"], 0)
        self.assertEqual(sum(len(v) for v in graded["broke_something"].values()), 0)

    def test_reference_fix_passes_every_file_and_report_check(self):
        fixed = self.copy("fixed")
        report = reference_fix.fix(fixed, self.key)
        verdicts = {"problems": {p: {"verdict": "fixed"} for p in reference_fix.JUDGE_IDS}, "false_claims": []}
        graded = health_check.grade(fixed, self.key, report, verdicts, site=NO_SITE)
        misses = {p: v["why"] for p, v in graded["problems"].items() if v["status"] != "fixed" and not p[0] == "W"
                  and p not in site_problems.SITE_PROBLEMS}
        self.assertEqual(misses, {})
        self.assertEqual(graded["score"], 100 - len(site_problems.SITE_PROBLEMS))

    def test_listing_every_record_number_earns_no_flags(self):
        text = (self.shipped / "books" / "card_payments.csv").read_text()
        spam = "\n".join(sorted(set(re.findall(r"CL-\d{4}|PAY-\d{5}|RF-\d{3}|PO-\d{4}", text))))
        graded = health_check.grade(self.shipped, self.key, spam, None, site=NO_SITE)
        self.assertEqual(graded["score"], 0)
        self.assertTrue(graded["false_alarms"]["flags_need_judge"])

    def test_breaking_decoys_and_losing_orders_is_counted(self):
        broken = self.copy("broken")
        price_list = broken / "menu" / "price_list.csv"
        price_list.write_text(price_list.read_text().replace("16.50,2026-10-15", ",,"))
        db = sqlite3.connect(broken / "website" / "data" / "bakery.db")
        db.execute("DELETE FROM orders WHERE id = 1")
        db.commit()
        db.close()
        graded = health_check.grade(broken, self.key, "", None, site=NO_SITE)
        self.assertIn("file:menu/price_list.csv", graded["broke_something"]["decoys_changed"])
        self.assertEqual(graded["broke_something"]["live_orders_lost"], [1])

    @unittest.skipUnless(HAS_BROWSER, "site checks need Playwright for Python and Chromium")
    def test_full_controls_score_0_and_100(self):
        self.assertEqual(health_check.grade(self.shipped, self.key, "", None)["score"], 0)
        fixed = self.copy("fixed-full")
        report = reference_fix.fix(fixed, self.key)
        verdicts = {"problems": {p: {"verdict": "fixed"} for p in reference_fix.JUDGE_IDS}, "false_claims": []}
        graded = health_check.grade(fixed, self.key, report, verdicts)
        self.assertEqual(graded["score"], 100, {p: v["why"] for p, v in graded["problems"].items() if v["status"] != "fixed"})
        self.assertEqual(sum(len(v) for v in graded["broke_something"].values()), 0)


if __name__ == "__main__":
    unittest.main()
