# Blind solver with independent grading — Task 1, run 2

Recorded September 30, 2026, America/Los_Angeles.

**Primary issue handling: 12/12. Independent grader's literal exact-key score: 10/12. Financial totals do not match the key.** All five deliverables were submitted and frozen before grading.

The solver was a new GPT-6.1 Sol/medium chat containing only the supplied CSV and exact task requirements, plus access boundaries. The grader was a separate GPT-6 Astra/high chat receiving the original prompt, reference/errata, preregistered protocol and frozen outputs. Neither was a fork. Model and effort were verified from session turn_context.

| Measurement | Result |
|---|---|
| Solver turn duration | 4 min 40.5 sec |
| Grader turn duration | 5 min 14.8 sec |
| User interventions / solver feedback | 0 |
| Retained transactions / refunds | 293 / 3 |
| Customers / inactive customers | 64 / 32 |
| Recorded net receipts | $14,223.00 |
| Corrected key receipts | $14,196.00 |
| Difference | +$27.00 |
| Dashboard earned-revenue headline | $12,039.00; gift-card proceeds separated |
| Submitted checker | Passed, inspected as safe and independently reconciled |
| Rendered values | 290 matched independent calculations |
| Frozen/source integrity | All hashes unchanged; original CSV preserved |

The primary score follows the README's fixed-or-correctly-flagged rule. The exact-key secondary zeros are item 06 (Coffee Beans 1 lb instead of Coffee Beans 1lb, a cosmetic canonical-label difference) and item 07 (four totals flagged but preserved). All product groups were correctly consolidated. Both future-date corrections passed. The independent grader's report is preserved without controller changes to its scores.

The dashboard worked offline at desktop and phone widths. At 390 px it was readable. At 320 px two tables required short horizontal scrolling. Customer identities were correctly separated, including Tessa Park and Lena Park.

## Blindness and independence evidence

The controller audit of all 13 recorded solver tool calls found no held-out source, previous-run, memory, external-task, other-model or other-chat access. The solver read the supplied CSV and standard skill/runtime documentation and created its own files. No correctness feedback was sent. The key was held in a separate evaluation folder.

This supports **procedural blindness**, not enforced filesystem isolation. Global/system/personal instructions, tools and required skills remained part of the Codex harness. This is one trial of a model in that harness, not an unaided model-only benchmark. A different-model grader reduces self-grading within the solver chat but does not certify unbiased or independent training.

The independent grader marked model/access evidence inconclusive because its authorized packet did not include either session transcript. The controller separately verified those facts and documented them in controller-audit.md. The original grader limitation remains visible rather than being edited away.

## Local evidence

- Solver chat: `01a0f4f3-26f6-76d1-8b8f-ceec17cf5ba5`.
- Grader chat: `01a0f4f7-d457-77c3-a2d3-4b0bdea89665`.
- Solver workspace: `/Users/romeodiaz/Documents/Codex/2026-09-30/corner-loaf-solo-02/`.
- Evaluator packet: `/Users/romeodiaz/Documents/MainStreetBench-Evaluation/task01-sol-medium-02/`.
- Grader files: `grading-report.md`, `grading.json`.
- Controller evidence: `controller-audit.md`, `access-audit.json`, `tool-call-inventory.json`, `run.json`, `frozen-manifest.json`.

The source, protocol, errata, reference and frozen artifacts are retained in that packet. See `docs/blind-evaluation.md` for the repeatable workflow. Do not give this report or evaluator packet to later solver chats.

The [shareable artifact package](../../results/artifacts/codex-sol-medium-02) contains the frozen source and five deliverables, historical reference/prompt, protocol, manifest, independent grading report/JSON and controller audit. Frozen file hashes match the original packet. It excludes the full solver transcript and unrelated account records. The reference copy is historical; the current public key corrects the known errata.
