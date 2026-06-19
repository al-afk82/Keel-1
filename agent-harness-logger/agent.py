import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.config import load_agent_config
from band.runtime.types import SessionConfig
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.usage import report_usage
from shared.mentions import strip_mentions

AGENT_NAME = "harness-logger"
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the harness logger. The Python layer has already classified and written the record to the harness before you run.

Return this exact JSON. No other text. No explanation.

{
  "agent": "harness-logger",
  "status": "logged"
}

Nothing else."""


# Agents do not emit one shared vocabulary. Map every "this is a problem" word
# onto confirmed, and every hedge onto uncertain, so the turn status does not
# silently undercount when an agent phrases a real finding its own way.
CONFIRMED_WORDS = {
    "violation", "drifted", "drift", "gap-found", "gap_found",
    "misaligned", "mismatch", "fail", "failed", "flagged", "flag",
}
UNCERTAIN_WORDS = {"uncertain", "unsure", "partial", "maybe", "ambiguous"}


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


def write_to_harness(data: dict) -> None:
    harness_url = os.getenv("HARNESS_URL", "http://167.233.71.106:5000")
    harness_secret = os.getenv("HARNESS_SECRET", "drift-harness-2026")
    try:
        requests.post(
            f"{harness_url}/write",
            json={"data": data},
            headers={"x-secret": harness_secret},
            timeout=10,
        )
        logger.info("Harness write complete.")
    except Exception as e:
        logger.error("Harness write failed: %s", e)


def make_graph(band_tools: list) -> object:
    llm = ChatOpenAI(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        last = state["messages"][-1] if state["messages"] else None
        if last:
            try:
                raw = last.content if hasattr(last, "content") else str(last)
                if isinstance(raw, str):
                    raw = strip_mentions(raw)
                    # The adapter wraps content as "[sender]: ... {json}". Extract
                    # the JSON object so the parse survives any leading label.
                    start = raw.find("{")
                    end = raw.rfind("}")
                    if start != -1 and end > start:
                        raw = raw[start:end + 1]
                incoming = json.loads(raw) if isinstance(raw, str) else raw

                # Only the aggregate message carries findings. The graph's second
                # pass sees the agent's own logged reply, which has none — skip it
                # so we do not write a spurious empty record per turn.
                if not isinstance(incoming, dict) or "findings" not in incoming:
                    logger.info("No findings in message, skipping harness write.")
                else:
                    findings = incoming.get("findings", [])
                    turn_status = derive_turn_status(findings)

                    confirmed = [
                        f for f in findings
                        if classify(f.get("status")) == "confirmed"
                    ]
                    uncertain = [
                        f for f in findings
                        if classify(f.get("status")) == "uncertain"
                    ]

                    record = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "turn_status": turn_status,
                        "payload": incoming.get("payload", {}),
                        "confirmed_findings": confirmed,
                        "uncertain_findings": uncertain,
                    }

                    write_to_harness(record)
                    logger.info(
                        "Logged turn — status: %s, confirmed: %d, uncertain: %d",
                        turn_status,
                        len(confirmed),
                        len(uncertain),
                    )
            except Exception as e:
                logger.warning("Could not parse incoming payload: %s", e)
                write_to_harness({"raw": str(last), "parse_error": str(e)})

        try:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
            response = llm_with_tools.invoke(messages)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                report_usage(AGENT_NAME, response.usage_metadata.get("input_tokens", 0), response.usage_metadata.get("output_tokens", 0))
            return {"messages": [response]}
        except Exception as e:
            logger.error("Anthropic call failed: %s", e)
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=json.dumps({"agent": AGENT_NAME, "status": "error", "error": str(e)}))]}

    def should_continue(state: MessagesState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(band_tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, ["tools", END])
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=InMemorySaver())


async def main():
    load_dotenv()

    agent_id, api_key = load_agent_config("harness_logger")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        session_config=SessionConfig(enable_context_hydration=False),
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Harness logger running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
