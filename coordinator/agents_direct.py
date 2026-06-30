#!/usr/bin/env python3
"""
Direct agent caller — Band stripped.

Each drift agent is, underneath its Band wrapper, just a system prompt and a
model. This module lifts those out and calls Anthropic directly, so the
coordinator runs the agents in process with no Band, no bridge, no session.

Both run_chain.py and the harness backend import direct_call from here, so
stripping Band happens in one place for every surface.

The agent directories (agent-*) live in the hackathon repo. Point AGENTS_ROOT at
it; defaults to the repo this file sits in.
"""

import ast
import json
import os
import re
from pathlib import Path

import requests

# Where the agent-* directories live. On the server the harness runs from a
# different folder than the agents, so this is overridable.
AGENTS_ROOT = Path(os.getenv("AGENTS_ROOT", Path(__file__).resolve().parent.parent))

# Route name (the same names the Band bridge used) -> agent directory.
AGENTS: dict[str, str] = {
    "03-human-profiler":       "agent-human-profiler",
    "04-engine-profiler":      "agent-engine-profiler",
    "05-alignment-classifier": "agent-alignment-checker",
    "06-question-generator":   "agent-question-generator",
    "07-gap-analyzer":         "agent-gap-analyzer",
    "08-constraints-checker":  "agent-constraints",
    "09-anti-patterns-checker": "agent-antipatterns",
    "10-voice-checker":        "agent-voice-checker",
    "11-quality-checker":      "agent-quality-checker",
    "12-identity-agent":       "agent-identity",
    "13-verifier":             "agent-verifier",
}

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

_cache: dict[str, tuple[str, str]] = {}


def _load_key() -> str:
    """Key from the environment, falling back to the agents' .env file."""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key:
        return key
    env = AGENTS_ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _load_prompt_and_model(agent_dir: str) -> tuple[str, str]:
    """Reproduce an agent's exact SYSTEM_PROMPT and model without importing it.

    The agent modules import the Band SDK at the top, so we cannot import them.
    Instead we parse the file and evaluate only the assignments that build the
    prompt — RULES and IDENTITY read a reference file, SYSTEM_PROMPT is a plain
    string or an f-string over those — in order, in a tiny namespace. This gives
    the prompt byte for byte, reference files included, with no Band dependency.
    """
    path = AGENTS_ROOT / agent_dir / "agent.py"
    src = path.read_text()
    tree = ast.parse(src)

    model = DEFAULT_MODEL
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "model" and isinstance(node.value, ast.Constant):
            model = node.value.value

    ns: dict = {"Path": Path, "__file__": str(path)}
    wanted = {"RULES", "IDENTITY", "SYSTEM_PROMPT", "AGENT_NAME"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in wanted:
            try:
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
            except Exception:
                pass
    return ns.get("SYSTEM_PROMPT", ""), model


def _get(route: str) -> tuple[str, str]:
    if route not in _cache:
        _cache[route] = _load_prompt_and_model(AGENTS[route])
    return _cache[route]


_FENCE_OPEN = re.compile(r"^```[a-zA-Z]*\s*")
_FENCE_CLOSE = re.compile(r"\s*```$")


def _parse_json(text: str):
    """Agents reply with JSON, sometimes fenced, with leading prose, as an object
    or as a bare array. Try the whole thing, then an object slice, then an array
    slice, so every shape parses."""
    t = _FENCE_OPEN.sub("", (text or "").strip())
    t = _FENCE_CLOSE.sub("", t.strip())
    try:
        return json.loads(t)
    except Exception:
        pass
    for op, cl in (("{", "}"), ("[", "]")):
        s, e = t.find(op), t.rfind(cl)
        if s != -1 and e > s:
            try:
                return json.loads(t[s:e + 1])
            except Exception:
                continue
    raise ValueError("no json")


_SEVERITY_RANK = {"violation": 4, "drifted": 3, "misaligned": 3, "mismatch": 3,
                  "gap-found": 3, "fail": 3, "uncertain": 2, "clean": 1}


def _collapse(subs: list, name: str) -> dict:
    subs = [f for f in subs if isinstance(f, dict)]
    if not subs:
        return {"agent": name, "status": "clean", "rule": None, "excerpt": None, "severity": None}
    worst = max(subs, key=lambda f: _SEVERITY_RANK.get(str(f.get("status", "")).lower(), 0))
    return {"agent": name, "status": worst.get("status"), "rule": worst.get("rule"),
            "excerpt": worst.get("excerpt"), "severity": worst.get("severity")}


def _normalize(route: str, result):
    """Some agents (the verifier) return a wrapper of sub findings, or a bare list,
    instead of one flat verdict. Collapse either to a single verdict by its worst
    sub finding so every consumer gets the uniform flat shape."""
    name = "verifier" if route == "13-verifier" else route
    if isinstance(result, list):
        return _collapse(result, name)
    if isinstance(result, dict) and "findings" in result and "status" not in result:
        return _collapse(result.get("findings", []), name)
    return result


def direct_call(route: str, payload: dict) -> tuple[str, dict]:
    """Run one agent directly against Anthropic. Same signature and return shape
    the Band bridge_call had: (route, finding_dict)."""
    if route not in AGENTS:
        return route, {"agent": route, "error": f"unknown route {route}"}
    try:
        prompt, model = _get(route)
        r = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": _load_key(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": MAX_TOKENS,
                "system": prompt,
                "messages": [{"role": "user", "content": json.dumps(payload)}],
            },
            timeout=60,
        )
        data = r.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        try:
            return route, _normalize(route, _parse_json(text))
        except Exception:
            return route, {"agent": route, "raw": text}
    except Exception as exc:
        return route, {"agent": route, "error": str(exc)}


# Convenience aliases so existing code can swap with one import line.
bridge_call = direct_call
call = direct_call


if __name__ == "__main__":
    # Self test: load every prompt and report, no model calls.
    for r, d in AGENTS.items():
        p, m = _get(r)
        print(f"{r:24} {d:24} model={m:22} promptlen={len(p):5} {'OK' if p else 'EMPTY'}")
