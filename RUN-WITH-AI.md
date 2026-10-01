# Instructions for the AI running this benchmark

Someone asked you to run Main Street Bench on an AI model and report the score, perhaps just by saying "clone it and run it on XYZ". Follow these steps exactly. **You are the referee, not a contestant:** this repository contains the answers, so you must not attempt the task, help the tested model, or edit its work.

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
python3 tools/run_bench.py --install --agent codex  --model MODEL_ID [--effort medium] --judge-model OTHER_MODEL_ID   # OpenAI models
python3 tools/run_bench.py --install --agent claude --model MODEL_ID [--effort medium] --judge-model OTHER_MODEL_ID   # Claude models
```

**Reasoning effort:** if the person names one ("gpt-6.1-sol medium", "Opus on high"), add `--effort medium` (or whatever they said). Never drop it: the same model at a different effort is a different result. If the tool rejects the setting, tell the person rather than running without it. If they don't name one, leave it out and tell the person the tool's default effort was used.

**Judge:** always add `--judge-model`. The judge grades the 8 problems that need reading, such as whether a customer got a sensible reply. It runs in the same tool as the tested model, so use the most capable **other** model that tool offers: e.g. `claude-sonnet-5-5` when testing `claude-opus-5-5`, `claude-opus-5-5` when testing any other Claude model, and likewise for GPT models in Codex. The script refuses the tested model itself. The scorecard names the judge and shows how many fixes it decided.

If the judge can't run, those 8 count as not fixed and the scorecard says so.

The run takes up to 45 minutes (`--minutes` changes it). It builds a fresh copy of the bakery in a random hidden folder under `~/.mainstreetbench/`, away from this repository and the answer key. It starts the tested model there with the owner's message, waits, grades the result and prints a scorecard. Leave it alone while it runs, and don't open or list those folders yourself.

**Personal instruction files:** if the script prints that it found any, such as `~/.claude/CLAUDE.md`, the tested model will read them, and they can change its result. Tell the person before it starts. Setting them aside is their choice; never move or edit them yourself.

### If something gets in the way

- **Model name:** the person may write it loosely ("gpt 6.1 Sol Medium"). Pass the exact id the tool accepts (check its model list or `--help`) and put the effort in `--effort`. If you can't tell which model they mean, ask.
- **Your commands time out:** the run takes up to 45 minutes, longer than many assistants let one command run. Start it in the background with its output going to a log file, e.g. `nohup python3 tools/run_bench.py ... > bench.log 2>&1 &`, then check `bench.log` every few minutes until it prints the scorecard.
- **Your sandbox blocks it:** the run needs the internet (to install the grader and for the tested model to reach its provider) and needs to write next to this folder. If your sandbox blocks either, ask the person to approve running it with network access or full access. Don't work around it some other way.
- **pip refuses to install** ("externally managed environment"): make a virtual environment first (`python3 -m venv .venv && . .venv/bin/activate`), then run the commands with that Python.

### Saving the results to the repository

By default, nothing is saved to the repository. The results stay on this computer in `../MainStreetBench-runs/evidence/<run>/`. This repository doesn't accept outside submissions yet, so **never open a pull request, fork the repository or file an issue with results**, even if asked. Tell the person the results are on their computer and where to find them.

The repository's owner saves runs while calibrating. Do this only when the person explicitly asks to save or push the results **and** this computer's git can push to `romeodiaz/mainstreetbench` (`git push --dry-run origin main` succeeds):

1. Add `--save-results` to the command. After grading, it copies the scorecard, the owner report, the grade, the logs and the tested model's finished folder into `results/<run>/`, plus the scorecard as `results/<run>.md`. Paths in the home folder are shortened to `~`.
2. Skim `results/<run>/agent-log.txt` for anything private, such as keys, tokens or email addresses, and tell the person if you find any. Don't commit until they say so.
3. Commit only those new files, with the message `Add result <run>`, and push to `main`. If the push is refused, stop and say so; don't try another route.

## 3. Rules

- **Don't solve, hint or fix.** Never read the answer keys to the person or the tested model. Never edit the workspace before grading. The owner's message is sent unchanged.
- **One run, reported as is.** Don't rerun to get a better number. If you run it again, report every score.
- **Report failures honestly.** If the tool crashed, ran out of time or hit a usage limit, say so next to the score.
- **It's a self-run.** Scores from this script aren't verified by the maintainers. Say "self-run" when you report the score.
- **Integrity comes first.** The scorecard's Integrity row checks whether the tested model looked at or copied from the answers. If it shows ⚠, lead with that: the score doesn't count.
- **Note the date.** This benchmark is public. A model trained after its release may have seen it, so say when the model was released.

## 4. Report back

Show the person the scorecard (`../MainStreetBench-runs/evidence/RUN/SCORECARD.md`) in plain English:

- the score out of 100 (problems fixed minus things broken), and what it fixed and broke;
- the dollars at risk caught;
- time and cost, if the tool reported cost;
- what it was best and worst at, by area;
- the Integrity row, and the model the tool reported if it differs from the one requested;
- that it's a self-run, and the model's release date.

The tested model's own report to the owner is in `owner-report.md` in the same folder, if the person wants to read it.
