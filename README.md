# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost, on the jobs a small business owner actually has?

## The current task: the shop health check (v0.6)

An AI gets everything for Corner Loaf Bakery and this message from the owner, word for word:

> I run Corner Loaf Bakery, a small bakery in the US. Today is Thursday, October 8, 2026.
>
> Something feels off with the business and I can't put my finger on it. This folder has everything: our ordering website, September's books, the menu and allergen sheet, our policies, our online listing and the shop inbox. FOLDER-GUIDE.md says what's where.
>
> Please go through all of it. Fix whatever you can fix, and keep everything that already works working; customers have real orders in website/data/bakery.db, so don't lose any. For anything you can't fix from here, like money that needs chasing, tell me exactly what's wrong and which order, payment or invoice numbers to look at.
>
> When you're done, give me a plain-English report: what you found, what you fixed, and what I need to do.

**100 problems** are planted across those files, and nothing lists them. They range from "the baguette is marked gluten-free" to "anyone can cancel anyone's order by typing an order number" to "a payout never reached the bank". [See all 100 in plain English.](docs/health-check-problems.md)

The score is **problems fixed out of 100**, alongside:
- **"Said it fixed it, but didn't"**
- **"Broke something that worked"**
- **Dollars at risk caught**
- **Cost**

The design follows [Bug Hunt Bench](https://github.com/phuryn/bug-hunt-bench): many independent planted problems, no list of what to find, and a blind judge model only where a check can't be exact.

**Status: built and verified, no model runs yet.** The grading controls hold:
- the untouched workspace scores **0**;
- a complete reference fix scores **100**;
- each of the 39 website problems is shown, one at a time, to fail only its own check.

The problems split 17 obvious, 49 needing cross-checking, and 34 hidden. That mix is meant to leave headroom, so expect scores well below 100. [How to run and grade it](tasks/health-check/), and [how to keep runs apart from this repository](docs/running-the-bench.md).

## Test a new AI yourself

Paste this into an AI assistant that can run commands on your computer, such as Claude Code or Codex:

> Clone https://github.com/romeodiaz/mainstreetbench, follow RUN-WITH-AI.md, and run Main Street Bench on the model **XYZ**. Give me the score.

Your assistant sets things up, starts **XYZ** in its own folder with the bakery owner's message, waits for it to finish (up to 45 minutes) and grades the work. You get a scorecard:
- problems fixed out of 100;
- dollars at risk caught;
- anything it broke;
- time and cost.

Your assistant only referees. It doesn't help or take the test itself, because it can see the answers. Results you run yourself are labelled **self-run**.

## Three configurations

| Configuration | Work | Reasoning |
|---|---|---|
| GPT-6.1 Sol solo | Sol does the whole job | Medium |
| Claude Opus 5.5 solo | Opus does the whole job | Medium |
| Opus + Sol | Opus plans and reviews; Sol implements | Medium for both |

Record the actual model identifiers and settings. Compare quality, time and the total cost of every task agent. The results can show that Sol already handles the job well, or that delegation adds more cost than value.

A health check suits the split: deciding what's wrong is the judgment part, and fixing many separate problems is the execution part. Single runs vary, so run each configuration more than once and treat differences of a couple of problems as a tie.

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
