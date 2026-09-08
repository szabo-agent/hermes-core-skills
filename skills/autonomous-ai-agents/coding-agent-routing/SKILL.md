---
name: coding-agent-routing
description: "Use when coding or delegating implementation to workers."
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [coding, orchestration, opencode, claude-code, codex, littlebeast]
    category: autonomous-ai-agents
    related_skills: [opencode, claude-code, codex, pick-workspace, spike]
---

# Coding agent routing

Hermes is the commander on littlebeast. Non-trivial code is written by a worker, not by Hermes hand-editing a pile of files.

Default worker: **OpenCode** on local Nemotron (`llama.cpp/nemotron-lightning` → `http://127.0.0.1:10000/v1`).
Escalate to **Claude Code** or **Codex** only when the task is complex.

After picking a worker, load that worker's skill (`opencode`, `claude-code`, or `codex`) and follow it. This skill only decides *who* and *when*.

## When to Use

- Any request to build, implement, refactor, prototype, or fix code
- You are about to write more than a trivial patch yourself
- User says use OpenCode / Claude / Codex, or "just build it"

Do not use for: research-only, vault notes, config/instruction edits, 1–2 line patches in files you already have open, or questions with no code change.

## Router

| Worker | Use for | Do not use for |
|---|---|---|
| **OpenCode** (default) | Basic/general: mechanical edits, spikes, throwaway prototypes, tests for a known shape, "make this work", local-only work | Hard architecture, design taste, security review, multi-worktree PR campaigns |
| **Claude Code** | Complex reasoning, reviews, gnarly bugs after a worker failed. Design only when Codex window is worse than Claude's | Cheap mechanical edits; same tree as another worker |
| **Codex** | Complex git work; **design** (5.6 Sol/Astra ≈ Opus). Features, PRs, worktrees | Luna for design (too light); overlapping another worker's tree |

Tie-breakers:

1. User names a worker → that worker.
2. No git repo and the work is a spike/prototype → OpenCode in `workspaces/coding/active/` (init git only if Codex is required).
3. Real git repo + feature/PR → Codex.
4. Needs a designed artifact (Three.js, UI, motion) → Codex Sol (5.6 ≈ Opus). Claude if Codex 5h is critical. Astra if asked.
5. Unsure → OpenCode first. Escalate with the failed attempt as context.

Never run two workers on the same working tree. Parallel only via separate git worktrees or separate spike dirs.

## Procedure

1. **Scope.** One workspace, one tree. Name cwd, files, and done-definition. Classify the task: `basic` | `design` | `git` | `complex`. If the human named a git repo, work there; otherwise `~/AgentOS/workspaces/coding/active/<slug>/`.
2. **Session check (mandatory before any cloud worker).** Run:

```
python3 ~/.hermes/skills/autonomous-ai-agents/coding-agent-routing/scripts/session_check.py --task <basic|design|git|complex> [--repo] [--named claude|codex|opencode] [--codex-model astra|sol|luna]
```

Honor `pick.harness`, `pick.model`, `pick.effort`. Say remaining % in one line. Do not dispatch Claude/Codex when the script marks them critical/exhausted unless the user named that harness *and* you warned. OpenCode is the quota-free fallback.
3. **Load** the matching worker skill. Do not invent CLI flags.
4. **Dispatch** using `pick.command` (swap in the real task). Self-contained prompt: goal, constraints, files, done-definition, "do not commit unless the card says so".
5. **Wait / poll.** Do not interleave your own writes into that tree while the worker is running.
6. **Review.** `git diff` or file list + tests. If the worker failed or the result is sloppy, escalate (OpenCode → Claude or Codex **after another session_check**), do not silently rewrite everything yourself.
7. **Integrate.** Summarize what changed, where, and what you verified. File artifacts under workspace `out/` if they are done.

Done when: session_check ran, worker exited, you inspected the diff, tests or a smoke run happened, and the user gets a path + result (not a plan).

## Quota → model / thinking

Bands use **min(5-hour remaining, 7-day remaining)** from `claude-usage --cli` and `codex-cli-usage json`.

