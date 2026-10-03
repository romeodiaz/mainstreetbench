<h1 align="center"><img src="docs/images/logo-github.png" alt="Main Street Bench" width="420"></h1>

> **AI assistants:** if someone asked you to run Main Street Bench on a model, follow [RUN-WITH-AI.md](RUN-WITH-AI.md) step by step. You are only the referee: this repository holds the answers, so never work on the bakery task yourself.

How well can an AI look after a small business? Main Street Bench hands an AI everything for a neighborhood bakery, with 100 hidden problems, and scores what it fixes and what it breaks.

## Test any AI in one sentence

Open the coding mode of your AI app in an empty folder. In Claude desktop that's the **Code** tab; in ChatGPT desktop it's **Codex**. Then paste:

> Clone https://github.com/romeodiaz/mainstreetbench and run Main Street Bench on **gpt-6.1-sol** at **medium** effort. Give me the score.

Swap in the model and effort level you want to test (for example **claude-opus-5-5** at **high**). Approve the assistant's requests to run commands, and come back in about an hour.

You get a scorecard with:
- the score out of 100;
- what it fixed and what it broke;
- dollars at risk caught, out of $100,000;
- time and cost.

Your assistant only referees: it starts the model you named in its own folder, then grades the result. The scorecard also checks that the model didn't peek at the answers. Results stay on your computer, and are labelled **self-run**. This repository isn't taking outside submissions yet.

### What you need

- **The tested model's app, signed in on this computer.** That's Claude Code for Claude models, or the Codex CLI for GPT models. Your assistant can install it; you sign in once.
- **A paid plan with room for one long job.** A run takes about 15 minutes of the model's work (it's stopped at 45), plus a little for the judges of 10 of the problems: one model from each of Claude Code and Codex that you have installed and signed in.
- **The basics:** Python 3.10+, git, about 1 GB of disk space and an internet connection. Your assistant checks these and installs what's missing.
- **Your computer awake** for about an hour. It's checked on Linux and should work on a Mac. On Windows, if it fails, ask your assistant to use WSL.

## What the AI is asked to do

