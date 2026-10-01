# Instructions for the AI running this benchmark

Someone asked you to run Main Street Bench on an AI model and report the score. Follow these steps exactly. **You are the referee, not a contestant:** this repository contains the answers, so you must not attempt the task, help the tested model, or edit its work.

## 1. Check what you need

- Python 3.10 or newer.
- The command-line tool for the model to test:
  - **Claude models:** Claude Code (`claude`). Use the model id it accepts, e.g. `claude-opus-5-5`.
  - **OpenAI models:** Codex CLI (`codex`). Use the model id it accepts.
  - **Anything else:** any tool that takes a prompt on standard input, works in the current folder and prints its final answer. Use `--agent custom --command "..."`.
- If the tool isn't installed or signed in, tell the person exactly what to install or sign into, and stop. Don't substitute a different model.

Command-line flags change between versions. If the preset fails on a flag, check `claude --help` or `codex exec --help` and pass the working command with `--agent custom --command`.

## 2. Run it

From this repository's folder:

```sh
python3 tools/run_bench.py --install --agent codex  --model MODEL_ID [--effort medium]   # OpenAI models
python3 tools/run_bench.py --install --agent claude --model MODEL_ID [--effort medium]   # Claude models
```

**Reasoning effort:** if the person names one ("gpt-6.1-sol medium", "Opus on high"), add `--effort medium` (or whatever they said). Never drop it: the same model at a different effort is a different result. If the tool rejects the setting, tell the person rather than running without it. If they don't name one, leave it out and tell the person the tool's default effort was used.

Add a judge for the 8 problems that need reading, ideally a different model from the one being tested:

```sh
  --judge claude --judge-model claude-sonnet-5-5
```

Without a judge, those 8 count as not fixed and the scorecard says so.

The run takes up to 45 minutes (`--minutes` changes it). It builds a fresh copy of the bakery in `../MainStreetBench-runs/runs/`, starts the tested model there with the owner's message, waits, grades the result and prints a scorecard. Leave it alone while it runs.

## 3. Rules

- **Don't solve, hint or fix.** Never read the answer keys to the person or the tested model. Never edit the workspace before grading. The owner's message is sent unchanged.
- **One run, reported as is.** Don't rerun to get a better number. If you run it again, report every score.
- **Report failures honestly.** If the tool crashed, ran out of time or hit a usage limit, say so next to the score.
- **It's a self-run.** Scores from this script aren't verified by the maintainers, and the tested model could in principle read files outside its folder. Say "self-run" when you report the score.
- **Note the date.** This benchmark is public. A model trained after its release may have seen it, so say when the model was released.

## 4. Report back

Show the person the scorecard (`../MainStreetBench-runs/evidence/RUN/SCORECARD.md`) in plain English:

- the score out of 100;
- the dollars at risk caught;
- whether it broke anything;
- time and cost, if the tool reported cost;
- what it was best and worst at, by area;
- that it's a self-run, and the model's release date.

The tested model's own report to the owner is in `owner-report.md` in the same folder, if the person wants to read it.
