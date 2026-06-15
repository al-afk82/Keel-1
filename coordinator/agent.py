import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from band import Agent
from band.config import load_agent_config
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage
from band.core.protocols import AgentToolsProtocol
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DIR = Path(__file__).parent
CATCH_LOG_PATH = _DIR / "catch-log-entries.jsonl"

VOICE_RULES = (_DIR.parent / "agent-voice-checker" / "reference" / "voice-rules.md").read_text()
QUALITY_CRITERIA = (_DIR.parent / "agent-quality-checker" / "reference" / "quality-criteria.md").read_text()
CONSTRAINTS = (_DIR.parent / "agent-constraints" / "reference" / "constraints.md").read_text()
ANTIPATTERNS = (_DIR.parent / "agent-antipatterns" / "reference" / "antipatterns.md").read_text()

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


async def _call(system: str, user: str) -> dict:
    response = await get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        raise ValueError(f"Could not parse verdict JSON: {raw[:200]}")


async def check_voice(ai_output: str) -> dict:
    system = f"""You are the voice checker. Check whether the AI output violates any of the voice rules below.

Return ONLY this JSON — no other text, no explanation:

If a violation is found:
{{"agent": "voice-checker", "status": "violation", "rule": "rule ID and name", "excerpt": "the exact offending text", "severity": "high or medium"}}

If no violation:
{{"agent": "voice-checker", "status": "clean", "rule": null, "excerpt": null, "severity": null}}

If multiple violations, return highest severity only.

---

{VOICE_RULES}"""
    try:
        return await _call(system, ai_output)
    except Exception as e:
        logger.warning("voice check failed: %s", e)
        return {"agent": "voice-checker", "status": "clean", "rule": None, "excerpt": None, "severity": None}


async def check_quality(ai_output: str) -> dict:
    system = f"""You are the quality checker. Check whether the AI output meets the quality criteria below.

Return ONLY this JSON — no other text, no explanation:

If a quality failure is found:
{{"agent": "quality-checker", "status": "violation", "rule": "criteria ID and name", "excerpt": "the exact failing text or what is missing", "severity": "high or medium"}}

If quality is acceptable:
{{"agent": "quality-checker", "status": "clean", "rule": null, "excerpt": null, "severity": null}}

If multiple failures, return highest severity only.

---

{QUALITY_CRITERIA}"""
    try:
        return await _call(system, ai_output)
    except Exception as e:
        logger.warning("quality check failed: %s", e)
        return {"agent": "quality-checker", "status": "clean", "rule": None, "excerpt": None, "severity": None}


async def check_constraints(ai_output: str) -> dict:
    system = f"""You are the constraints agent. Check whether the AI output violates any of the hard rules below.

Return ONLY this JSON — no other text, no explanation:

If a violation is found:
{{"agent": "constraints", "status": "violation", "rule": "rule ID and name", "excerpt": "the exact offending text", "severity": "high or medium"}}

If no violation:
{{"agent": "constraints", "status": "clean", "rule": null, "excerpt": null, "severity": null}}

If multiple violations, return highest severity only.

---

{CONSTRAINTS}"""
    try:
        return await _call(system, ai_output)
    except Exception as e:
        logger.warning("constraints check failed: %s", e)
        return {"agent": "constraints", "status": "clean", "rule": None, "excerpt": None, "severity": None}


async def check_antipatterns(ai_output: str) -> dict:
    system = f"""You are the antipatterns agent. Check whether the AI output matches any known failure pattern below.

Return ONLY this JSON — no other text, no explanation:

If a match is found:
{{"agent": "antipatterns", "status": "violation", "pattern": "pattern ID and name", "excerpt": "the exact offending text", "severity": "high or medium"}}

If no match:
{{"agent": "antipatterns", "status": "clean", "pattern": null, "excerpt": null, "severity": null}}

If multiple matches, return highest severity only.

---

{ANTIPATTERNS}"""
    try:
        return await _call(system, ai_output)
    except Exception as e:
        logger.warning("antipatterns check failed: %s", e)
        return {"agent": "antipatterns", "status": "clean", "pattern": None, "excerpt": None, "severity": None}


async def correct_output(original: str, violations: list[dict]) -> str:
    violation_summary = "\n".join(
        f"- [{v.get('agent')}] {v.get('rule') or v.get('pattern')}: \"{v.get('excerpt')}\""
        for v in violations
    )
    system = """You are the corrector. Rewrite the AI output to fix the violations listed. Keep the meaning and length similar. Return ONLY the corrected text — no explanation, no preamble."""
    user = f"""Original output:
{original}

Violations to fix:
{violation_summary}

Corrected output:"""
    try:
        response = await get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning("correction failed: %s", e)
        return original


def write_catch_log(entry: dict) -> None:
    with open(CATCH_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


class CoordinatorAdapter(SimpleAdapter):
    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
        history,
        participants_msg,
        contacts_msg,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        ai_output = msg.content.strip()

        if not ai_output:
            return

        logger.info("Coordinator received output to check (%d chars)", len(ai_output))

        results = await asyncio.gather(
            check_voice(ai_output),
            check_quality(ai_output),
            check_constraints(ai_output),
            check_antipatterns(ai_output),
            return_exceptions=True,
        )

        verdicts = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning("A check raised an exception: %s", r)
                verdicts.append({"status": "clean", "severity": None})
            else:
                verdicts.append(r)

        high_violations = [v for v in verdicts if v.get("severity") == "high"]

        if high_violations:
            delivered = await correct_output(ai_output, high_violations)
            was_corrected = True
        else:
            delivered = ai_output
            was_corrected = False

        log_id = str(uuid.uuid4())[:8]
        entry = {
            "log_id": log_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original": ai_output,
            "delivered": delivered,
            "corrected": was_corrected,
            "verdicts": verdicts,
            "user_response": None,
        }
        write_catch_log(entry)

        result_payload = {
            "output": delivered,
            "corrected": was_corrected,
            "verdicts": verdicts,
            "log_id": log_id,
        }

        sender = msg.sender_name or msg.sender_id
        await tools.send_message(
            json.dumps(result_payload, ensure_ascii=False),
            mentions=[sender],
        )

        logger.info(
            "Coordinator done — log_id=%s corrected=%s violations=%d",
            log_id,
            was_corrected,
            len(high_violations),
        )


async def main():
    load_dotenv(override=True)

    agent_id, api_key = load_agent_config("coordinator")

    adapter = CoordinatorAdapter()

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Coordinator running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
