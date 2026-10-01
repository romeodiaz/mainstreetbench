# Main Street Bench v0.1: Opus 5.5 Plans, GPT 6.1 Sol Builds

Video storyboard, Sep 30, 2026. Live version: https://claude.ai/code/artifact/fb809332-b5b8-473a-9957-b5a780a3924d

## Concept and positioning

The video's claim: **the setup matters as much as the model.** You give the same real business job to the same two models, Opus 5.5 as planner and GPT 6.1 Sol as builder, in three different apps, and score them honestly.

Why this builds authority with small business owners:

- **You show, not tell.** Most AI content is opinions. A timed, scored test with real output is evidence.
- **You translate for non-technical buyers.** Frame Opus as the architect and GPT 6.1 Sol as the build crew. Owners already understand hiring a planner and a crew.
- **You play it safe on their behalf.** Every setup in the battle stays within Anthropic's and OpenAI's terms. Say so on camera. It separates you from creators pushing proxies and hacks that can get an account banned.
- **You end with a recommendation by business type**, not a single "winner." That's what an advisor does.

One-sentence promise to the viewer: *In three minutes, you'll know which AI setup gets the most real work done for a small business, and which shortcuts to avoid.*

## Format and specs

Record once, cut two versions: a 3-minute horizontal main video and a 60-second vertical cutdown.

| Version | Aspect | Length | Where it goes |
| --- | --- | --- | --- |
| Main | 16:9, 1440p | 2:45–3:05 | LinkedIn native upload, YouTube |
| Cutdown | 9:16, 1080×1920 | 55–60 s | LinkedIn, Instagram Reels, TikTok, YouTube Shorts |

- Record the screen at 1440p so you can zoom in during editing and keep code and text readable on phones.
- Burn in captions on both versions. Most feed video is watched muted.
- Speed up agent footage 8–16× and label the speed on screen.

## Battle rules

**The job:** turn a small bakery's messy order spreadsheet into a clean customer list and a sales dashboard. Almost every owner has a spreadsheet like this, and the before-and-after is easy to see at a glance.

The test file, Corner Loaf Bakery's `customer_orders.csv`, has 300 rows with 12 planted problems, such as the same customer spelled four ways, mixed date formats, test orders, refunds, and a 2062 typo. Each harness gets the same file and the same prompt from `prompt.md`.

This is Task 1 of Main Street Bench v0.1, "The Messy Spreadsheet." Deliverables, shown on screen before recording:

1. A clean orders file with consistent dates, numbers, and product names.
2. A customer list with duplicates merged and phones in one format.
3. A cleaning log listing every fix and flag with order IDs.
4. A single-file dashboard: revenue by month, top 10 customers, best sellers, and customers with no order in 90 days. It must work on a phone.
5. A check script confirming the dashboard matches the clean data.

**Contenders:**

| Contender | How Opus hands work to GPT 6.1 Sol |
| --- | --- |
| Orca | Built-in orchestration: Opus starts Codex workers |
| Conductor | Opus chat uses the official Codex plugin |
| Claude Desktop (Code tab) | Opus uses the official Codex plugin, told to delegate in `CLAUDE.md` |

**Fairness rules:**

- Same prompt, pasted from one text file. Same starting commit and the same CSV. Keep the answer key off screen and out of every agent's folder.
- Opus 5.5 and GPT 6.1 Sol at the same effort settings in every app. Show the model picker on screen.
- Timer starts when the prompt is sent and stops when the check script passes and all five deliverables exist.
- Only step in when an app is stuck, and count every intervention.

**Scorecard:**

| Category | What you measure | Why an owner cares |
| --- | --- | --- |
| Setup time | Minutes from install to first run | Time before they see value |
| Time to done | Wall-clock minutes until the check script passes | How fast work gets done |
| Hands-on time | Number of times you stepped in | How much babysitting it needs |
| Quality | Planted problems fixed or flagged, out of 12, plus whether the dashboard totals match the answer key | Whether they can trust the output |
| Usage cost | Claude and ChatGPT usage meters, before vs. after | What it costs on their plans |
| Terms-safe | Yes or no | Whether it can get their account banned |

