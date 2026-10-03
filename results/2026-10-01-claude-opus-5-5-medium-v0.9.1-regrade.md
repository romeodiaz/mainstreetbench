# Regrade: claude-opus-5-5 medium on v0.9 (two runs)

| | Run 1 | Run 2 |
|---|---:|---:|
| First graded (v0.9.1) | 73 | 86 |
| **Regraded (v0.9.2)** | **76** | **87** |
| Fixed | 76 | 87 |
| Broken | 0 | 0 |

The bakery folder is unchanged, and so is the model's work. Both runs score the same under the later v0.9.3 grader, which is what their scorecards now show; it changed only the dollars at risk (now out of $100,000). Three grading flaws were corrected:

| Flaw | Effect | Fix |
|---|---|---|
| P01 failed any mention of "nut-free" on the scone | Run 1 wrote "contains almond flour; NOT nut-free", which is the warning the problem asks for | "NOT nut-free" counts as a warning. |
| P17 failed the Thanksgiving promotion whenever it still mentioned the closed Thursday | Run 1 left the pickup date "to confirm"; run 2 moved it to Wednesday, November 25. Both noted that the shop is closed that Thursday, and both failed | Only a pickup actually set for the closed Thursday fails; "to confirm" counts. |
| M26 accepted only some wordings of the tax undercharge | Run 1 reported that earlier October orders "were charged 8% instead of 8.25%" | That wording counts; the earlier ones still do. |

Run 1 gained all three (P01, P17, M26). Run 2 gained P17 only.

The scorecards' Integrity line also changed. The first scorecards said "personal instructions loaded: ~/.codex/AGENTS.md". That file belongs to Codex; Claude Code doesn't read it, and it appears nowhere in either run's log. From v0.9.2 the runner lists only the personal instruction files the tested tool reads.

## Misses

- **Both runs (12):** L02, L04, L12, M15, M28, M33, M37, P14, W39, W46, W48, W49.
- **Run 1 only (12):** C12, L10, L11, W32, W37, W38, W40, W42–W45, W47.
- **Run 2 only (1):** L16.

Run 1 stopped after 7 minutes and left most of the website accessibility work undone. Run 2 worked for 15 minutes and fixed most of it. That is nearly all of the 11-point gap between the two runs.
