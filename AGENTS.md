# AgentOS — commander constitution

Single Hermes home. No profiles.

Root: ~/AgentOS
Hermes home: ~/.hermes (or $HERMES_HOME)

## First actions every session
1. Read this file
2. Use skill pick-workspace unless cwd is already a workspace or project
3. Read only that workspace's AGENTS.md
4. Check ~/AgentOS/board/inbox.md and doing.md
5. If the work is to build or change code, load skill coding-agent-routing before writing more than a trivial patch

## Where things go
| Kind | Path |
|---|---|
| Working files | workspaces/<domain>/active/ |
| Finished artifacts | workspaces/<domain>/out/ |
| Durable notes | vault/ |
| Task state | board/ |
| Real repos | projects/<name>/ or the human's existing git path |
| How-to | ~/.hermes/skills/ |
| Facts | ~/.hermes/memories/MEMORY.md |

## Delegation inside one profile
You may use Hermes delegate_task for parallel file-bounded work.
Each child must get: explicit cwd, explicit files, explicit done-definition.
Children do not write MEMORY.md. You integrate.

## Coding agents
Hermes commands. Workers write non-trivial code. Load skill coding-agent-routing.
Before any cloud worker, run `scripts/session_check.py` (claude-usage --cli + codex-cli-usage json). Honor pick.harness / model / effort.
- OpenCode + llama.cpp/nemotron-lightning (:10000) — default, basic/general, quota-free fallback
- Claude Code — complex reasoning, reviews. opus or sonnet only; design only if Codex window is worse
- Codex — git/PRs, and design (5.6 Sol ≈ Opus; Astra if asked). Auto luna only for non-design tight windows
Skip a cloud harness when 5h/7d remaining is under 15% unless the human named it.
Never two workers on the same tree. Do not commit unless asked.

## Quality bar
- No invented sources
- No secrets in markdown
- Prefer patches over rewrites
- After repeatable work, offer session-wrapup + skill save

## Do not
- Create profiles
- Use $HOME as cwd
- Mix two workspaces in one session
- Commit .env, keys, or credentials