Pick a winner per category, not one overall score. Then give a verdict by business type in the video.

## Main video storyboard

Eleven shots, about 3 minutes. Anything in [brackets] gets filled in from your real results after recording; don't script outcomes in advance.

| # | Time | OBS scene | On screen | Script | On-screen text |
| --- | --- | --- | --- | --- | --- |
| 1 | 0:00–0:05 | Talking head | You, close framing, direct to camera | "I gave the same job to the two best AI models, in three different setups. The setup mattered more than I expected." | SAME MODELS. 3 SETUPS. 1 JOB. |
| 2 | 0:05–0:15 | Split | Simple graphic: architect (Opus 5.5) hands plans to a build crew (GPT 6.1 Sol) | "Opus 5.5 is the architect. It plans. GPT 6.1 Sol is the crew. It builds. The question is which app runs that team best." | PLANNER + BUILDER |
| 3 | 0:15–0:30 | Screen + cam corner | Slow scroll through the messy bakery spreadsheet, then the five deliverables | "The job: a bakery's order spreadsheet. Same customer spelled four ways, test orders mixed in, a sale dated 2062. Sound familiar? Turn it into a clean customer list and a dashboard." | THE JOB |
| 4 | 0:30–0:40 | Results board | Empty scorecard, three contender name cards | "Same prompt, same models, same settings. Timer starts when I hit send." | MAIN STREET BENCH v0.1 |
| 5 | 0:40–1:10 | Screen + cam corner | Orca, sped up. Freeze on the moment Opus hands tasks to Codex workers. Stopwatch overlay | "Round one, Orca. Watch Opus write the plan, then split it into [number] tasks for the crew." React to one real moment. | ROUND 1: ORCA · 16× |
| 6 | 1:10–1:40 | Screen + cam corner | Conductor, sped up. Show the Codex plugin being called from the Opus chat | "Round two, Conductor. Same team, but here Opus calls GPT through the official Codex plugin." React to one real moment. | ROUND 2: CONDUCTOR · 16× |
| 7 | 1:40–2:05 | Screen + cam corner | Claude Desktop Code tab, sped up. Briefly show the `CLAUDE.md` delegation rule | "Round three, Anthropic's own app, with one instruction telling Opus to delegate." React to one real moment. | ROUND 3: CLAUDE DESKTOP · 16× |
| 8 | 2:05–2:25 | Screen + cam corner | The three dashboards side by side, then the scorecard fills row by row | "Here's what each one actually built. [Fastest] finished in [time]. [Best quality] caught [X] of 12 planted problems." | Scorecard animates in |
| 9 | 2:25–2:45 | Talking head | You, direct to camera | "If you want to watch every step, I'd pick [A]. If you want to hand it off and check back later, [B]." | WHICH ONE FOR YOU |
| 10 | 2:45–2:55 | Talking head | You, slightly closer framing | "And if someone sells you unlimited AI through a proxy or a hack, skip it. You can lose the account your business runs on." | SKIP THE SHORTCUTS |
| 11 | 2:55–3:05 | Split | You + your name, title, and CTA card | "This is what I help businesses figure out. Comment SCORECARD and I'll send you the full results." | COMMENT "SCORECARD" |

If one app fails or needs help, keep that moment in. Real friction is more credible than a clean sweep.

## Vertical cutdown (60 seconds)

Same footage, restacked: your camera in the top third, a cropped and zoomed screen in the bottom two thirds.

