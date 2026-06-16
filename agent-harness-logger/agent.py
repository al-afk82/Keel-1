import asyncio
import json
import logging
import os

import requests
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.config import load_agent_config
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the harness logger. You receive a record and it has already been written to the harness by the Python layer before you run.

Return this exact JSON. No other text. No explanation.

{
  "agent": "harness-logger",
  "status": "logged"
}

Nothing else."""


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
                record = json.loads(raw) if isinstance(raw, str) else raw
                write_to_harness(record)
            except Exception as e:
                logger.warning("Could not parse incoming payload: %s", e)
                write_to_harness({"raw": str(last), "parse_error": str(e)})

        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
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
