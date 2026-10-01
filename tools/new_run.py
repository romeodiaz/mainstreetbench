#!/usr/bin/env python3
"""Set up one benchmark attempt outside the repository, in the folder layout from docs/running-the-bench.md.

    python3 tools/new_run.py --model sol

Builds ../runs/<date>-<model>-v0.7-NN/workspace (the only folder the AI sees), moves the answer key to
../keys/<run>/, creates ../evidence/<run>/, and prints what to give the AI and what to deny it.
"""

import argparse
import datetime as dt
import json
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION = "v0.7"


def create_run(model: str, base: Path, hidden: Path | None = None) -> dict:
    """Build a run outside the repository. Returns its paths and the source commit.

    With hidden, the workspace and the key go into two unrelated random folders under it instead of
    base/runs and base/keys, so nothing next to the AI's folder points at the answers."""
    base = base.expanduser().resolve()
    if base == REPO or REPO in base.parents:
        raise SystemExit("The run folder must be outside the repository, or the AI could read the answers")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    if subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.strip():
        raise SystemExit("The repository has uncommitted changes; commit or stash them so the run matches a commit")
    label = "".join(ch if ch.isalnum() or ch in "-." else "-" for ch in model.lower()).strip("-") or "model"
    stem = f"{dt.date.today().isoformat()}-{label}-{VERSION}"
    number = 1
    while (base / "runs" / f"{stem}-{number:02d}").exists():
        number += 1
    run = f"{stem}-{number:02d}"
    run_dir, key_dir, evidence = base / "runs" / run, base / "keys" / run, base / "evidence" / run
    if hidden:
        hidden = hidden.expanduser().resolve()
        if hidden == REPO or REPO in hidden.parents:
            raise SystemExit("The hidden folder must be outside the repository")
        run_dir, key_dir = hidden / secrets.token_hex(6), hidden / secrets.token_hex(6) / "key"
    run_dir.mkdir(parents=True)
    subprocess.run([sys.executable, str(REPO / "tasks" / "health-check" / "build.py"), "--out", str(run_dir / "workspace")],
                   check=True, capture_output=True)
    key_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(run_dir / "workspace-key"), str(key_dir))
    shutil.move(str(run_dir / "workspace-prompt.txt"), str(run_dir / "prompt.txt"))
    evidence.mkdir(parents=True)
    info = {"run": run, "model": model, "version": VERSION, "source_commit": commit,
            "created": dt.datetime.now().isoformat(timespec="seconds")}
    (evidence / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return {**info, "base": base, "workspace": run_dir / "workspace", "prompt": run_dir / "prompt.txt",
            "key": key_dir, "evidence": evidence}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="Short label, e.g. sol, opus, opus-sol")
    parser.add_argument("--base", type=Path, default=REPO.parent,
                        help="Parent folder holding runs/, keys/ and evidence/ (default: next to the repo)")
    args = parser.parse_args()
    r = create_run(args.model, args.base)
    print(f"""Run {r['run']} is ready (source commit {r['source_commit'][:7]}).

Give the AI:
  working folder  {r['workspace']}
  prompt (as is)  {r['prompt']}

Deny the AI:
  {REPO}
  {r['base'] / 'keys'}
  {r['base'] / 'evidence'}
  other folders in {r['base'] / 'runs'}, prior sessions and memories

Afterwards:
  1. Save the AI's final message as {r['evidence'] / 'owner-report.md'}
  2. Freeze a copy:  cp -R {r['workspace']} {r['evidence'] / 'frozen'}
  3. Grade in a sandbox, from the repo:
     python3 evaluators/health_check.py --workspace {r['evidence'] / 'frozen'} --key {r['key']} \\
       --report {r['evidence'] / 'owner-report.md'} --judge-bundle {r['evidence'] / 'judge.json'} --out {r['evidence'] / 'grade.json'}
""")


if __name__ == "__main__":
    main()
