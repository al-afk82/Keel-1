import asyncio
import logging
import os
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

SYSTEM_PROMPT = """You are the thinking logger. Your only job is to log the engine's internal thinking verbatim and return a confirmation.

When you receive a message, treat it as the engine's thinking to log. Use band_send_message to return this exact JSON. No other text. No explanation.

{
  "agent": "thinking-logger",
  "input_id": "the input_id from the incoming message",
  "status": "logged",
  "thinking": "the engine thinking verbatim",
  "timestamp": "ISO 8601 timestamp"
}

Replace the thinking field with the exact content you received. Replace the timestamp with the current UTC time in ISO 8601 format. Nothing else."""


def make_graph(band_tools: list) -> object:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
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

    agent_id, api_key = load_agent_config("thinking_logger")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Thinking logger running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
