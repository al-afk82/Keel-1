"""
Layer 2 test — offline logic check for Agent 03 (Human Profiler) and
Agent 04 (Engine Profiler).

This bypasses Band entirely. It loads each agent's real SYSTEM_PROMPT, sends
sample inputs straight to Claude, and checks the returned JSON matches the
`profile` schema in shared/schema.json (agent / status / id / role / scope).

It tests the part you authored — the prompt — not Band's plumbing.

Run:
    uv run python test_profilers.py

Needs ANTHROPIC_API_KEY in .env. Does NOT need agent_config.yaml or Band.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

ROOT = Path(__file__).parent

# Each agent.py exposes a module-level SYSTEM_PROMPT. The folders have hyphens,
# so load the module by file path rather than a normal import.
AGENTS = [
    {
        "name": "human-profiler",
        "file": ROOT / "agent-human-profiler" / "agent.py",
        "samples": [
            # A non-technical founder — should read as a business/founder role.
            "hey can someone explain what an API is? my devs keep saying it and "
            "I need to understand it for an investor call tomorrow",
            # A senior engineer — should read as a technical/expert role.
            "What's the tradeoff between optimistic and pessimistic locking for a "
            "high-write Postgres table? Assume I know the basics of MVCC.",
        ],
    },
    {
        "name": "engine-profiler",
        "file": ROOT / "agent-engine-profiler" / "agent.py",
        "samples": [
            # Engine thinking that drifted into deep code-review territory.
            "The user asked me to summarize this file. I'll read through it, but I "
            "also notice a SQL injection risk on line 40 and an unused import. I "
            "should point out every bug I can find and suggest a refactor.",
            # Engine thinking that stayed scoped to a plain explanation.
            "They want a plain-language answer for a non-technical audience. I'll "
            "avoid jargon, give one analogy, and keep it to a few sentences.",
        ],
    },
]

REQUIRED_KEYS = {"agent", "status", "id", "role", "scope"}


def load_system_prompt(agent_file: Path) -> str:
    """Import an agent.py by path and return its SYSTEM_PROMPT."""
    spec = importlib.util.spec_from_file_location(
        f"_agent_{agent_file.parent.name}", agent_file
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SYSTEM_PROMPT


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of the model's reply, tolerating
    code fences or stray prose."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw = fenced.group(1) if fenced else None
    if raw is None:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        raw = brace.group(0) if brace else text
    return json.loads(raw)


def check(verdict: dict, expected_agent: str) -> list[str]:
    """Return a list of problems with this verdict. Empty list == pass."""
    problems = []
    missing = REQUIRED_KEYS - verdict.keys()
    if missing:
        problems.append(f"missing keys: {sorted(missing)}")
    if verdict.get("agent") != expected_agent:
        problems.append(f"agent != {expected_agent!r} (got {verdict.get('agent')!r})")
    if verdict.get("status") != "profiled":
        problems.append(f"status != 'profiled' (got {verdict.get('status')!r})")
    for field in ("role", "scope"):
        val = verdict.get(field)
        if not isinstance(val, str) or not val.strip():
            problems.append(f"{field} is empty or not a string")
    return problems


def main() -> int:
    load_dotenv()
    # No tools bound: offline, the model returns the JSON as plain text instead
    # of calling band_send_message. That is exactly what we want to inspect.
    llm = ChatAnthropic(model="claude-sonnet-4-6")

    total = 0
    failures = 0

    for agent in AGENTS:
        prompt = load_system_prompt(agent["file"])
        print(f"\n{'=' * 70}\n{agent['name']}\n{'=' * 70}")
        for i, sample in enumerate(agent["samples"], 1):
            total += 1
            messages = [SystemMessage(content=prompt), HumanMessage(content=sample)]
            reply = llm.invoke(messages).content
            print(f"\n[{i}] input: {sample[:80]}...")
            try:
                verdict = extract_json(reply)
            except json.JSONDecodeError:
                failures += 1
                print(f"    FAIL — could not parse JSON. Raw reply:\n{reply}")
                continue

            problems = check(verdict, agent["name"])
            print(f"    role:  {verdict.get('role')}")
            print(f"    scope: {verdict.get('scope')}")
            if problems:
                failures += 1
                print(f"    FAIL — {'; '.join(problems)}")
            else:
                print("    PASS")

    print(f"\n{'=' * 70}\n{total - failures}/{total} passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
