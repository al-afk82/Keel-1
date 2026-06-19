import asyncio
import json
import logging
import os
import sys
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

AGENT_NAME = "alignment-checker"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the alignment checker. Your only job is to compare the human's role and scope against the engine's role and scope and decide if they are aligned.

When you receive a message, it will contain both a human profile and an engine profile in JSON format.

Before concluding, reason through the evidence in this order. First read each profile and state to yourself what role and scope each describes in one sentence. Second compare role to role directly: do the two roles describe the same function and expertise level? Third compare scope to scope: does the human's intended outcome match the outcome the engine was optimising for? A difference in wording that describes the same functional intent is not misalignment. A difference in function, audience, or expertise level is. If both role and scope are consistent, return aligned. If either diverges materially, return misaligned with a specific description of where they diverge.

Use band_send_message to return this exact JSON. No other text. No explanation.

If aligned:
{
  "agent": "alignment-checker",
  "status": "aligned",
  "reason": null
}

If misaligned:
{
  "agent": "alignment-checker",
  "status": "misaligned",
  "reason": "specific description of where the roles or scopes diverge"
}

Aligned means the human's intended role and scope match the role and scope the engine assumed. If they match, return aligned. If they do not match, return misaligned with a specific reason describing the gap.

On the first message of a conversation, require strong evidence of misalignment before flagging. Ambiguity alone is not enough. Nothing else."""


def make_graph(band_tools: list) -> object:
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        try:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + clean_messages(state["messages"])
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

    agent_id, api_key = load_agent_config("alignment_checker")

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

    logger.info("Alignment checker running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
