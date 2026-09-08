# coding

Cwd for software, agents, MCP, local LLM harnesses, scripts.

## Layout
- inbox/ raw requests
- active/ current branch of work
- out/ patches, reports, snippets ready to move into a real repo

## Rules
- If a git repo exists under ~/AgentOS/projects or a path the human names, work in the repo, not here
- Put a thin AGENTS.md in any new repo you create
- Do not store model weights here
- Run destructive git only with explicit approval
- Load skill coding-agent-routing before implementing. Hermes does not hand-write non-trivial code.

## Workers
Before Claude or Codex, run:
```
python3 ~/.hermes/skills/autonomous-ai-agents/coding-agent-routing/scripts/session_check.py --task <basic|design|git|complex> [--repo] [--codex-model astra|sol|luna]
```
Honor the printed pick (harness, model, effort). OpenCode if the cloud window is critical.

Default: OpenCode on local Nemotron.
```
opencode run --model llama.cpp/nemotron-lightning '<task>'
```
Complex design (Three.js, UI, motion): Codex Sol (5.6 ≈ Opus). Claude if Codex 5h is critical. git init the spike.
```
codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" --sandbox workspace-write '<task>'
```
Complex reasoning/review when Codex is tight: Claude. opus or sonnet only; pass `--effort` from session_check.
Complex git/PR/worktrees: Codex (repo required). Auto sol (healthy) or luna (tight). Astra via `--codex-model astra`.
```
codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" --sandbox workspace-write '<task>'
codex exec -m gpt-5.6-luna -c model_reasoning_effort="medium" --sandbox workspace-write '<task>'
```
Load the matching skill (opencode / claude-code / codex) after the pick.
One worker per tree. Review the diff. Do not commit unless asked.