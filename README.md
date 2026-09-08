# hermes-core-skills

Public, sanitized AgentOS tree plus shared Hermes skills.

This is the commander map (where work goes) and the how-to skills. It is not a dump of live work, vault notes, Tesla/home telemetry, credentials, or other git repos.

## AgentOS

Copy or clone this repository to `~/AgentOS`. Hermes should start with this directory as cwd so `AGENTS.md` loads.

| Path | Purpose |
|---|---|
| `instruction.md` | Deploy / re-deploy playbook |
| `AGENTS.md` | Commander constitution |
| `board/` | Inbox / doing / blocked / done |
| `vault/` | Compounding notes (empty skeleton here) |
| `workspaces/<domain>/` | Domain sandboxes (`AGENTS.md` only; `active/` is gitignored) |
| `projects/` | Pointer for real git repos |
| `shared/` | Templates and schemas |
| `skills/` | Hermes skills to copy or symlink into `~/.hermes/skills/` |

Live workspace contents, SQLite history, model weights, `.env`, and tokens stay off this repo.

## Skills

Install by copying or symlinking a skill directory into `~/.hermes/skills/<category>/`.

| Skill | Category | Use when |
|---|---|---|
| [coding-agent-routing](skills/autonomous-ai-agents/coding-agent-routing/SKILL.md) | autonomous-ai-agents | Coding or delegating implementation to OpenCode, Claude Code, or Codex |

`coding-agent-routing` includes `scripts/session_check.py`, which picks a harness from Claude/Codex quota remaining.

## License

MIT
