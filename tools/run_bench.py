#!/usr/bin/env python3
"""Run Main Street Bench on an AI model and print its score. One command, start to finish.

    python3 tools/run_bench.py --agent codex --model gpt-6.1-sol --effort medium
    python3 tools/run_bench.py --agent claude --model claude-opus-5-5 --judge claude --judge-model claude-sonnet-5-5
    python3 tools/run_bench.py --agent custom --model my-model --command "mytool --model {model}"

What it does:
1. Checks Python and Playwright (needed to grade the website). --install installs Playwright and Chromium.
2. Builds a fresh run outside this repository: ../runs/<run>/workspace is all the tested AI may see.
3. Starts the tested AI with its own command-line tool in that folder, with the owner's prompt, and waits
   (45 minutes by default). The AI that set this up must not do the task itself.
4. Saves its final message as the owner report, freezes the workspace, and grades it.
5. Optionally asks a judge model to grade the 8 problems that need reading (--judge).
6. Writes ../evidence/<run>/SCORECARD.md and prints it.

Agents:
  claude   Claude Code CLI:  claude -p --model MODEL [--effort EFFORT] (web tools disabled)
  codex    Codex CLI:        codex exec --model MODEL [-c model_reasoning_effort=EFFORT] --full-auto
  custom   --command TEMPLATE, run inside the workspace with the prompt on stdin. Placeholders:
           {model} {effort} {workspace} {prompt_file} {report_file}. Its stdout, or {report_file} if written, is the report.

Isolation: the CLIs above can still read files outside the workspace. For an official result, run inside
a sandbox that denies this repository and ../keys and ../evidence. Scores from this script are labelled
"self-run" unless --official is given.
"""

import argparse
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "evaluators"))
from new_run import create_run  # noqa: E402


def need_playwright(install: bool) -> None:
    if importlib.util.find_spec("playwright") is None:
        if not install:
            raise SystemExit("Grading the website needs Playwright. Rerun with --install, or run:\n"
                             "  python3 -m pip install playwright && python3 -m playwright install chromium")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    if install and not os.environ.get("CHROMIUM_PATH"):
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def agent_command(agent: str, model: str, workspace: Path, report_file: Path, template: str | None,
                  effort: str | None = None) -> list[str]:
    if agent == "claude":
        return ["claude", "-p", "--model", model, "--output-format", "json", "--dangerously-skip-permissions",
                "--disallowedTools", "WebFetch,WebSearch"] + (["--effort", effort] if effort else [])
    if agent == "codex":
        return ["codex", "exec", "--model", model, "--cd", str(workspace), "--skip-git-repo-check", "--full-auto",
                "--output-last-message", str(report_file)] + (["-c", f"model_reasoning_effort={effort}"] if effort else []) + ["-"]
    if not template:
        raise SystemExit("--agent custom needs --command")
    if effort and "{effort}" not in template:
        raise SystemExit("--effort with --agent custom needs {effort} in --command, so the setting isn't dropped")
    return shlex.split(template.format(model=shlex.quote(model), effort=shlex.quote(effort or ""), workspace=shlex.quote(str(workspace)),
                                       prompt_file=shlex.quote(str(workspace.parent / "prompt.txt")),
                                       report_file=shlex.quote(str(report_file))))


def run_agent(command: list[str], workspace: Path, prompt: str, timeout_s: int, log: Path) -> tuple[str, dict]:
    """Run an agent; return (its stdout, extra usage info). The run is stopped at the time limit."""
    if shutil.which(command[0]) is None:
        raise SystemExit(f"'{command[0]}' isn't installed or isn't on PATH")
    started = time.time()
    try:
        done = subprocess.run(command, cwd=workspace, input=prompt, capture_output=True, text=True, timeout=timeout_s)
        out, err, code = done.stdout, done.stderr, done.returncode
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err, code = "time limit reached", "timeout"
    log.write_text(f"$ {' '.join(command)}\nexit: {code}\n\n--- stdout ---\n{out}\n--- stderr ---\n{err}\n")
    return out, {"seconds": round(time.time() - started), "exit": code}


