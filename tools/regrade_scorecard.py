#!/usr/bin/env python3
"""Rewrite results/<run>.md from a saved regrade (maintainer only).

    python3 tools/regrade_scorecard.py --grader v0.9.2 results/<run> [results/<run> ...]

A regrade re-checks a saved submission with a corrected grader and writes
results/<run>/regrade.json beside the original grade.json. This rebuilds the
public scorecard from that regrade, so the page a reader opens shows the same
score as the README. results/<run>/SCORECARD.md is left alone: it stays as the
scorecard written when the run was first graded.

Two lines are corrected against the regrade rather than copied:
- "Said it fixed something, but didn't" drops problems the regrade now counts as fixed.
- Integrity lists only personal instruction files the tested tool reads.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluators"))
import integrity  # noqa: E402
from run_bench import scorecard  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--grader", required=True, help="Version of the grader that produced regrade.json, e.g. v0.9.2")
parser.add_argument("runs", nargs="+", type=Path, help="results/<run> folders holding regrade.json")
args = parser.parse_args()

for folder in args.runs:
    load = lambda name: json.loads((folder / name).read_text())  # noqa: E731
    run, usage, checked, first, graded = (load(n) for n in ("run.json", "usage.json", "integrity.json", "grade.json", "regrade.json"))
    original = (folder / "SCORECARD.md").read_text()
    judge = re.search(r"^\| Judge \| (.+) \|$", original, re.M).group(1)

    if isinstance(graded["said_fixed_but_not"], list):
        graded["said_fixed_but_not"] = [p for p in graded["said_fixed_but_not"] if graded["problems"][p]["status"] != "fixed"]
    agent = "claude" if run["model"].startswith("claude") else "codex"
    reads = integrity.READ_BY[agent] - ({"~/.codex/AGENTS.md"} if usage.get("clean_profile") else set())
    checked["personal_instructions_found"] = [p for p in checked["personal_instructions_found"] if p in reads]

    card = scorecard(run, graded, {"seconds": usage["seconds"]}, usage, False, None if judge == "none" else judge, checked)
    note = (f"Regraded with the {args.grader} grader; first graded {first['score']}. The model's work is unchanged. "
            f"The scorecard from the first grading is kept in [{folder.name}/SCORECARD.md]({folder.name}/SCORECARD.md).")
    head, rest = card.split("\n\n", 2)[:2], card.split("\n\n", 2)[2]
    target = folder.parent / f"{folder.name}.md"
    target.write_text("\n\n".join(head + [note, rest]))
    print(f"{target}: {first['score']} -> {graded['score']}")
