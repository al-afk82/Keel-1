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
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.usage import report_usage

AGENT_NAME = "harness-logger"
from langchain_anthropic import ChatAnthropic
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


def derive_turn_status(findings: list) -> str:
    statuses = {f.get("status") for f in findings if isinstance(f, dict)}
    confirmed = {"violation", "drifted", "gap-found"}
    if statuses & confirmed:
        return "confirmed"
    if "uncertain" in statuses:
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
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        last = state["messages"][-1] if state["messages"] else None
        if last:
            try:
                raw = last.content if hasattr(last, "content") else str(last)
                incoming = json.loads(raw) if isinstance(raw, str) else raw

                findings = incoming.get("findings", [])
                turn_status = derive_turn_status(findings)

                confirmed = [
                    f for f in findings
                    if f.get("status") in {"violation", "drifted", "gap-found"}
                ]
                uncertain = [
                    f for f in findings
                    if f.get("status") == "uncertain"
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

        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            report_usage(AGENT_NAME, response.usage_metadata.get("input_tokens", 0), response.usage_metadata.get("output_tokens", 0))
        return {"messages": [response]}

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
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Harness logger running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
