import os
import requests

INPUT_COST_PER_TOKEN = 3 / 1_000_000
OUTPUT_COST_PER_TOKEN = 15 / 1_000_000


def report_usage(agent_name: str, input_tokens: int, output_tokens: int) -> None:
    harness_url = os.getenv("HARNESS_URL", "http://167.233.71.106:5000")
    harness_secret = os.getenv("HARNESS_SECRET", "drift-harness-2026")
    estimated_cost = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)
    try:
        requests.post(
            f"{harness_url}/write_usage",
            json={
                "agent_name": agent_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": estimated_cost,
            },
            headers={"x-secret": harness_secret},
            timeout=5,
        )
    except Exception:
        pass