Codex windows are a **shared credit pool**. The % remaining is real. Message counts are OpenAI Plus published ranges scaled by that % — not a token quote. The next task's tokens are unknowable (context, tools, cache, reasoning).

Relative Codex burn (official credits / 1M **input** tokens vs Luna): Astra 50×, Sol 20×, Luna 1×.

| remaining | band | Claude | Codex auto |
|---|---|---|---|
| ≥40% | healthy | design → opus `--effort high`; else sonnet `--effort high` | `gpt-5.6-sol` + effort high |
| 15–39% | tight | sonnet `--effort medium` | `gpt-5.6-luna` + effort medium |
| 5–14% | critical | skip unless named; sonnet `--effort low` | skip unless named; luna + low |
| <5% / error | exhausted | other harness or OpenCode | other harness or OpenCode |

Astra (`gpt-6-astra`) is opt-in: `--codex-model astra`. Do not auto-pick it — one typical turn is ~4% of a Plus 5h bar. Design stays on Sol (never auto-Luna). OpenCode always `llama.cpp/nemotron-lightning`.

session_check prints `est_local_msgs_left_this_5h` for Astra/Sol/Luna. Use that as a budget, not a promise.

## Dispatch one-liners

Prefer `pick.command` from session_check. Templates:

```
opencode run --model llama.cpp/nemotron-lightning '<task>'

claude -p '<task>' --model sonnet --effort medium --allowedTools 'Read,Edit,Write,Bash' --max-turns 20

codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" --sandbox workspace-write '<task>'
codex exec -m gpt-5.6-luna -c model_reasoning_effort="medium" --sandbox workspace-write '<task>'
codex exec -m gpt-6-astra -c model_reasoning_effort="high" --sandbox workspace-write '<task>'
```

Always pass `--model` / `-m` and Claude `--effort` / Codex `model_reasoning_effort` explicitly.

Long jobs: `background=true` and `process` poll. Interactive TUI only when print/exec/run is not enough — then follow the worker skill (tmux for Claude, pty for Codex/OpenCode TUI).

## House rules (littlebeast)

- One heavy local inference: Nemotron is already on `:10000`. Do not start gpt-oss-120b beside it.
- If disk is under ~15% free, or swap is thrashing, do not dispatch. Say so.
- If Dave is at the seat and the task is not urgent, prefer Claude/Codex (cloud) over extra local GPU load — OpenCode is still OK; it reuses the already-running server.
- Do not raise windows. Do not commit, push, or touch `.env` unless asked.
- `delegate_task` is for Hermes subagents (research/review), not a substitute for these CLIs.

## Pitfalls

1. **Hermes implements the feature anyway.** If it is more than a trivial patch, you already failed this skill.
2. **Wrong model or skipped quota check.** Always run session_check first. OpenCode: `llama.cpp/nemotron-lightning`. Claude: only opus/sonnet + explicit `--effort`. Codex: `gpt-5.6-sol` (healthy), `gpt-5.6-luna` (tight), `gpt-6-astra` only if asked. Never burn a critical 5-hour window on opus/Astra/high.
3. **Codex outside git.** It will refuse. `git init` in a spike dir only if you meant to use Codex.
4. **Two workers, one tree.** Collisions. Worktrees or separate dirs.
5. **Skipping the worker skill.** Flags rot. Load `opencode` / `claude-code` / `codex` after the pick.
6. **No review.** Worker output is a self-report until you `git diff` and run something.

## Verification

- [ ] session_check.py ran; remaining % spoken; pick honored
- [ ] Worker chosen from the table **and** quota bands
- [ ] Matching skill loaded
- [ ] Command used pick.command (or the worker skill's current equivalent)
- [ ] OpenCode model was `llama.cpp/nemotron-lightning` when OpenCode ran
- [ ] Claude used opus or sonnet with `--effort`; Codex used sol, luna, or astra with reasoning effort; cost line spoken
- [ ] Diff inspected; smoke/test run if code changed
- [ ] No second worker on the same tree
- [ ] User got paths and outcome, not a promise
