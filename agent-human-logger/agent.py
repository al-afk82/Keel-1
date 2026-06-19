import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.config import load_agent_config
from band.runtime.types import SessionConfig

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.usage import report_usage

AGENT_NAME = "human-logger"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are A1 — the human logger. Your only job is to log the human's input verbatim and assign it a unique ID.

You are the first agent in the pipeline. Every exchange starts here. The input_id you generate is the single identifier that all downstream agents — A2, A3, constraints, antipatterns, verifier, and the harness — must carry in their verdicts so every finding is traceable back to this exact exchange.

When you receive a message, treat it as the human input to log. Generate a unique input_id using a UUID4. Use band_send_message to return this exact JSON. No other text. No explanation.

{{
  "agent": "human-logger",
  "input_id": "a UUID4 you generate for this exchange",
  "status": "logged",
  "input": "the exact human message verbatim",
  "timestamp": "{timestamp}"
}}

Replace input with the exact message you received. Generate a fresh UUID4 for input_id. Use the timestamp exactly as written above. Nothing else."""


def make_graph(band_tools: list) -> object:
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        try:
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
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

    agent_id, api_key = load_agent_config("human_logger")

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

    logger.info("Human logger running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
