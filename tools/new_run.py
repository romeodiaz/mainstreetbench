#!/usr/bin/env python3
"""Set up one benchmark attempt outside the repository, in the folder layout from docs/running-the-bench.md.

    python3 tools/new_run.py --model sol

Builds ../runs/<date>-<model>-v0.6-NN/workspace (the only folder the AI sees), moves the answer key to
../keys/<run>/, creates ../evidence/<run>/, and prints what to give the AI and what to deny it.
"""

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION = "v0.6"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="Short label, e.g. sol, opus, opus-sol")
    parser.add_argument("--base", type=Path, default=REPO.parent,
                        help="Parent folder holding runs/, keys/ and evidence/ (default: next to the repo)")
    args = parser.parse_args()
    base = args.base.expanduser().resolve()
    if base == REPO or REPO in base.parents:
        parser.error("--base must be outside the repository, or the AI could read the answers")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    if dirty:
        parser.error("The repository has uncommitted changes; commit or stash them so the run matches a commit")

    stem = f"{dt.date.today().isoformat()}-{args.model}-{VERSION}"
    number = 1
    while (base / "runs" / f"{stem}-{number:02d}").exists():
        number += 1
    run = f"{stem}-{number:02d}"
    run_dir, key_dir, evidence = base / "runs" / run, base / "keys" / run, base / "evidence" / run
    run_dir.mkdir(parents=True)
    subprocess.run([sys.executable, str(REPO / "tasks" / "health-check" / "build.py"), "--out", str(run_dir / "workspace")],
                   check=True, capture_output=True)
    key_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(run_dir / "workspace-key"), str(key_dir))
    shutil.move(str(run_dir / "workspace-prompt.txt"), str(run_dir / "prompt.txt"))
    evidence.mkdir(parents=True)
    (evidence / "run.json").write_text(json.dumps({"run": run, "model_label": args.model, "version": VERSION,
                                                   "source_commit": commit, "created": dt.datetime.now().isoformat()},
                                                  indent=2) + "\n")
    print(f"""Run {run} is ready (source commit {commit[:7]}).

Give the AI:
  working folder  {run_dir / 'workspace'}
  prompt (as is)  {run_dir / 'prompt.txt'}

Deny the AI:
  {REPO}
  {base / 'keys'}
  {base / 'evidence'}
  other folders in {base / 'runs'}, prior sessions and memories

Afterwards:
  1. Save the AI's final message as {evidence / 'owner-report.md'}
  2. Freeze a copy:  cp -R {run_dir / 'workspace'} {evidence / 'frozen'}
  3. Grade in a sandbox, from the repo:
     python3 evaluators/health_check.py --workspace {evidence / 'frozen'} --key {key_dir} \\
       --report {evidence / 'owner-report.md'} --judge-bundle {evidence / 'judge.json'} --out {evidence / 'grade.json'}
""")


if __name__ == "__main__":
    main()
