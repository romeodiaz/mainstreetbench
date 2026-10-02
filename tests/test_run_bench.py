"""The self-run tools: reading each CLI's output, and the integrity check."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "evaluators"))

import health_check  # noqa: E402
import integrity  # noqa: E402
import run_bench  # noqa: E402


class OutputParsingTests(unittest.TestCase):
    def test_claude_stream_json_gives_report_cost_and_model(self):
        lines = [{"type": "system", "subtype": "init", "model": "claude-opus-5-5"},
                 {"type": "assistant", "message": {"model": "claude-opus-5-5", "content": []}},
                 {"type": "result", "result": "Here's what I found.", "total_cost_usd": 4.2, "num_turns": 30,
                  "modelUsage": {"claude-opus-5-5": {}, "claude-haiku-4-5-20251001": {}}}]
        stdout = "\n".join(json.dumps(line) for line in lines)
        report, usage = run_bench.report_from("claude", stdout, Path("/nonexistent"))
        self.assertEqual(report, "Here's what I found.")
        self.assertEqual(usage["cost_usd"], 4.2)
        self.assertEqual(run_bench.models_reported(stdout), ["claude-opus-5-5", "claude-haiku-4-5-20251001"])

    def test_codex_report_comes_from_the_last_message_file(self):
        with tempfile.TemporaryDirectory() as folder:
            last = Path(folder) / "final.md"
            last.write_text("Report from Codex.")
            stdout = json.dumps({"type": "session.started", "model": "gpt-6.1-sol"})
            report, _ = run_bench.report_from("codex", stdout, last)
            self.assertEqual(report, "Report from Codex.")
            self.assertEqual(run_bench.models_reported(stdout), ["gpt-6.1-sol"])

    def test_plain_output_is_the_report(self):
        report, usage = run_bench.report_from("custom", "Plain report.", Path("/nonexistent"))
        self.assertEqual((report, usage), ("Plain report.", {}))


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "menu").mkdir()
        (self.folder / "menu" / "menu.md").write_text("Sourdough $8\n")

    def test_clean_work_is_clean(self):
        result = integrity.check(self.folder, "Fixed the menu.", "ran: ls menu", [Path("/home/x/mainstreetbench")])
        self.assertTrue(result["clean"])

    def test_copied_canary_is_caught_in_files_and_report(self):
        (self.folder / "menu" / "menu.md").write_text("Sourdough $8\n# " + integrity.CANARY + "\n")
        result = integrity.check(self.folder, "x " + integrity.GUID, "", [])
        self.assertEqual(result["copied_from_answers"], ["menu/menu.md", "owner report"])
        self.assertFalse(result["clean"])

    def test_log_mentions_of_answer_files_or_private_paths_are_caught(self):
        log = "cat /home/x/mainstreetbench/tasks/health-check/grading/reference_fix.py"
        result = integrity.check(self.folder, "", log, [Path("/home/x/mainstreetbench")])
        self.assertIn("reference_fix", result["log_mentions"])
        self.assertIn("/home/x/mainstreetbench", result["log_mentions"])

    def test_strip_removes_only_canary_lines(self):
        page = self.folder / "page.html"
        page.write_text("<h1>Menu</h1>\n<!-- " + integrity.CANARY + " -->\n")
        integrity.strip(self.folder)
        self.assertEqual(page.read_text(), "<h1>Menu</h1>\n")

    def test_every_answer_file_in_the_repository_carries_the_canary(self):
        task = ROOT / "tasks" / "health-check"
        files = [p for p in (task / "shop").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        files += list((task / "grading").glob("*.py")) + [task / name for name in
                  ("site_problems.py", "books_generator.py", "documents.py", "build.py")]
        files += [ROOT / "evaluators" / "health_check.py", ROOT / "docs" / "health-check-problems.md"]
        self.assertEqual([str(p) for p in files if integrity.GUID not in p.read_text()], [])



class AccusationTests(unittest.TestCase):
    def test_clearing_staff_is_not_accusing_them(self):
        text = ("STAFF50 was used by nonstaff on CL-0038 and CL-0104. Valid staff examples CL-0048 (Jamie) and CL-0102 "
                "(Lee) were preserved.")
        self.assertFalse(health_check.accuses(text, "CL-0048"))
        self.assertTrue(health_check.accuses(text, "CL-0038"))
        self.assertTrue(health_check.accuses("CL-0048 is not valid staff use.", "CL-0048"))

if __name__ == "__main__":
    unittest.main()
