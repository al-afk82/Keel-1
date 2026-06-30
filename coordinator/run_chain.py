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
  python3 run_chain.py --json "<human input>" "<engine response>"

With --json the human readable trace is suppressed and a single JSON object is
printed to stdout: {input_id, turn_status, findings:[every agent]}. This is the
shape the website consumes to show one verdict with a per agent drill down.
"""

import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Vocabulary for rolling every agent's status up into one turn verdict. Mirrors
# the harness logger so the website verdict and the stored record never disagree.
CONFIRMED_WORDS = {
    "violation", "drifted", "drift", "gap-found", "gap_found",
    "misaligned", "mismatch", "fail", "failed", "flagged", "flag",
}
UNCERTAIN_WORDS = {"uncertain", "unsure", "partial", "maybe", "ambiguous"}

SKIPPED = []

# --json suppresses the human trace and emits one machine readable object.
# --stream emits one event line per agent the moment it returns, then a final
# done line, so the website can draw the pipeline live instead of all at once.
JSON_MODE = "--json" in sys.argv
STREAM_MODE = "--stream" in sys.argv
ARGS = [a for a in sys.argv[1:] if a not in ("--json", "--stream")]


def out(*a):
    if not JSON_MODE and not STREAM_MODE:
        print(*a)


def emit(event: str, data) -> None:
    # One JSON object per line, flushed immediately, so each agent surfaces on
    # the page the instant it resolves rather than waiting for the whole chain.
    if STREAM_MODE:
        print(json.dumps({"event": event, "data": data}), flush=True)


def classify(status) -> str:
    if not isinstance(status, str):
        return "clean"
    s = status.strip().lower()
    if s in CONFIRMED_WORDS:
        return "confirmed"
    if s in UNCERTAIN_WORDS:
        return "uncertain"
    return "clean"


def derive_turn_status(findings: list) -> str:
    classes = {classify(f.get("status")) for f in findings if isinstance(f, dict)}
    if "confirmed" in classes:
        return "confirmed"
    if "uncertain" in classes:
        return "uncertain"
    return "clean"


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
    # Fan out, returning as each agent resolves rather than in submit order, so
    # in stream mode the fastest agents surface first. emit() is a no-op unless
    # streaming, so this is safe for the plain and json paths too.
    out_map: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(routes))) as pool:
        futs = {pool.submit(call, rt, payload): rt for rt in routes}
        for fut in as_completed(futs):
            route, result = fut.result()
            out_map[route] = result
            emit("agent", result)
    return out_map


def main() -> None:
    human_input = ARGS[0] if len(ARGS) > 0 else (
        "Summarise the lease agreement in two sentences."
    )
    engine_response = ARGS[1] if len(ARGS) > 1 else (
        "Here is a haiku about autumn leaves drifting gently to the ground."
    )

    input_id = str(uuid.uuid4())
    base = {
        "input_id": input_id,
        "human_input": human_input,
        "engine_response": engine_response,
    }

    out(f"input_id: {input_id}")
    out(f"human_input: {human_input}")
    out(f"engine_response: {engine_response}")
    if SKIPPED:
        out(f"skipped (key not linked): {', '.join(SKIPPED)}")
    out()

    out("step 1  logging input ...")
    call("01-logger", base)

    out("step 2  profilers ...")
    profiles = fan(PROFILERS, base)
    for route, res in profiles.items():
        out(f"  {route}: {json.dumps(res)[:140]}")

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

    out("step 3  verdict agents ...")
    verdicts = fan(VERDICT_AGENTS, context)
    findings = []
    for route, res in verdicts.items():
        findings.append(res)
        out(f"  {route}: {json.dumps(res)[:140]}")

    out("step 3.5  verifier ...")
    non_clean = [
        f for f in findings
        if isinstance(f, dict) and f.get("status", "").lower().strip() in PROBLEM_STATUSES
    ]
    if non_clean:
        _, verifier_result = call("13-verifier", {"input_id": input_id, "findings": non_clean})
    else:
        verifier_result = {"agent": "verifier", "status": "clean", "rule": None, "excerpt": None, "severity": None}
    findings.append(verifier_result)
    emit("agent", verifier_result)
    out(f"  13-verifier: {json.dumps(verifier_result)[:140]}")

    out("step 4  aggregate to harness logger ...")
    aggregate = {"payload": base, "findings": findings}
    call("14-harness-logger", aggregate)

    statuses = [f.get("status") for f in findings if isinstance(f, dict)]
    out()
    out(f"verdicts collected: {len(findings)}")
    out(f"statuses: {statuses}")
    out(f"input_id for harness lookup: {input_id}")

    # Every agent recorded — profilers included — so the page can show the full
    # reasoning chain, not only the agents that flagged something.
    all_agents = [human_prof, engine_prof] + findings
    summary = {
        "input_id": input_id,
        "turn_status": derive_turn_status(findings),
        "findings": all_agents,
    }

    if JSON_MODE:
        print(json.dumps(summary))

    # Closes the live stream — the page reads this to settle the final verdict
    # once every agent row has filled in.
    emit("done", {"input_id": input_id, "turn_status": summary["turn_status"], "count": len(all_agents)})


if __name__ == "__main__":
    main()
