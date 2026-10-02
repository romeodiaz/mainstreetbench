<h1 align="center"><img src="docs/images/logo.png" alt="Main Street Bench" width="420"></h1>

> **AI assistants:** if someone asked you to run Main Street Bench on a model, follow [RUN-WITH-AI.md](RUN-WITH-AI.md) step by step. You are only the referee: this repository holds the answers, so never work on the bakery task yourself.

How well can an AI look after a small business? Main Street Bench hands an AI everything for a neighborhood bakery, with 100 hidden problems, and scores what it fixes and what it breaks.

## Test any AI in one sentence

Open the coding mode of your AI app in an empty folder. In Claude desktop that's the **Code** tab; in ChatGPT desktop it's **Codex**. Then paste:

> Clone https://github.com/romeodiaz/mainstreetbench and run Main Street Bench on **gpt-6.1-sol** at **medium** effort. Give me the score.

Swap in the model and effort level you want to test (for example **claude-opus-5-5** at **high**). Approve the assistant's requests to run commands, and come back in about an hour.

You get a scorecard with:
- the score out of 100;
- what it fixed and what it broke;
- dollars at risk caught;
- time and cost.

Your assistant only referees: it starts the model you named in its own folder, then grades the result. The scorecard also checks that the model didn't peek at the answers. Results stay on your computer, and are labelled **self-run**. This repository isn't taking outside submissions yet.

### What you need

- **The tested model's app, signed in on this computer.** That's Claude Code for Claude models, or the Codex CLI for GPT models. Your assistant can install it; you sign in once.
- **A paid plan with room for one long job.** A run uses up to 45 minutes of the model's work, plus a little for a second model from the same plan that judges 8 of the problems.
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

The other 10, such as whether a customer got a sensible reply, are decided by a judge model against a short yes/no checklist. Where a reply needs a specific fact, such as the right refund amount, code checks that first. The scorecard names the judge and shows how many points it decided.

The design follows [Bug Hunt Bench](https://github.com/phuryn/bug-hunt-bench): many independent planted problems, no list of what to find, and a judge only where a check can't be exact.

**The grading is verified:**
- an untouched bakery scores **0**;
- a complete fix scores **100**;
- each of the 31 website problems is shown, one at a time, to fail only its own check.

The problems split 4 obvious, 37 needing cross-checking, and 59 hidden, so expect scores well below 100. More detail: [the grader](tasks/health-check/) and [running it by hand](docs/running-the-bench.md).

## Results so far

The current version is **v0.9**. It's calibrated so a cheap model has room to fall short: problems that GPT-6.1 Sol solved every time were swapped for the kinds it kept missing, such as accessibility and safeguards on the website, single wrong rows in a large set of books, and complete legal and policy fixes ([why](docs/health-check-problems.md#decisions)). Scores from different versions aren't directly comparable.

| Model | Version | Score | Notes |
|---|---|---|---|
| claude-opus-5-5, medium | v0.9 | **87** (run 2) | Self-run, Claude Code. $3.94, 15 min. [Scorecard](results/2026-10-01-claude-opus-5-5-medium-v0.9.1-02.md), [comparison](results/v0.9-comparison.md) |
| claude-opus-5-5, medium | v0.9 | **76** (run 1; 73 as first graded) | Self-run, Claude Code. $2.29, 7 min. [Scorecard](results/2026-10-01-claude-opus-5-5-medium-v0.9.1-01.md) |
| gpt-6.1-sol, medium | v0.9 | **72** (run 2; 69 as first graded) | Self-run. [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.9-02.md), [regrade of both runs](results/2026-10-01-gpt-6.1-sol-medium-v0.9-regrade.md) |
| gpt-6.1-sol, medium | v0.9 | **71** (run 1; 67 as first graded) | Self-run. Crashed the online menu (counted as broken). [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.9-01.md) |
| gpt-6.1-sol, medium | v0.8 | **86** (77 as first graded) | Self-run. The first grade had grader flaws, which are fixed in v0.8.1. [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.8-01.md), [regrade](results/2026-10-01-gpt-6.1-sol-medium-v0.8-01-regrade.md) |
| gpt-6.1-sol, medium | v0.7 | **91** (87 as first graded) | Self-run. The first grade had grader flaws, which are fixed in v0.7.1. [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.7-01.md), [regrade](results/2026-10-01-gpt-6.1-sol-medium-v0.7-01-regrade.md) |
| gpt-6.1-sol, medium | v0.6 | **90** (72 as first graded) | Self-run. The first grade had grader flaws, which are fixed in v0.6.1. [Scorecard](results/2026-10-01-gpt-6.1-sol-medium-v0.6-01.md), [regrade](results/2026-10-01-gpt-6.1-sol-medium-v0.6-01-regrade.md) |

## Earlier rounds

Each earlier task told the AI what to do, and Sol solo did nearly all of it:

| Round | Task | Result |
|---|---|---|
| v0.2 | [Reconcile September's books](tasks/retail-reconciliation/) | Sol passed every business check and planted case ([run](results/sol-medium-v0.2-01.md)) |
| v0.3 | [Three ordering-site tickets with interface notes](tasks/ordering-site/) | Sol 100 ([run](results/sol-medium-v0.3-01.md)) |
| v0.4 | Five tickets, owner's words only | 0 from an inherited starter bug; about 100 once fixed ([run](results/sol-medium-v0.4-01.md)) |
| v0.5 | Eight tickets | 1.3 raw from a grader flaw; **97.2** regraded, missing only one security mistake ([run](results/sol-medium-v0.5-01.md), [regrade](results/sol-medium-v0.5-01-regrade.md)) |

What they taught: Sol does what it's told, and its one real miss was something nobody asked about. The health check is built around that gap.

## Check the benchmark

Python 3.10+ standard library; website checks also need Playwright for Python and Chromium. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tasks/health-check/grading/isolation_check.py
```
