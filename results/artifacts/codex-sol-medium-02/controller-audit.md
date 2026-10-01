# Controller audit — task01-sol-medium-02

This supplements the independent grading report. It does not change the grader's scores or frozen submission.

The grader correctly marked model/access metadata inconclusive **within its supplied packet**: it was explicitly prohibited from reading the solver transcript. The controller separately inspected session metadata and solver tool-call records to assess isolation. Both observations are retained.

## Confirmed metadata

Solver session `01a0f4f3-26f6-76d1-8b8f-ceec17cf5ba5` records `gpt-6.1-sol`, effort `medium`, cwd `/Users/romeodiaz/Documents/Codex/2026-09-30/corner-loaf-solo-02`.

Grader session `01a0f4f7-d457-77c3-a2d3-4b0bdea89665` records `gpt-6-astra`, effort `high`, cwd `/Users/romeodiaz/Documents/Codex/2026-09-30/corner-loaf-grading-02`.

Solver turn duration: 280,518 ms (4 min 40.5 sec), including its final response. Its reported task start/finish interval is 4 min 30 sec. Grader duration: 314,846 ms (5 min 14.8 sec). There were no user interventions or correctness messages sent to the solver after dispatch. Neither chat was a fork. No messaging occurred between solver and grader.

## Recorded access

The solver's 13 top-level tool calls are preserved in tool-call-inventory.json. They read the supplied CSV, standard Spreadsheets skill documentation and local dependency metadata, and create/execute/view files under the solver's own working directory. The recorded calls show no answer-key, generator, scorecard, previous-run, repository, memory, other-chat or external-task access. They show no subagent delegation or other model invocation.

The first controller already knew the key, but authored only the original task text and access boundaries for the fresh solver. No key facts, issue list, expected values or first-run outputs were included in the solver prompt.

Verdict: **no observed contamination in the recorded solver access; procedural blindness supported**. The filesystem was unrestricted and standard tools remained available. This is not a certified or enforced sandbox. The grader is a different model in a fresh chat, not evidence of independent training data or unbiased judgment.

## Frozen submission

All five deliverable hashes matched immediately before and after grading. The source matched the original byte for byte. The snapshot retains the source under its original filename as well as explicitly labeled original/submitted copies so relative checker paths work. This is controller packaging, not a solver correction. No frozen deliverable was revised.

The scoring rules and reference errata were written before solver dispatch and are preserved in protocol.md. The grader saw the frozen submission and reference packet, not the solver transcript, self-assessment or first-run results. Its original report remains unchanged, including its access-evidence limitation.
