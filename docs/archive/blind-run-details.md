# Blind solver and independent grading

Task 1 can be evaluated without exposing its key to the solver. Moving the key alone is insufficient: use a new chat with no inherited history and a separate input workspace.

Future trials use the approved **v0.2** task text from `tasks/01-messy-spreadsheet/prompt.md`, verbatim. Record its version and SHA-256 hash in the run packet. The second local trial below used the archived v0.1 prompt; preserve its original packet. For v0.2, grade against what that prompt actually requests: do not require v0.1-only filenames, a particular phone display format, or a specific check-script implementation. Keep grading instructions outside the solver prompt.

## Run sequence

1. Prepare an input folder containing only the original customer_orders.csv. Keep the answer key, generator, scorecard, rubric and previous outputs in a separate evaluator folder. The solver must not receive this repository.
2. Before execution, record the model, reasoning effort, time limit, allowed tools/skills, scoring definitions and key errata. The current trial uses a 30-minute limit. Preserve the task wording verbatim.
3. Start a new solver chat, not a fork, with GPT-6.1 Sol at medium effort. Supply only the CSV and exact task prompt, plus a boundary instruction forbidding other task sources, memory/history lookup, other agents/models and communications with the grader. No solution hints or issue list.
4. Keep the controller out of implementation. Record time and every user intervention. Do not send correctness feedback. Let the solver stop at completion or the preregistered time limit.
5. Freeze all five deliverables plus the source, with hashes and timestamps. Preserve the parent input filename for any checker that needs it. Never replace this snapshot with a corrected submission.
6. Start a separate GPT-6 Astra chat at high effort to grade the frozen files. Provide the original prompt, answer key, errata and scoring rules. Do not provide the solver's reasoning, self-assessment or previous results. Do not allow the grader to repair the submission.
7. Inspect scripts before executing them. Independently reconcile financial/customer/product/monthly figures and inspect the rendered offline dashboard. Verify frozen hashes remain unchanged.
8. Audit the solver tool-call transcript for held-out sources, external task copies and other model/chat access. Confirm model and effort from session metadata. Label contaminated or inconclusive runs honestly.

## Score definitions

The primary 12-item score follows the README: each problem is fixed or correctly flagged on all affected rows. The secondary score follows exact answer-key handling. Financial accuracy and artifact/UI acceptance are reported separately. No generic flag earns a point. Do not silently choose whichever rubric yields a better score.

Known key errata: 10058 and 10215 have no recoverable email in the source; flags are valid. Excluding both future-dated rows from the corrected total yields $14,075, not $14,175. Fix the grading reference, not the solver input.

## Isolation limit

An unrestricted local filesystem permits access outside the solver directory. Separate folders, input boundaries and transcript audits provide procedural blindness, not enforced isolation. For enforced isolation, use an environment containing only the input with no host mount, external connectors or task-source network access. Changing the environment changes the harness and must be recorded.

Available system/personal instructions and required skills are part of the Codex harness. This is a blind task evaluation using a selected model in a specified harness, not an unaided model-only benchmark. A different-model grader reduces self-grading bias but does not establish independent training data or remove all judging bias.

## Second local trial

- Solver chat: `01a0f4f3-26f6-76d1-8b8f-ceec17cf5ba5`.
- Grader chat: `01a0f4f7-d457-77c3-a2d3-4b0bdea89665`.
- CSV-only input: `/Users/romeodiaz/Code/mainstreetbench-blind/task01-sol-medium-02/`.
- Solver workspace: `/Users/romeodiaz/Documents/Codex/2026-09-30/corner-loaf-solo-02/`.
- Evaluator packet: `/Users/romeodiaz/Documents/MainStreetBench-Evaluation/task01-sol-medium-02/`.

The evaluator packet holds the preregistered protocol, reference copy, freeze tool, frozen snapshot/manifest, access audit, run metadata and separate grading reports. Keep it outside future solver workspaces.
