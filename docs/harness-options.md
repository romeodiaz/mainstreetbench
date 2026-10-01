# Harness options: Opus 5.5 plans, GPT 6.1 Sol builds

Research notes as of Sep 30, 2026. These apps and Anthropic's rules for third-party tools change often; check the [Agent SDK plan article](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan) before relying on any billing claim. Not legal advice.

In every option, GPT 6.1 Sol runs through Codex (or Pi or Hermes) on a ChatGPT login; set it as the default in `~/.codex/config.toml`. "Subscription" means Opus 5.5 counts against your Claude plan limits.

## Opus uses your Claude subscription (interactive)

| Option | Pros | Cons |
|---|---|---|
| **Orca** | Opus orchestrates Codex workers natively; handoff between agents; editor, diff review, browser; free, open source, Mac/Win/Linux | Workers only see Opus's briefs; multi-account switching can raise usage-policy issues |
| **Conductor (local)** | Most polished Mac app; parallel worktrees; Codex plugin works inside an Opus chat | Mac only; switching models starts a new chat; no built-in orchestration |
| **Claude Desktop Code tab / VS Code / JetBrains + Codex plugin** | Official apps with no terminal; official OpenAI plugin; can delegate automatically through `CLAUDE.md` | Single-session focus; less of a multi-agent overview |
| **Claude Code (terminal) + Codex plugin** | Most direct setup; `codex-rescue` subagent; background jobs | Terminal interface; Claude sometimes does tasks itself |
| **bb** | Most flexible: scriptable threads, bots, handoff, remote machines | More setup; young software; community plugins; Claude/Cursor auth can fail if the daemon can't see credentials |
| **MCP bridges** (agents-mcp, subagent-mcp) | Any MCP client can start Codex workers; orchestrator context stays small | Community tools; more configuration |
| **Zed (via ACP)** | Agent panel built into the editor, running on Claude Code | Codex connected separately; little orchestration tooling |

## Opus uses your Claude subscription, but runs automatically (programmatic usage)

| Option | Pros | Cons |
|---|---|---|
| **Paperclip** | Built-in Claude Code and Codex adapters; org chart with an Opus lead and Codex workers; budget limits; self-hosted | Runs on heartbeats, the category Anthropic has tried to bill separately; heavy on limits; no code review |
| **Conductor Cloud** | Agents create workspaces and start or monitor chats through the Conductor CLI | Early access; unconfirmed whether you can choose each chat's agent |
| **OpenClaw (Claude CLI option)** | Always-on agent; works over chat apps | Runs `claude -p`, same billing risk as Paperclip; its own docs recommend API keys for always-on use |

## Mixed: GPT side on your ChatGPT plan, Opus paid

| Option | Pros | Cons |
|---|---|---|
| **Amp** | Mode Dial sets main agent, Oracle, and subagent models separately; custom agents and modes via plugins; Puck manages threads; Orbs run agents in the cloud | Opus needs Amp credits or an Anthropic API key; delegation needs a custom orchestrator mode to be reliable; subscription routing is experimental |

## Opus costs extra (API key, extra usage, or vendor credits)

| Option | Pros | Cons |
|---|---|---|
| **Factory Droid (Missions)** | Separate orchestrator, worker, and validator models; Spec Mode model setting; custom droids | Factory credits; needs an automated way to validate work |
| **Devin Fusion** | Lead + sidekick pairings tuned by Cognition | Sidekick slot doesn't offer GPT 6.1 Sol; Devin quota billing |
| **Pi** | Minimal and extensible; ChatGPT login works well as a worker | Claude `/login` bills as extra usage |
| **Hermes Agent** | Always-on, with memory and skills; Codex login works as a worker | Claude login bills as extra usage and often errors; Agent SDK provider is off by default |
| **OpenCode** | Good interface; works with many providers | Claude only with an API key |
| **Cursor / Windsurf** | Full editor with Claude built in | Claude runs through their backend, never your subscription |
| **API keys for both** | Fully supported; works in any tool; best for products and automation | Pay per token for everything |

## Uncertain

| Option | Why |
|---|---|
| **OpenClaw setup-token** | Gives OpenClaw your subscription token directly, closer to what Anthropic's terms prohibit |

## Avoid

| Option | Why |
|---|---|
| **CLIProxyAPI (Claude side), pi-sub-anthropic / pi-claude-max, OpenCode auth plugins, hermes-claude-auth** | They reuse your subscription token or pretend to be Claude Code, which goes against Anthropic's terms and risks your account |

## Reviewer model notes (Droid Missions validator)

- **Opus 5.5:** cheapest; checks against its own plan, so not fully independent.
- **GPT-6 Astra:** strong at coding; may share blind spots with Sol (same company).
- **Fable 5.1:** most independent and capable reviewer; roughly twice Astra's cost per task.
- Sensible default: Opus reviews each milestone, Fable 5.1 does one final review.

## Related

- [Bug Hunt Bench](https://github.com/phuryn/bug-hunt-bench) by Pawel Huryn tests models on 105 planted bugs; Main Street Bench tests harnesses on small-business tasks. His grading method (planted items only, blind grading, no partial credit, multiple runs) inspired this bench.
