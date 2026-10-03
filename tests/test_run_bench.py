"""The self-run tools: reading each CLI's output, and the integrity check."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_codex_requests_are_priced_one_by_one_at_public_api_prices(self):
        def record(given, cached, out):
            return {"type": "token_usage_record", "payload": {"usage": {
                "input_tokens": given, "cached_input_tokens": cached, "cache_write_input_tokens": 0, "output_tokens": out}}}
        session = [{"type": "session_meta", "payload": {}}, {"type": "turn_context", "payload": {"model": "gpt-6.1-sol"}},
                   record(100_000, 80_000, 1_000), record(300_000, 0, 1_000),
                   {"type": "session_meta", "payload": {}}, {"type": "turn_context", "payload": {"model": "codex-auto-review"}},
                   record(9_000, 0, 100)]
        log = "".join(json.dumps(r) + "\n" for r in run_bench.codex_requests("\n".join(json.dumps(e) for e in session)))
        usage = run_bench.codex_usage(log, "gpt-6.1-sol")
        # 20K uncached at $2/M, 80K cached at $0.10/M and 1K out at $10/M; then a long request at 2x input, 1.5x output
        self.assertAlmostEqual(usage["cost_usd"], 0.058 + 1.215)
        self.assertIn("1 of them over 272K", usage["cost_basis"])
        self.assertIn("codex-auto-review aren't counted", usage["cost_basis"])

    def test_tokens_burned_adds_claudes_cache_counts_and_counts_codexs_cached_input_once(self):
        claude = {"usage": {"input_tokens": 56, "cache_creation_input_tokens": 192_613, "cache_read_input_tokens": 3_542_289,
                            "output_tokens": 84_602}}
        codex = {"usage": {"input_tokens": 1_219_674, "cached_input_tokens": 1_136_128, "output_tokens": 25_417}}
        self.assertEqual(run_bench.tokens_burned(claude), (3_819_560, 84_602))
        self.assertEqual(run_bench.tokens_burned(codex), (1_245_091, 25_417))
        self.assertIsNone(run_bench.tokens_burned({}))

    def test_codex_log_without_requests_is_priced_from_its_totals_at_standard_rates(self):
        totals = {"input_tokens": 1_000_000, "cached_input_tokens": 900_000, "cache_write_input_tokens": 0, "output_tokens": 20_000}
        log = json.dumps({"type": "turn.completed", "usage": totals})
        self.assertAlmostEqual(run_bench.codex_usage(log, "gpt-6.1-sol")["cost_usd"], 0.2 + 0.09 + 0.2)
        self.assertEqual(run_bench.codex_usage(log, "unpriced-model"), {"usage": totals})


class CleanProfileTests(unittest.TestCase):
    def test_claude_runs_without_the_persons_settings_or_the_starting_sessions_variables(self):
        command = run_bench.agent_command("claude", "claude-opus-5-5", Path("."), Path("report.md"), None)
        self.assertEqual(command[command.index("--setting-sources") + 1], "project,local")
        self.assertIn("--strict-mcp-config", command)
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            fake = folder / "claude"   # prints the variables it was given
            fake.write_text('#!/bin/sh\necho "$CLAUDECODE|$CLAUDE_CODE_ENTRYPOINT|$CLAUDE_CONFIG_DIR"\n')
            fake.chmod(0o755)
            session_that_started_it = {"PATH": f"{folder}:{os.environ['PATH']}", "CLAUDECODE": "1",
                                       "CLAUDE_CODE_ENTRYPOINT": "desktop", "CLAUDE_CONFIG_DIR": "/where/the/sign-in/is"}
            with mock.patch.dict(os.environ, session_that_started_it):
                stdout, timing = run_bench.run_agent(["claude", "-p"], folder, "", 30, folder / "agent-log.txt")
        self.assertEqual(stdout.strip(), "||/where/the/sign-in/is")
        self.assertTrue(timing["clean_profile"])


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


class JudgePanelTests(unittest.TestCase):
    def test_a_point_needs_every_judge(self):
        one = {"problems": {"C01": {"verdict": "fixed", "evidence": "reply drafted"}, "M28": {"verdict": "fixed"}},
               "false_claims": ["W39", "L02"]}
        two = {"problems": {"C01": {"verdict": "fixed", "evidence": "names the refund"}, "M28": {"verdict": "not fixed"}},
               "false_claims": ["L02"]}
        both = run_bench.combine_verdicts([one, two])
        self.assertEqual({p: v["verdict"] for p, v in both["problems"].items()}, {"C01": "fixed", "M28": "not fixed"})
        self.assertEqual(both["false_claims"], ["L02"])
        self.assertIn("agreed on 1 of 2", run_bench.judges_line(["judge-a", "judge-b"], [one, two]))

    def test_one_judge_keeps_its_own_verdicts(self):
        one = {"problems": {"C01": {"verdict": "fixed", "evidence": "reply drafted"}}, "false_claims": ["W39"]}
        self.assertEqual(run_bench.combine_verdicts([one]), one)
        self.assertEqual(run_bench.judges_line(["judge-a"], [one]), "judge-a")

if __name__ == "__main__":
    unittest.main()
