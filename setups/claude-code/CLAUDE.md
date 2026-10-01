## Workflow: Opus plans, Codex implements

Requires the official Codex plugin: `/plugin marketplace add openai/codex-plugin-cc`, `/plugin install codex@openai-codex`, `/codex:setup`.

- For any non-trivial change, first write a plan with numbered tasks and acceptance criteria.
- Delegate implementation of each task to the codex:codex-rescue subagent, in the background when tasks are independent.
- Include in each brief: files involved, constraints, and the test command that proves it's done.
- After Codex finishes, review the diff and run the tests yourself. Send fixes back to Codex rather than rewriting them yourself unless they're trivial.
- Do small edits (a few lines) directly.
