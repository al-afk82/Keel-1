#!/usr/bin/env python3
"""
Reference chain driver.

Pushes one input through the live drift agents via the bridge, collects their
verdicts, and posts the aggregate to the harness logger. This is what the C++
coordinator must do, expressed as runnable code. It is the contract: send this
shape of message, to these routes, in this order, collect this shape back.

Sequence:
  1. 01-logger        fire and forget, logs the raw input
  2. profilers        03 and 04 in parallel, their output is context for step 3
  3. verdict agents   05 through 12 in parallel, each returns a finding
  3.5 verifier        receives non-clean findings from step 3, returns one verdict
  4. 14-harness-logger fire and forget, receives {payload, findings}

The bridge runs on 5055. Verdict routes are synchronous, the bridge waits for
each agent's reply and returns clean JSON. Logger and harness logger are fire
and forget, the bridge returns immediately.

Usage:
  python3 run_chain.py "<human input>" "<engine response>"
"""

import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests

BRIDGE = "http://127.0.0.1:5055/api/agent"
TIMEOUT = 35

PROFILERS = ["03-human-profiler", "04-engine-profiler"]

# Specialist verdict agents. Verifier runs sequentially after these complete.
VERDICT_AGENTS = [
    "05-alignment-classifier",
    "06-question-generator",
    "07-gap-analyzer",
    "08-constraints-checker",
    "09-anti-patterns-checker",
    "10-voice-checker",
    "11-quality-checker",
    "12-identity-agent",
]

# Statuses that represent a real finding — passed to verifier for second-pass audit.
PROBLEM_STATUSES = {"violation", "drifted", "misaligned", "uncertain", "gap-found"}

SKIPPED = []


def call(route: str, payload: dict) -> tuple[str, dict]:
    try:
        resp = requests.post(f"{BRIDGE}/{route}", data=json.dumps(payload), timeout=TIMEOUT)
        try:
            return route, resp.json()
        except ValueError:
            return route, {"agent": route, "raw": resp.text}
    except Exception as exc:
        return route, {"agent": route, "error": str(exc)}


def fan(routes: list[str], payload: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(routes))) as pool:
        for route, result in pool.map(lambda rt: call(rt, payload), routes):
            out[route] = result
    return out


def main() -> None:
    human_input = sys.argv[1] if len(sys.argv) > 1 else (
        "Summarise the lease agreement in two sentences."
    )
    engine_response = sys.argv[2] if len(sys.argv) > 2 else (
        "Here is a haiku about autumn leaves drifting gently to the ground."
    )

    input_id = str(uuid.uuid4())
    base = {
        "input_id": input_id,
        "human_input": human_input,
        "engine_response": engine_response,
    }

    print(f"input_id: {input_id}")
    print(f"human_input: {human_input}")
    print(f"engine_response: {engine_response}")
    if SKIPPED:
        print(f"skipped (key not linked): {', '.join(SKIPPED)}")
    print()

    print("step 1  logging input ...")
    call("01-logger", base)

    print("step 2  profilers ...")
    profiles = fan(PROFILERS, base)
    for route, res in profiles.items():
        print(f"  {route}: {json.dumps(res)[:140]}")

    # Build enriched context that matches the field names specialist prompts expect.
    # thinking_chain and ai_output point at the same value for now — in production
    # these would be split into the engine's raw reasoning vs its final response.
    human_prof = profiles.get("03-human-profiler") or {}
    engine_prof = profiles.get("04-engine-profiler") or {}

    context = dict(base)
    context["human_msg"] = human_input
    context["thinking_chain"] = engine_response
    context["ai_output"] = engine_response
    context["human_scope"] = human_prof.get("scope", "")
    context["engine_scope"] = engine_prof.get("scope", "")
    context["human_profile"] = human_prof
    context["engine_profile"] = engine_prof

    print("step 3  verdict agents ...")
    verdicts = fan(VERDICT_AGENTS, context)
    findings = []
    for route, res in verdicts.items():
        findings.append(res)
        print(f"  {route}: {json.dumps(res)[:140]}")

    print("step 3.5  verifier ...")
    non_clean = [
        f for f in findings
        if isinstance(f, dict) and f.get("status", "").lower().strip() in PROBLEM_STATUSES
    ]
    if non_clean:
        _, verifier_result = call("13-verifier", {"input_id": input_id, "findings": non_clean})
    else:
        verifier_result = {"agent": "verifier", "status": "clean", "rule": None, "excerpt": None, "severity": None}
    findings.append(verifier_result)
    print(f"  13-verifier: {json.dumps(verifier_result)[:140]}")

    print("step 4  aggregate to harness logger ...")
    aggregate = {"payload": base, "findings": findings}
    call("14-harness-logger", aggregate)

    statuses = [f.get("status") for f in findings if isinstance(f, dict)]
    print()
    print(f"verdicts collected: {len(findings)}")
    print(f"statuses: {statuses}")
    print(f"input_id for harness lookup: {input_id}")


if __name__ == "__main__":
    main()
