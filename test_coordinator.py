import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from coordinator.agent import (
    check_voice,
    check_quality,
    check_constraints,
    check_antipatterns,
    correct_output,
)

SAMPLE_OUTPUT = """Sure, happy to help with that! As an AI language model, I want to make sure
I provide you with the most seamless and robust solution to leverage your existing workflows.
Let me know if you need anything else!"""

async def run():
    print(f"Testing output:\n{SAMPLE_OUTPUT}\n")
    print("Running 4 checks in parallel...\n")

    results = await asyncio.gather(
        check_voice(SAMPLE_OUTPUT),
        check_quality(SAMPLE_OUTPUT),
        check_constraints(SAMPLE_OUTPUT),
        check_antipatterns(SAMPLE_OUTPUT),
    )

    labels = ["voice", "quality", "constraints", "antipatterns"]
    high_violations = []

    for label, verdict in zip(labels, results):
        status = verdict.get("status", "unknown")
        severity = verdict.get("severity")
        rule = verdict.get("rule") or verdict.get("pattern")
        excerpt = verdict.get("excerpt")
        print(f"[{label}] status={status} severity={severity}")
        if rule:
            print(f"  rule: {rule}")
        if excerpt:
            print(f"  excerpt: {excerpt!r}")
        print()
        if severity == "high":
            high_violations.append(verdict)

    if high_violations:
        print(f"{len(high_violations)} high severity violation(s) found. Running corrector...\n")
        corrected = await correct_output(SAMPLE_OUTPUT, high_violations)
        print(f"Corrected output:\n{corrected}\n")
    else:
        print("No high severity violations. Output passes through unchanged.")

if __name__ == "__main__":
    asyncio.run(run())
