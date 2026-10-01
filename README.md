# Main Street Bench

Can an expensive model planning and reviewing a cheaper model's work deliver similar quality at a lower cost, on the jobs a small business owner actually has?

## The current task: the shop health check (v0.6)

An AI gets everything for Corner Loaf Bakery and this message from the owner, word for word:

> Hi! I own Corner Loaf Bakery, a small neighborhood bakery. Today is Thursday, October 8, 2026.
>
> Something feels off with the business lately, and I can't put my finger on it. I've attached a folder with everything for the business: our ordering website, September's books, the menu and allergen sheet, our policies, our online listing and the shop's emails. There's a note in there called FOLDER-GUIDE that says what's where.
>
> Could you go through all of it? Please fix whatever you can, but don't break anything that's working. Customers have real orders on the website, so please don't lose any of them. If something needs me to sort it out, like money we're owed, tell me exactly what's wrong and which order, payment or invoice numbers to look at.
>
> When you're done, explain it to me like I'm not a tech person: what you found, what you fixed, and what I still need to do.

<details>
<summary>FOLDER-GUIDE, the note in the bakery's folder</summary>

- `website/`: our online ordering site. Sam built it; his notes are in `website/README.md`. `website/data/bakery.db` has real customer orders; please don't lose any.
- `books/`: September's register exports, card payments, payouts, bank statement, cash drawer counts, supplier bills, refunds, disputes and the reports our spreadsheet makes.
- `menu/`: the menu, price lists, allergen sheet, recipes and the coffee supplier's spec.
- `policies/`: refund, gift card, cancellation and coupon pages, and the receipt template.
- `signs/`: the sign on the front door.
- `listing/`: our online business listing and recent reviews.
- `admin/`: staff list, promotions calendar, accounts and services, newsletter list.
- `inbox/`: emails from the last few weeks. `drafts/` has replies we haven't sent.

</details>

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

To test a particular reasoning setting, say so: "run Main Street Bench on gpt-6.1-sol at medium effort".

Your assistant sets things up, starts **XYZ** in its own folder with the bakery owner's message, waits for it to finish (up to 45 minutes) and grades the work. You get a scorecard:
- problems fixed out of 100;
- dollars at risk caught;
- anything it broke;
- time and cost.

Your assistant only referees. It doesn't help or take the test itself, because it can see the answers. Results you run yourself are labelled **self-run**.

## What you need

**An assistant that can run commands on your computer.** A regular chat window can't run the test; it needs the assistant's coding mode.

| App | What to use |
|---|---|
| Claude desktop | The **Code** tab. Choose an empty folder to work in, then paste the sentence. |
| ChatGPT desktop | **Codex**, OpenAI's coding agent, working on your computer rather than in the cloud. Open an empty folder, then paste the sentence. |

**The tool for the model you're testing, installed and signed in on the same computer.** The test starts the model through its command-line tool:
- **Claude models** (Opus, Sonnet and others): Claude Code.
- **OpenAI models** (GPT and others): Codex CLI.

Your assistant can install either one. You'll need to sign in once, with the account whose plan you want the test to use.

**A paid plan with room for one long job.** A run can take up to 45 minutes of the tested model's work, and it counts against that plan's usage limits. If you ask for a judge model, that uses a little more.

**The basics, which your assistant checks and can install:**
- Python 3.10 or newer;
- git;
- about 1 GB of free disk space for the grading browser and the run folders;
- an internet connection while setting up.

**About an hour with the computer awake.** Your assistant will ask permission to run commands, so approve them. Leave it alone while the tested model works; it reports back when grading is done.

The test is checked on Linux and should work on a Mac. On Windows, if it fails, ask your assistant to run it in WSL.

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