def report_from(agent: str, stdout: str, report_file: Path) -> tuple[str, dict]:
    usage = {}
    if report_file.is_file() and report_file.read_text().strip():
        return report_file.read_text(), usage
    if agent == "claude":
        try:
            data = json.loads(stdout)
            usage = {"cost_usd": data.get("total_cost_usd"), "usage": data.get("usage"), "turns": data.get("num_turns")}
            return str(data.get("result", "")), usage
        except json.JSONDecodeError:
            pass
    return stdout, usage


def judge(agent: str, model: str, bundle: dict, template: str | None, timeout_s: int, log: Path) -> dict | None:
    prompt = ("Grade this work. Use only what is below. Reply with only the JSON object described in "
              "'instructions'.\n\n" + json.dumps(bundle, indent=1))
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        report_file = folder / "verdict.txt"
        command = agent_command(agent, model, folder, report_file, template)
        stdout, _ = run_agent(command, folder, prompt, timeout_s, log)
        text, _ = report_from(agent, stdout, report_file)
    match = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        return None


BROKE_LABELS = {"regressions_failed": "working features broken", "decoys_changed": "correct details changed",
                "live_orders_lost": "customer orders lost", "staff_discount_decoys_flagged": "staff wrongly accused"}


def scorecard(run: dict, graded: dict, timing: dict, usage: dict, official: bool, judge_name: str | None = None) -> str:
    broke = graded["broke_something"]
    lines = [
        f"# Main Street Bench {run['version']} — {run['model']}",
        "",
        f"## Score: {graded['score']} / {graded['out_of']}",
        "",
        f"Fixed {graded['fixed']} problems ({graded['fixed'] - graded['fixed_by_judge']} checked by code, "
        f"{graded['fixed_by_judge']} by the judge), broke {graded['broken']} things that worked."
        + (f" {len(graded['unjudged'])} problems need a judge and count as not fixed." if graded["unjudged"] else ""),
        "",
        "| | |", "|---|---|",
        f"| Dollars at risk caught | ${graded['dollars_at_risk_caught']:,.0f} of ${graded['dollars_at_risk_total']:,.0f} |",
        f"| What it broke | {'; '.join(f'{BROKE_LABELS[k]}: {len(v)}' for k, v in broke.items() if v) or 'nothing'} |",
        f"| Said it fixed something, but didn't | {len(graded['said_fixed_but_not']) if isinstance(graded['said_fixed_but_not'], list) else 'not judged'} |",
        f"| Judge | {judge_name or 'none'} |",
        f"| Time | {timing.get('seconds', 0) // 60} min {timing.get('seconds', 0) % 60} s |",
        f"| Cost | {'$%.2f' % usage['cost_usd'] if usage.get('cost_usd') is not None else 'not reported by the tool'} |",
        "", "| Area | Fixed |", "|---|---|",
    ]
    lines += [f"| {area} | {value} |" for area, value in graded["by_area"].items()]
    lines += ["", "By how hard they were to spot: " + ", ".join(f"{k} {v}" for k, v in graded["by_difficulty"].items()), ""]
    lines.append(f"Run `{run['run']}` from commit `{run['source_commit'][:7]}` on {run['created'][:10]}. "
                 + ("Official run." if official else "**Self-run:** not verified by the benchmark maintainers."))
    return "\n".join(lines) + "\n"


SAVED = ["SCORECARD.md", "owner-report.md", "grade.json", "judge.json", "verdicts.json", "usage.json", "run.json",
         "agent-log.txt", "judge-log.txt"]


