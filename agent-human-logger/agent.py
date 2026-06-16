import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
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

SYSTEM_PROMPT_TEMPLATE = """You are A1 — the human logger. Your only job is to structure the human's input into the log record below.

You are the first agent in the pipeline. Every exchange starts here. The input_id and timestamp are already assigned — do not change them. Use band_send_message to return this exact JSON. No other text. No explanation.

{{
  "agent": "human-logger",
  "input_id": "{input_id}",
  "status": "logged",
  "input": "the exact human message verbatim",
  "timestamp": "{timestamp}"
}}

Replace input with the exact message you received. Use the input_id and timestamp exactly as written above. Nothing else."""


def make_graph(band_tools: list) -> object:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            input_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
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

    agent_id, api_key = load_agent_config("human_logger")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Human logger running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