| # | Time | Visual | Script |
| --- | --- | --- | --- |
| 1 | 0:00–0:03 | Your face, full frame | "Same AI job. Three setups. Here's which one I'd put in your business." |
| 2 | 0:03–0:10 | Architect-and-crew graphic | "Opus 5.5 plans. GPT 6.1 Sol builds. Which app runs them best?" |
| 3 | 0:10–0:20 | Orca highlight, 16× | One line on the moment that stood out |
| 4 | 0:20–0:30 | Conductor highlight, 16× | One line on the moment that stood out |
| 5 | 0:30–0:40 | Claude Desktop highlight, 16× | One line on the moment that stood out |
| 6 | 0:40–0:52 | Scorecard, full screen | "[Winner] for speed. [Winner] for quality. [Pick] if you want it hands-off." |
| 7 | 0:52–1:00 | Your face + CTA card | "Full scorecard? Comment SCORECARD." |

Open on a moving frame, not a title card. The first second decides whether people keep watching.

## OBS scene setup

Four scenes cover every shot. Put each on a hotkey so you can switch without looking.

| Scene | Layout | Used in shots |
| --- | --- | --- |
| Talking head | Camera full frame | 1, 9, 10 |
| Split | Graphic or card left two thirds, camera right third | 2, 11 |
| Screen + cam corner | Screen full frame, circular camera bottom right, stopwatch top right | 3, 5–8 |
| Results board | Scorecard full frame (a browser source or slide), small camera corner | 4, 8 |

- **Recording:** record at 1440p, and put the mic on its own audio track so you can fix levels in editing.
- **Vertical version:** a vertical-canvas plugin (such as Aitum Vertical) can record the 9:16 layout at the same time, which saves re-framing later.
- **Stopwatch:** use a browser-source timer you can start with a hotkey the moment you send each prompt.
- **Long runs:** record each round as a separate file. It makes speeding up and trimming much easier.

## Pre-record checklist

**Privacy**

- [ ] Turn on Do Not Disturb and close email, Slack, and messaging apps.
- [ ] Use a demo repo with no real client data.
- [ ] Keep `.env` files, API keys, and tokens off screen. Blur account emails in editing.

**Fairness**

- [ ] Prompt saved in one text file, pasted identically into each app.
- [ ] Same starting commit and CSV in every run, with the answer key stored outside the project folder.
- [ ] Model and effort settings shown on screen in each app.
- [ ] Usage meters screenshotted before and after each round.
- [ ] If time allows, run each contender twice and report both.

**Accuracy and credibility**

- [ ] Say "in this test" rather than implying the results always hold.
- [ ] Put the recording date and app versions in the caption. These apps and their billing rules change often.
- [ ] Label every speed-up.
- [ ] Disclose any sponsorship or affiliate links.

## Captions and CTA

The call to action is a lead magnet: people comment SCORECARD, and you send the full results as a one-page PDF. That starts a conversation with exactly the owners you want.

**LinkedIn post (main video)**

> I gave the same job to two AI models and ran it through three different apps.
>
> The test: Main Street Bench v0.1. Turn a bakery's messy order spreadsheet into a clean customer list and a sales dashboard. I planted 12 problems in it. Opus 5.5 planned the cleanup. GPT 6.1 Sol built it.
>
> What I learned:
> • [Takeaway 1: the setup that was fastest, and why]
> • [Takeaway 2: the one that needed the least babysitting]
> • [Takeaway 3: which one I'd set up for a business owner who isn't technical]
>
> One more thing: all three setups stay within the AI companies' terms. If someone offers you "unlimited AI" through a workaround, ask what happens when the account gets shut off.
>
> Comment SCORECARD and I'll send you the full results.
>
> Recorded [date]. App versions in the comments.

**Short-form caption (cutdown)**

> Same AI job, 3 setups. Which one would you trust in your business? Comment SCORECARD for the full results.

**First comment (post it yourself right after publishing)**

> Setup details: Orca [version], Conductor [version], Claude Desktop [version]. Opus 5.5 at [effort], GPT 6.1 Sol at [effort]. Speed-ups labeled in the video.