It gets [the bakery's folder](example-workspace/) and this message from the owner, word for word:

> Hi! I own Corner Loaf Bakery, a small neighborhood bakery.
>
> Something feels off with the business lately, and I can't put my finger on it. I've attached [a folder](example-workspace/) with everything for the business: our ordering website, September's books, the menu and allergen sheet, our policies, our online listing and the shop's emails.
>
> Could you go through all of it? Please fix whatever you can, but don't break anything that's working. Customers have real orders on the website, so please don't lose any of them. If something needs me to sort it out, like money we're owed, tell me exactly what's wrong and which order, payment or invoice numbers to look at.
>
> When you're done, explain it to me like I'm not a tech person: what you found, what you fixed, and what I still need to do.

[`example-workspace/`](example-workspace/) is that folder exactly as the AI receives it, including a short [FOLDER-GUIDE](example-workspace/FOLDER-GUIDE.md) note. Each run starts from a fresh copy.

**100 problems** are planted across those files, and nothing lists them. They range from "the baguette is marked gluten-free" to "anyone can cancel anyone's order by typing an order number" to "a payout never reached the bank". [See all 100 in plain English.](docs/health-check-problems.md)

## How it's scored

**The score is problems fixed, minus things broken, out of 100.** "Broken" means:
- a feature that worked and now doesn't;
- a correct detail it "fixed" anyway;
- a customer order it lost;
- a staff member wrongly accused of misusing their discount.

A careless model that fixes 70 problems but breaks 6 things scores 64.

**90 problems are checked by code:**
- the website is clicked through in a real browser;
- the books and documents are checked against an answer key.

The other 10, such as whether a customer got a sensible reply, are decided by a judge model against a short yes/no checklist. Where a reply needs a specific fact, such as the right refund amount, code checks that first. The scorecard names the judge and shows how many points it decided. Every tested model gets the same judges: one model from each of Claude Code and Codex that is installed, and with both a point needs both.

The design follows [Bug Hunt Bench](https://github.com/phuryn/bug-hunt-bench): many independent planted problems, no list of what to find, and a judge only where a check can't be exact.

**The grading is verified:**
- an untouched bakery scores **0**;
- a complete fix scores **100**;
- each of the 31 website problems is shown, one at a time, to fail only its own check.

The problems split 4 obvious, 37 needing cross-checking, and 59 hidden, so expect scores well below 100. More detail: [the grader](tasks/health-check/) and [running it by hand](docs/running-the-bench.md).

## Results so far

The current version is **v0.10**: the same bakery and the same 100 problems as v0.9, but the shop now sells about $100,000 a month, so September's books hold about 2,000 sales instead of 1,217 ([why](docs/health-check-problems.md#decisions)). No model has been run on v0.10 yet.

The rows below are from **v0.9**, graded with the v0.9.3 grader. v0.9.1 and v0.9.2 corrected grading flaws only, and v0.9.3 only re-set the [dollars at risk](docs/health-check-problems.md#dollars-at-risk) to add up to $100,000, so the four rows compare directly with each other, but not with v0.10 scores (the Opus run names say v0.9.1 because that grader was current when they ran). Charts of these scores, beside five public indexes for the same models, are at [workwithguava.com/mainstreetbench](https://workwithguava.com/mainstreetbench).

v0.9 is calibrated so a cheap model has room to fall short: problems that GPT-6.1 Sol solved every time were swapped for the kinds it kept missing, such as accessibility and safeguards on the website, single wrong rows in a large set of books, and complete legal and policy fixes ([why](docs/health-check-problems.md#decisions)). Scores from different versions aren't directly comparable, so runs on versions before v0.9 are kept in [results/](results/) but not listed here.

| Model | Version | Score | Run time | Tokens burned | Speed (output tokens/s) | Notes |
|---|---|---|---|---|---|---|
| claude-opus-5-5, medium | v0.9 | **87** (run 2; 86 as first graded) | 14 min 46 s | 3.82M | 95 | Self-run, Claude Code. $3.94. [Scorecard](results/2026-10-01-claude-opus-5-5-medium-v0.9.1-02.md), [regrade of both runs](results/2026-10-01-claude-opus-5-5-medium-v0.9.1-regrade.md), [comparison](results/v0.9-comparison.md) |
| claude-opus-5-5, medium | v0.9 | **76** (run 1; 73 as first graded) | 7 min 21 s | 2.38M | 91 | Self-run, Claude Code. $2.29. [Scorecard](results/2026-10-01-claude-opus-5-5-medium-v0.9.1-01.md) |
| gpt-6.1-sol, medium | v0.9 | **72** (run 2; 69 as first graded) | 14 min 53 s | 1.73M | 28 | Self-run, Codex. $0.61 (estimated). [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.9-02.md), [regrade of both runs](results/2026-10-01-gpt-6.1-sol-medium-v0.9-regrade.md) |
| gpt-6.1-sol, medium | v0.9 | **71** (run 1; 67 as first graded) | 14 min 21 s | 1.25M | 30 | Self-run, Codex. $0.53 (estimated). Crashed the online menu (counted as broken). [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.9-01.md) |

Tokens burned counts everything the model read and wrote, most of it cached input it re-reads at each step. Speed is output tokens per second of run time, so time spent running commands counts against it.

## Limits

- **The problems were tuned on one model.** From v0.7 to v0.9, problems GPT-6.1 Sol solved every time were swapped for kinds it missed, and v0.10's bigger books were chosen knowing Sol finds single wrong rows less often than Opus. Nothing was tuned against Claude models this way, so read a gap between Sol and a Claude model as an upper bound.
- **A score is the model plus its tool.** Claude models run in Claude Code and GPT models in Codex, each under that tool's own rules for running commands.
- **A few runs aren't a ranking.** One model's scores have differed by 11 points between two runs. Compare averages over at least three runs, and treat a few points as a tie.
- **The judges haven't been checked against a person.** They decide 10 of the 100 problems.
- **It's one made-up bakery, and the answers are public.** A model released after this repository may have seen them, and the integrity check detects peeking; it doesn't prevent it.
- **It was built with Claude.** The problems, the checks and the dollar figures were written with Claude models' help, which could favor the way Claude models phrase things.

## Check the benchmark

Python 3.10+ standard library; website checks also need Playwright for Python and Chromium. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tasks/health-check/grading/isolation_check.py
```

## License

[MIT](LICENSE). Everything here is public so anyone can check how problems are planted and graded. The answer files carry a canary line asking that they stay out of AI training data; [running the bench](docs/running-the-bench.md#open-source-and-contamination) covers what that means for results.