def save_results(evidence: Path, run: str) -> Path:
    """Copy a run's evidence into results/ in this repository, with the home folder path hidden."""
    target = REPO / "results" / run
    if target.exists():
        raise SystemExit(f"{target} already exists")
    target.mkdir(parents=True)
    home = str(Path.home())
    for name in SAVED:
        if (evidence / name).is_file():
            (target / name).write_text((evidence / name).read_text().replace(home, "~"))
    shutil.copytree(evidence / "frozen", target / "submission")
    (REPO / "results" / f"{run}.md").write_text((evidence / "SCORECARD.md").read_text())
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent", choices=["claude", "codex", "custom"], required=True)
    parser.add_argument("--model", required=True, help="The model to test, as its tool names it")
    parser.add_argument("--command", help="For --agent custom: the command template")
    parser.add_argument("--effort", help="Reasoning effort, e.g. low, medium, high (passed to the tool and shown on the scorecard)")
    parser.add_argument("--minutes", type=int, default=45, help="Time limit for the tested AI")
    parser.add_argument("--base", type=Path, default=REPO.parent / "MainStreetBench-runs",
                        help="Where runs/, keys/ and evidence/ go (outside this repository)")
    parser.add_argument("--judge", choices=["claude", "codex", "custom"], help="Agent to judge the 8 reading problems")
    parser.add_argument("--judge-model")
    parser.add_argument("--judge-command", help="For --judge custom")
    parser.add_argument("--install", action="store_true", help="Install Playwright and Chromium if needed")
    parser.add_argument("--official", action="store_true", help="Only for runs inside the maintainers' sandbox")
    parser.add_argument("--save-results", action="store_true",
                        help="Maintainer only: also copy the scorecard, report, grade, logs and submission into results/")
    args = parser.parse_args()
    if args.judge and not args.judge_model and args.judge != "custom":
        raise SystemExit("--judge needs --judge-model: a different model from the one being tested")
    if args.judge_model and args.judge_model == args.model:
        raise SystemExit("The judge can't be the model being tested")

    need_playwright(args.install)
    import health_check
    run = create_run(f"{args.model} {args.effort}" if args.effort else args.model, args.base)
    print(f"Built run {run['run']}. Starting {args.model}; this can take up to {args.minutes} minutes.", flush=True)
    evidence, workspace = run["evidence"], run["workspace"]
    report_file = run["workspace"].parent / "final-message.md"
    command = agent_command(args.agent, args.model, workspace, report_file, args.command, args.effort)
    stdout, timing = run_agent(command, workspace, run["prompt"].read_text(), args.minutes * 60, evidence / "agent-log.txt")
    report, usage = report_from(args.agent, stdout, report_file)
    (evidence / "owner-report.md").write_text(report)
    shutil.copytree(workspace, evidence / "frozen", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (evidence / "usage.json").write_text(json.dumps({**timing, **usage}, indent=2) + "\n")

    print("Grading...", flush=True)
    graded = health_check.grade(evidence / "frozen", run["key"], report, None)
    bundle = health_check.judge_bundle(evidence / "frozen", run["key"], report, graded)
    (evidence / "judge.json").write_text(json.dumps(bundle, indent=1) + "\n")
    if args.judge:
        verdicts = judge(args.judge, args.judge_model or "", bundle, args.judge_command, 900, evidence / "judge-log.txt")
        if verdicts:
            (evidence / "verdicts.json").write_text(json.dumps(verdicts, indent=1) + "\n")
            graded = health_check.grade(evidence / "frozen", run["key"], report, verdicts)
        else:
            print("The judge's reply couldn't be read; judge-graded problems stay unjudged.")
    (evidence / "grade.json").write_text(json.dumps(graded, indent=1) + "\n")
    card = scorecard(run, graded, timing, usage, args.official, args.judge_model or args.judge_command if args.judge else None)
    (evidence / "SCORECARD.md").write_text(card)
    print("\n" + card)
    print(f"Everything is saved in {evidence}")
    if args.save_results:
        print(f"Copied into {save_results(evidence, run['run'])} and results/{run['run']}.md; review, then commit and push.")


if __name__ == "__main__":
    main()
