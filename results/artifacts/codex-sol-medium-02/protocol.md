# Preregistered blind solver / independent grader protocol

Run ID: task01-sol-medium-02. Prepared September 30, 2026, before solver execution.

## Solver conditions

- A new chat, not a fork, using GPT-6.1 Sol at medium reasoning. One agent handles planning and building. No subagents, other models, prior outputs or grader feedback.
- Business input is only the exact original CSV. Task wording is copied verbatim from reference/task-prompt.md. An isolation preamble governs input access without adding task hints.
- No benchmark repository, answer key, scorecard, generator or earlier chat history is supplied to the solver. Avoid identifiers revealing the benchmark or planted issue count in its prompt.
- Standard Codex tools and required skill instructions remain available. Record actual tools, skills and active personal/system instructions as harness conditions. This evaluates a model in the Codex harness, not unaided model capability.
- Copy the supplied CSV into a fresh chat's working folder before beginning. Inspect only that input and files created there. Do not access parent/sibling projects, memory, history, other chats, or online versions of this task. Offline task execution.
- Zero user corrections or implementation help during execution. Log any intervention instead of silently omitting it. Stop at the model's declared completion and passing check, or a predeclared 30-minute limit, preserving partial results if exceeded. No extra attempts or hint-driven retries after submission.
- A fresh input folder has been prepared containing only customer_orders.csv. The source has not been changed.

## Freeze and independence

The controller may observe status, timing and access, but sends no correctness feedback. When the solver finishes, snapshot its output directory and input into this evaluator folder using freeze.py. Record source and deliverable SHA-256 hashes, timestamps and the solver chat ID. Run grading only on that snapshot. Do not allow post-submission fixes to affect the score.

The grader uses a fresh, different-model chat, is given only the task, corrected reference notes, key and frozen outputs, and is told not to repair them. It does not see run 1, the solver's reasoning, self-assessment or this controller's predictions. It should report evidence for every score. Different models do not ensure independent training or eliminate bias; separation prevents feedback and self-grading within the solver chat.

Do not automatically execute a solver-provided check script in the grader's unrestricted environment. Inspect it first; run only if it is a local, non-destructive check. If not, assess it statically and use independent calculations. HTML is verified offline with network requests blocked.

## Scoring fixed before execution

Primary score is issue handling, 0/1 per planted problem, 12 total. A problem passes when all affected source rows are fixed or explicitly, correctly flagged, consistent with the README and task no-invention rule. Issue 05a and 05b form one combined item. A flag must identify the problem and affected IDs, not be a generic disclaimer. Do not demand unsupported invented values.

Secondary score is exact answer-key handling, 0/1 per item. For item 07, the key demands recalculated totals plus flags. For item 10, the key demands corrected 2026 dates or excluded rows plus flags. Mark departures separately even when the primary score passes. Financial accuracy is a separate comparison to the key, not inferred from the solver's own checker. Record full-data and future-row-excluded variants distinctly.

Additional acceptance criteria: all five requested artifacts, one row per real retained transaction, customer identity separation, numeric/date/contact formatting, reconciled monthly/product/customer totals, correct inactive population, offline behavior and phone readability. Do not invent weights or roll these into the 12-item score.

## Reference errata

- 10058 (Gideon Petrov) and 10215 (Mei Weber) each occur once in the source, with no email. They cannot be recovered from the input. Correct missing-email flags pass. The key mistakenly lists them as recoverable.
- Full corrected net revenue is $14,196.00. The two future-dated rows total $121.00. Excluding both produces $14,075.00; the key's $14,175.00 alternative is a typo.
- Future dates may be flagged without guessing under the primary scoring rule. For exact key handling, they must be corrected or excluded. Flagged retained rows should not be described as silently accepted dates.
- Keep refund transactions and gift-card receipts in the reference's receipts metric. Report any different accounting definition rather than silently substituting it.

## Access audit and claims

Inspect the solver's tool-call transcript for reads of held-out files, benchmark searches, external task copies, other agents/chats and reference leakage. Record exact model/effort from turn_context. Audit outcome can be clean, contaminated, or inconclusive. Do not claim a blind result if access cannot be established or prohibited sources were read. A local unrestricted filesystem and globally available tools are procedural isolation, not an enforced sandbox. For stronger isolation, use an environment containing only the input, with no host mount, external connectors or network.

Report timing, user interventions, incomplete artifacts, checker failures, actual access conditions, one-trial limitation and separate scores. This controller already knows the answer key and must not solve or grade the new run in the solver chat.
