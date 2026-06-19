import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
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
from shared.mentions import clean_messages

AGENT_NAME = "logger"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are the input logger. Your job is to log the human's message and the engine's thinking chain verbatim, and assign this exchange a unique ID.

You are the first agent in the pipeline. The input_id you generate is the single identifier all downstream agents must carry in their verdicts so every finding is traceable back to this exchange.

When you receive a message it will be a JSON object with tracking_id, human_msg, and thinking_chain. Use band_send_message to return this exact JSON. No other text. No explanation.

{{
  "agent": "logger",
  "input_id": "a UUID4 you generate for this exchange",
  "status": "logged",
  "human_input": "the exact human_msg verbatim",
  "thinking": "the exact thinking_chain verbatim",
  "timestamp": "{timestamp}"
}}

Generate a fresh UUID4 for input_id. Use the timestamp exactly as written above. Nothing else."""


def make_graph(band_tools: list) -> object:
    llm = ChatOpenAI(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools, tool_choice="required")

    def call_model(state: MessagesState) -> dict:
        try:
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            messages = [SystemMessage(content=system_prompt)] + clean_messages(state["messages"])
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
    graph.add_edge("tools", END)

    return graph.compile(checkpointer=InMemorySaver())


async def main():
    load_dotenv()

    agent_id, api_key = load_agent_config("logger")

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

    logger.info("Input logger running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
