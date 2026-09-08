# hermes-core-skills

The public, sanitized half of a single-profile Hermes agent setup: the **AgentOS tree** that tells the agent where work goes, and the **shared skills** that tell it how to do the work.

It is a working structure, not a demo. The private half — memory, tokens, live telemetry, notes — stays on the machine.

## The two-layer split

The whole design rests on keeping two things apart. Collapsing them is what turns an agent's home directory into a junk drawer.

| Layer | Lives at | Holds | Published here |
|---|---|---|---|
| **Hermes home** | `~/.hermes` | Identity, memory, skills, config, cron, secrets | Skills only |
| **AgentOS** | `~/AgentOS` | Board, vault, workspaces, project clones | Structure only |

Hermes home is *who the agent is*. AgentOS is *where it works*. Artifacts never land in Hermes home; procedures never land in memory.

## The tree

Clone or copy this repository to `~/AgentOS`. Start Hermes with that directory as cwd so `AGENTS.md` loads first.

| Path | Purpose |
|---|---|
| `AGENTS.md` | Commander constitution — read at the top of every session |
| `instruction.md` | Deploy / re-deploy playbook for the whole layout |
| `board/` | Task state: `inbox.md`, `doing.md`, `blocked.md`, `done/` |
| `vault/` | Compounding notes — research, decisions, runbooks, people, logs |
| `workspaces/<domain>/` | Domain sandboxes, one per life area |
| `projects/` | Real git repos (clones or worktrees), never a dump |
| `shared/` | Card, handoff and note templates plus the board-card schema |
| `skills/` | Skills to copy or symlink into `~/.hermes/skills/` |

The vault and board ship as empty skeletons. Workspaces ship with their `AGENTS.md` only — `active/`, `inbox/` and `out/` are gitignored so live work never reaches this repo.

## The operating loop

`AGENTS.md` is short on purpose. It fixes five things:

1. **Pick one workspace.** One domain per session. Work that spans two gets a board card and a switch, never a mixed tree.
2. **Read only that workspace's `AGENTS.md`.** Local rules beat global ones.
3. **Check the board.** `inbox.md` and `doing.md`, at most three active cards.
4. **Route the code.** Anything beyond a trivial patch loads `coding-agent-routing` and goes to a worker.
5. **Land it somewhere durable.** Artifacts to `out/` or a real repo, lessons to a skill or a vault runbook — not chat scrollback.

Each workspace narrows that further. `home-energy` is read-only against live systems unless told otherwise; `cyber` refuses targets the human doesn't own; `research` requires a null-result note when a scan finds nothing; `property` won't invent a price. The rules are the point — they are what makes an unattended session predictable.

| Workspace | Covers |
|---|---|
| `coding` | Software, agents, MCP, local LLM harnesses, scripts |
| `cyber` | Detection notes, lab repros, tooling tests, IR writeups |
| `home-energy` | Solar, batteries, EV charging, tariffs, automation |
| `research` | Open-web and document research |
| `property` | Renovation, contractors, quotes, property admin |
| `personal` | Personal admin, minimum necessary detail |

Add a directory with an `AGENTS.md` when a new life domain appears. Do not add Hermes profiles.

## Skills

Install by copying or symlinking a skill directory into `~/.hermes/skills/<category>/`.

| Skill | Category | Use when |
|---|---|---|
| [coding-agent-routing](skills/autonomous-ai-agents/coding-agent-routing/SKILL.md) | `autonomous-ai-agents` | Building, refactoring, or delegating implementation |

### coding-agent-routing

The house rule is that Hermes commands and workers write the code. The skill decides *who* and *when*, then hands off to that worker's own skill.

- **OpenCode** on a local model is the default and the quota-free fallback — mechanical edits, spikes, prototypes.
- **Codex** takes git work, PRs, worktrees, and designed artifacts.
- **Claude Code** takes complex reasoning and reviews, and design when the Codex window is worse.

Never two workers on one tree. Always inspect the diff — a worker's summary is a self-report until you read it.

Before any cloud worker it runs `scripts/session_check.py`, which reads `claude-usage --cli`, `codex-cli-usage json`, and the local llama-server, sorts each remaining quota into healthy / tight / critical / exhausted bands, and prints a pick plus a ready-to-run command:

```console
$ python3 scripts/session_check.py --task design
pick codex model=gpt-5.6-sol effort=medium | claude 5h 77.0% (healthy) | codex 5h 100.0% (tight) | llama up
codex exec -m gpt-5.6-sol -c model_reasoning_effort="medium" --sandbox workspace-write '<task>'
```

It is stdlib-only, prints no secrets, and adds `--json` for programmatic use. Costs are reported as relative burn against the cheapest model, because the token cost of the *next* task is not knowable — the estimates are a budget, not a meter.

## Requirements

The tree itself needs nothing. `coding-agent-routing` expects the harnesses you actually intend to dispatch — the `opencode`, `claude`, or `codex` CLIs — and `session_check.py` reads `claude-usage` and `codex-cli-usage` when present, degrading to an `unknown` band when they are not.

## Not in this repository

By design, and mostly enforced by `.gitignore`:

- Live workspace contents (`workspaces/*/active`, `inbox`, `out`)
- Vault notes, board history, home telemetry, SQLite databases
- `.env`, tokens, keys, model weights
- Other git repositories

If something here would only make sense on one machine, it does not belong here.

## License

MIT
