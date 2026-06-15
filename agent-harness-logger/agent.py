import asyncio
import logging
import os
import json
import requests
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.config import load_agent_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the harness logger. Your only job is to receive a compiled record of all agent verdicts and write it to the harness.

When you receive a message, it will contain the full verdict record for one conversation in JSON format. Parse it and use band_send_message to return this exact JSON after logging. No other text. No explanation.

{
  "agent": "harness-logger",
  "status": "logged",
  "entry_id": "the entry ID returned by the harness",
  "timestamp": "ISO 8601 timestamp"
}

Nothing else."""


def write_to_harness(data: dict) -> dict:
    harness_url = os.getenv("HARNESS_URL", "http://167.233.71.106:5000")
    harness_secret = os.getenv("HARNESS_SECRET", "drift-harness-2026")
    try:
        response = requests.post(
            f"{harness_url}/write",
            json={"data": data},
            headers={"x-secret": harness_secret},
            timeout=10,
        )
        return response.json()
    except Exception as e:
        logger.error("Harness write failed: %s", e)
        return {"entry_id": "error", "timestamp": ""}


def make_graph(band_tools: list) -> object:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        last_message = state["messages"][-1] if state["messages"] else None
        if last_message:
            try:
                content = last_message.content if hasattr(last_message, "content") else str(last_message)
                data = json.loads(content) if isinstance(content, str) else content
                write_to_harness(data)
            except Exception as e:
                logger.warning("Could not parse message for harness: %s", e)
                write_to_harness({"raw": str(last_message)})

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
    load_dotenv(override=True)

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
