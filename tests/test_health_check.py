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

    def test_dollars_at_risk_add_up_to_100000(self):
        listed = {pid: row["at_risk"] for pid, row in build.catalog().items()}
        self.assertEqual(listed, health_check.AT_RISK)   # the catalog and the grader show the same figures
        self.assertEqual(sum(listed.values()), 100_000)
        graded = health_check.grade(self.shipped, self.key, "", None, site=NO_SITE)
        self.assertEqual((graded["dollars_at_risk_caught"], graded["dollars_at_risk_total"]), (0, 100_000))

    def test_site_problems_apply_alone_and_together(self):
        site_problems.check_patches()
        self.assertEqual(len(site_problems.SITE_PROBLEMS), 31)

    def test_books_are_deterministic(self):
        self.assertEqual(books_generator.generate(), books_generator.generate())

    def test_workspace_holds_only_solver_material(self):
        files = [p.relative_to(self.shipped).as_posix() for p in self.shipped.rglob("*") if p.is_file()]
        self.assertFalse([f for f in files if re.search(r"grading|answer|key|reference|site_problems|shop/", f)])
        self.assertTrue((self.tmp / "shipped-prompt.txt").is_file())
        import integrity
        self.assertFalse([f for f in files if integrity.GUID.encode() in (self.shipped / f).read_bytes()])
        self.assertIn(integrity.GUID, (self.key / "answer_key.json").read_text())
        db = sqlite3.connect(self.shipped / "website" / "data" / "bakery.db")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 43)

    def test_readme_shows_the_prompt_word_for_word(self):
        readme = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", (ROOT / "README.md").read_text())
        prompt = (TASK / "prompt.txt").read_text().strip()
        for paragraph in prompt.split("\n\n"):
            self.assertIn("> " + paragraph.replace("\n", " "), readme)

    def test_example_workspace_matches_a_fresh_build(self):
        example = ROOT / "example-workspace"
        # Finder drops .DS_Store into folders it opens; it is ignored by git and is not part of the workspace.
        listing = lambda root: sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                                      if p.is_file() and p.name != ".DS_Store")
        self.assertEqual(listing(example), listing(self.shipped))
        for name in listing(self.shipped):
            if not name.endswith(".db"):
                self.assertEqual((example / name).read_bytes(), (self.shipped / name).read_bytes(), name)

        def orders(root):   # cancel keys are random per build
            db = sqlite3.connect(root / "website" / "data" / "bakery.db")
            db.row_factory = sqlite3.Row
            return [{k: row[k] for k in row.keys() if k != "cancel_key"} for row in db.execute("SELECT * FROM orders ORDER BY id")]
        self.assertEqual(orders(example), orders(self.shipped))

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

    def test_naming_records_without_saying_whats_wrong_earns_nothing(self):
        key = {entry["id"]: entry for entry in json.loads((self.key / "answer_key.json").read_text())["problems"]}
        planted = ", ".join(key[pid]["record_ids"][0] for pid in ("M29", "M33", "M34", "M37"))
        report = "\n".join([
            "You're open Tuesday to Sunday, as the door sign says. I reviewed the books from 2026-09-01 to 2026-09-30.",
            "I checked refunds " + ", ".join(f"RF-{n:03d}" for n in range(1, 14)) + " and they all look fine.",
            "\n".join(f"| RF-{n:03d} | succeeded |" for n in range(1, 14)),
            "Dispute DP-2209 is on file; nothing to do. The flyer went out on 9/19.",
            f"I spot-checked {planted} and found nothing wrong with them.",
            "Payouts " + ", ".join(f"PO-09{day:02d}" for day in range(1, 13)) + " all reached the bank.",
            "Two card payouts went to your old bank account. That isn't fraud, but chase it.",
        ])
        graded = health_check.grade(self.shipped, self.key, report, None, site=NO_SITE)
        self.assertEqual([pid for pid, v in graded["problems"].items() if v["status"] == "fixed"], [])

    def test_emptying_a_page_does_not_fix_it(self):
        emptied = self.copy("emptied")
        (emptied / "policies" / "gift_cards.md").write_text("TBD\n")
        graded = health_check.grade(emptied, self.key, "", None, site=NO_SITE)
        for pid in ("L03", "L15"):
            self.assertEqual(graded["problems"][pid]["status"], "not fixed", pid)

    def test_a_figure_inside_a_longer_number_does_not_count(self):
        figure = health_check.normalize
        self.assertTrue(health_check.has_figure(figure("The closing balance should be $2,485.00."), "2485.00"))
        self.assertTrue(health_check.has_figure(figure("2026-09,2240.00,425.00,180.00,2485.00,note"), "2485.00"))
        for text in ("payment PAY-02485", "a deposit of $12,485.00", "a payout of $2,485.37"):
            self.assertFalse(health_check.has_figure(figure(text), "2485"), text)

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
        self.assertEqual(graded["broken"], 2)
        self.assertEqual(graded["score"], max(graded["fixed"] - 2, 0))

    def test_replies_must_be_drafted_not_just_reported(self):
        report = "Nina owes $26.96 at pickup. Jordan: the cinnamon rolls contain milk. Tessa's total is $22.73."
        graded = health_check.grade(self.shipped, self.key, report, None, site=NO_SITE)
        for pid in ("C15", "C18", "C23"):
            self.assertEqual(graded["problems"][pid]["status"], "not fixed", pid)

    def test_judge_cannot_pass_a_reply_missing_the_facts(self):
        # The judge says everything is fixed, but the report has no refund amount, quote or nut warning.
        verdicts = {"problems": {p: {"verdict": "fixed"} for p in reference_fix.JUDGE_IDS}, "false_claims": []}
        graded = health_check.grade(self.shipped, self.key, "Replied to Rosa, Maria and Westside Dental.", verdicts, site=NO_SITE)
        for pid in ("C01", "C04", "C11", "M28"):
            self.assertEqual(graded["problems"][pid]["status"], "not fixed", pid)

    @unittest.skipUnless(HAS_BROWSER, "site checks need Playwright for Python and Chromium")
    def test_full_controls_score_0_and_100(self):
        self.assertEqual(health_check.grade(self.shipped, self.key, "", None)["score"], 0)
        fixed = self.copy("fixed-full")
        report = reference_fix.fix(fixed, self.key)
        verdicts = {"problems": {p: {"verdict": "fixed"} for p in reference_fix.JUDGE_IDS}, "false_claims": []}
        graded = health_check.grade(fixed, self.key, report, verdicts)
        self.assertEqual(graded["score"], 100, {p: v["why"] for p, v in graded["problems"].items() if v["status"] != "fixed"})
        self.assertEqual(graded["dollars_at_risk_caught"], 100_000)
        self.assertEqual(sum(len(v) for v in graded["broke_something"].values()), 0)


if __name__ == "__main__":
    unittest.main()
