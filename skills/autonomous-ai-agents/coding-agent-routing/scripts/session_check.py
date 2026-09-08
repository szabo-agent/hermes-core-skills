#!/usr/bin/env python3
"""Quota-aware harness pick for coding dispatch.

Reads:
  claude-usage --cli
  codex-cli-usage json
  llama-server http://127.0.0.1:10000/v1/models

Codex windows are a shared credit pool (percent remaining is real).
Per-model "messages left" are OpenAI's published Plus 5h ranges scaled by
that percent — estimates, not a meter. Token cost of the *next* task is
not knowable (context, tools, cache, reasoning). Relative burn is.

Does not print secrets. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from typing import Any

LLAMA = "http://127.0.0.1:10000/v1/models"
OPENCODE_MODEL = "llama.cpp/nemotron-lightning"
TIMEOUT = 20

HEALTHY = 40
TIGHT = 15
CRITICAL = 5

# Official Codex credit card + Plus local-msgs / 5h (developers.openai.com/codex/pricing).
# Input-credit ratio vs Luna is the relative session burn we can actually use.
CODEX_MODELS: dict[str, dict[str, Any]] = {
    "gpt-6-astra": {
        "label": "Astra",
        "plus_msgs_5h": (5, 45),
        "credits_per_1m": {"input": 250, "cached": 25, "output": 1250},
        "rel_to_luna": 50.0,
    },
    "gpt-5.6-sol": {
        "label": "Sol",
        "plus_msgs_5h": (10, 100),
        "credits_per_1m": {"input": 100, "cached": 10, "output": 500},
        "rel_to_luna": 20.0,
    },
    "gpt-5.6-luna": {
        "label": "Luna",
        "plus_msgs_5h": (250, 2000),
        "credits_per_1m": {"input": 5, "cached": 0.5, "output": 30},
        "rel_to_luna": 1.0,
    },
}

CODEX_IDS = {
    "astra": "gpt-6-astra",
    "sol": "gpt-5.6-sol",
    "luna": "gpt-5.6-luna",
    "gpt-6-astra": "gpt-6-astra",
    "gpt-5.6-sol": "gpt-5.6-sol",
    "gpt-5.6-luna": "gpt-5.6-luna",
}


def band(remaining: float | None) -> str:
    if remaining is None:
        return "unknown"
    if remaining < CRITICAL:
        return "exhausted"
    if remaining < TIGHT:
        return "critical"
    if remaining < HEALTHY:
        return "tight"
    return "healthy"


def usable(b: str) -> bool:
    return b in ("healthy", "tight", "unknown")


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=TIMEOUT, check=False
        )
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, f"missing: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout: {' '.join(cmd)}"
    except Exception as e:
        return 1, f"{type(e).__name__}: {e}"


def parse_claude(text: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "ok": False,
        "used_5h": None,
        "remaining_5h": None,
        "resets_5h": None,
        "used_7d": None,
        "remaining_7d": None,
        "resets_7d": None,
        "error": None,
    }
    if "Rate Limits: unavailable" in text:
        info["error"] = "claude-usage: rate limits unavailable (sign in)"
        return info
    pat = re.compile(
        r"(5-Hour|7-Day):\s+([\d.]+)% used \(\s*([\d.]+)% remaining\)"
        r"(?:\s+resets in (.+?))?\s*$",
        re.M,
    )
    found = False
    for m in pat.finditer(text):
        found = True
        label, used, rem = m.group(1), float(m.group(2)), float(m.group(3))
        reset = (m.group(4) or "").strip() or None
        if label.startswith("5"):
            info["used_5h"], info["remaining_5h"], info["resets_5h"] = used, rem, reset
        else:
            info["used_7d"], info["remaining_7d"], info["resets_7d"] = used, rem, reset
    if not found:
        info["error"] = "claude-usage: could not parse rate limits"
        return info
    info["ok"] = True
    rems = [r for r in (info["remaining_5h"], info["remaining_7d"]) if r is not None]
    info["remaining"] = min(rems) if rems else None
    info["band"] = band(info["remaining"])
    info["note"] = (
        "Claude Pro windows are percent-of-pool only. No official msgs/5h table "
        "like Codex; opus burns the bar faster than sonnet, not quantified here."
    )
    return info


def parse_codex(text: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "ok": False,
        "used_5h": None,
        "remaining_5h": None,
        "resets_5h": None,
        "used_7d": None,
        "remaining_7d": None,
        "resets_7d": None,
        "plan": None,
        "error": None,
    }
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        info["error"] = "codex-cli-usage: not JSON"
        return info
    if not isinstance(data, dict):
        info["error"] = "codex-cli-usage: unexpected JSON"
        return info
    info["plan"] = data.get("plan")
    five = data.get("5h") or data.get("primary") or {}
    week = data.get("7d") or data.get("secondary") or {}
    if "pct" in five:
        info["used_5h"] = float(five["pct"])
        info["remaining_5h"] = max(0.0, 100.0 - float(five["pct"]))
        info["resets_5h"] = five.get("resets_at")
    if "pct" in week:
        info["used_7d"] = float(week["pct"])
        info["remaining_7d"] = max(0.0, 100.0 - float(week["pct"]))
        info["resets_7d"] = week.get("resets_at")
    rems = [r for r in (info["remaining_5h"], info["remaining_7d"]) if r is not None]
    if not rems:
        info["error"] = "codex-cli-usage: no window pct"
        return info
    info["remaining"] = min(rems)
    info["band"] = band(info["remaining"])
    info["ok"] = True
    return info


def llama_ok() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(LLAMA, timeout=2) as r:
            body = r.read(2048)
        ok = r.status == 200 and b"model" in body
        return {
            "ok": ok,
            "endpoint": "http://127.0.0.1:10000/v1",
            "error": None if ok else "unexpected /v1/models",
        }
    except Exception as e:
        return {"ok": False, "endpoint": "http://127.0.0.1:10000/v1", "error": str(e)}


def estimate_codex(remaining_5h: float | None, plan: str | None) -> dict[str, Any]:
    """Scale OpenAI Plus 5h message ranges by remaining %. Not a token meter."""
    frac = None if remaining_5h is None else max(0.0, remaining_5h) / 100.0
    plan_note = (
        "ranges are Plus local-msgs/5h from OpenAI; this account plan="
        f"{plan or 'unknown'}. Pro 5x/20x would be higher. Cloud chats cost more."
    )
    out: dict[str, Any] = {"plan": plan, "note": plan_note, "models": {}}
    for mid, spec in CODEX_MODELS.items():
        lo, hi = spec["plus_msgs_5h"]
        midpt = (lo + hi) / 2
        est = None
        if frac is not None:
            est = {
                "lo": round(lo * frac, 1),
                "hi": round(hi * frac, 1),
                "mid": round(midpt * frac, 1),
            }
        out["models"][mid] = {
            "label": spec["label"],
            "rel_to_luna": spec["rel_to_luna"],
            "credits_per_1m_tokens": spec["credits_per_1m"],
            "plus_local_msgs_per_5h_full": {"lo": lo, "hi": hi},
            "est_pct_of_5h_per_typical_msg": round(100.0 / midpt, 2),
            "est_local_msgs_left_this_5h": est,
        }
    return out


def claude_pick(b: str, task: str) -> tuple[str, str]:
    if task == "design" and b == "healthy":
        return "opus", "high"
    if b == "healthy":
        return "sonnet", "high"
    if b in ("tight", "unknown"):
        return "sonnet", "medium"
    return "sonnet", "low"


def codex_effort(b: str) -> str:
    if b == "healthy":
        return "high"
    if b in ("tight", "unknown"):
        return "medium"
    return "low"


def auto_codex_model(b: str, remaining: float | None, task: str = "complex") -> str:
    """Astra is opt-in (50× Luna). Design stays on Sol (5.6 ≈ Opus), never Luna."""
    if task == "design":
        return "gpt-5.6-sol"
    if b == "healthy":
        return "gpt-5.6-sol"
    return "gpt-5.6-luna"


def command_for(harness: str, model: str, effort: str | None) -> str:
    if harness == "opencode":
        return f"opencode run --model {OPENCODE_MODEL} '<task>'"
    if harness == "claude":
        return (
            f"claude -p '<task>' --model {model} --effort {effort or 'medium'} "
            "--allowedTools 'Read,Edit,Write,Bash' --max-turns 20"
        )
    if harness == "codex":
        return (
            f"codex exec -m {model} -c model_reasoning_effort=\"{effort or 'medium'}\" "
            "--sandbox workspace-write '<task>'"
        )
    return ""


def decide(
    task: str,
    repo: bool,
    named: str | None,
    codex_model_opt: str | None,
    claude: dict,
    codex: dict,
    local: dict,
) -> dict[str, Any]:
    c_ok = claude.get("ok") and usable(claude.get("band", "exhausted"))
    x_ok = codex.get("ok") and usable(codex.get("band", "exhausted"))
    o_ok = local.get("ok")

    preferred = {
        "basic": "opencode",
        "design": None,
        "git": "codex",
        "complex": None,
    }[task]

    # Design: Codex 5.6 Sol/Astra is treated as an Opus peer. Quota picks the harness.
    if task == "design":
        if x_ok:
            preferred = "codex"
        elif c_ok:
            preferred = "claude"
        else:
            preferred = "opencode"

    if task == "complex":
        if repo and x_ok and c_ok:
            preferred = (
                "codex"
                if (codex.get("remaining") or 0) >= (claude.get("remaining") or 0)
                else "claude"
            )
        elif repo and x_ok:
            preferred = "codex"
        elif c_ok:
            preferred = "claude"
        else:
            preferred = "opencode"

    if named:
        preferred = named

    def fallbacks(start: str) -> list[str]:
        if start == "claude":
            return ["codex", "opencode"]
        if start == "codex":
            return ["claude", "opencode"]
        return (["codex"] if x_ok else []) + (["claude"] if c_ok else [])

    harness = preferred
    reason_bits: list[str] = []

    def can(h: str) -> bool:
        if h == "opencode":
            return True
        if h == "claude":
            return bool(c_ok)
        if h == "codex":
            # Design spikes may git init; do not block Codex on --repo.
            return bool(x_ok) and (repo or task in ("git", "design"))
        return False

    if named and not can(named) and named != "opencode":
        reason_bits.append(f"named {named} is not usable (quota or no git repo)")
        for h in fallbacks(named) + ["opencode"]:
            if can(h) or h == "opencode":
                harness = h
                break
    elif not named and not can(harness) and harness != "opencode":
        reason_bits.append(f"preferred {harness} is not usable")
        for h in fallbacks(harness) + ["opencode"]:
            if can(h) or h == "opencode":
                harness = h
                break

    if harness == "claude":
        model, effort = claude_pick(claude.get("band", "unknown"), task)
        reason_bits.append(
            f"Claude 5h {claude.get('remaining_5h')}% left ({claude.get('band')}) → {model}/{effort}"
        )
    elif harness == "codex":
        b = codex.get("band", "unknown")
        model = codex_model_opt or auto_codex_model(b, codex.get("remaining_5h"), task)
        effort = codex_effort(b)
        spec = CODEX_MODELS[model]
        reason_bits.append(
            f"Codex 5h {codex.get('remaining_5h')}% left ({b}) → {spec['label']}/{effort} "
            f"({spec['rel_to_luna']:g}× Luna credits)"
        )
        if task == "design":
            reason_bits.append("design: Codex 5.6 Sol/Astra treated as Opus-peer")
            if not repo:
                reason_bits.append("git init the spike")
        elif not repo and named == "codex":
            reason_bits.append("Codex needs a git repo")
        if codex_model_opt:
            reason_bits.append(f"codex-model override {model}")
    else:
        model, effort = OPENCODE_MODEL, None
        reason_bits.append("OpenCode local Nemotron (no cloud quota)")
        if not o_ok:
            reason_bits.append(f"llama-server not reachable: {local.get('error')}")

    if named and named != harness:
        reason_bits.append(f"overrode named={named}")

    return {
        "harness": harness,
        "model": model,
        "effort": effort,
        "reason": "; ".join(reason_bits),
        "command": command_for(harness, model, effort),
        "named": named,
        "preferred": preferred,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Pick coding harness from live Claude/Codex quota.")
    ap.add_argument("--task", choices=["basic", "design", "git", "complex"], default="complex")
    ap.add_argument("--repo", action="store_true", help="cwd is a git repo (Codex-eligible)")
    ap.add_argument("--named", choices=["opencode", "claude", "codex"], default=None)
    ap.add_argument(
        "--codex-model",
        choices=sorted(CODEX_IDS.keys()),
        default=None,
        help="Force Astra / Sol / Luna when Codex is picked",
    )
    ap.add_argument("--json", action="store_true", help="JSON only")
    args = ap.parse_args()
    repo = args.repo or args.task == "git"
    forced = CODEX_IDS.get(args.codex_model) if args.codex_model else None

    claude_bin = shutil.which("claude-usage") or "claude-usage"
    codex_bin = shutil.which("codex-cli-usage") or "codex-cli-usage"

    c_code, c_out = run([claude_bin, "--cli"])
    x_code, x_out = run([codex_bin, "json"])

    claude = parse_claude(c_out) if c_code == 0 else {
        "ok": False, "band": "unknown", "remaining": None, "error": c_out[:300]
    }
    if c_code != 0:
        claude["ok"] = False
        claude["band"] = "unknown"

    codex = parse_codex(x_out) if x_code == 0 else {
        "ok": False, "band": "unknown", "remaining": None, "error": x_out[:300]
    }
    if x_code != 0:
        codex["ok"] = False
        codex["band"] = "unknown"

    local = llama_ok()
    pick = decide(args.task, repo, args.named, forced, claude, codex, local)
    estimates = estimate_codex(codex.get("remaining_5h"), codex.get("plan"))

    result = {
        "task": args.task,
        "repo": repo,
        "claude": claude,
        "codex": codex,
        "opencode": local,
        "codex_cost": estimates,
        "pick": pick,
        "knowable": {
            "exact": "5h/7d percent remaining (shared credit pool per product)",
            "estimated": "Codex local msgs left = Plus published range × remaining_5h%",
            "unknowable": (
                "tokens the next task will burn. OpenAI: model, context, reasoning, "
                "tools, retrieval, cache all move the bar; prompt length is not a quote."
            ),
        },
        "rules": {
            "claude_models": ["opus", "sonnet"],
            "codex_models": list(CODEX_MODELS),
            "opencode_model": OPENCODE_MODEL,
            "auto_codex": "design → always sol (5.6 ≈ Opus); else healthy → sol, tight → luna; astra only via --codex-model",
            "bands": {
                "healthy": f">={HEALTHY}% remaining",
                "tight": f"{TIGHT}–{HEALTHY - 1}",
                "critical": f"{CRITICAL}–{TIGHT - 1}",
                "exhausted": f"<{CRITICAL}",
            },
        },
    }

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    p = pick
    print(
        f"pick {p['harness']} model={p['model']}"
        + (f" effort={p['effort']}" if p.get("effort") else "")
        + f" | claude 5h {claude.get('remaining_5h')}% ({claude.get('band')})"
        + f" | codex 5h {codex.get('remaining_5h')}% ({codex.get('band')})"
        + f" | llama {'up' if local.get('ok') else 'down'}"
    )
    print(p["reason"])
    print(p["command"])
    rem = codex.get("remaining_5h")
    if rem is not None:
        print(f"Codex session cost (Plus ranges × {rem:g}% of 5h left, not a quote):")
        for mid, row in estimates["models"].items():
            left = row["est_local_msgs_left_this_5h"]
            if not left:
                continue
            mark = " ← pick" if mid == p.get("model") else ""
            print(
                f"  {row['label']:5} {mid:14} {row['rel_to_luna']:4g}× Luna | "
                f"~{left['lo']:g}–{left['hi']:g} local msgs left "
                f"(~{row['est_pct_of_5h_per_typical_msg']}% of 5h / typical msg){mark}"
            )
    print("---")
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
