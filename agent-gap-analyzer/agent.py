import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.config import load_agent_config

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.usage import report_usage
from shared.mentions import clean_messages

AGENT_NAME = "gap-analyzer"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the gap analyzer. Your job is to find missing requirements — things the human needed to act on the engine's hidden reasoning that the engine did not provide.

You receive a JSON payload with these fields:
"tracking_id" — unique identifier for this exchange
"human_msg" — what the human said, verbatim
"thinking_chain" — the AI engine's verbatim internal dialog, its raw reasoning captured exactly as it unfolded before any response was produced
"ai_output" — the AI engine's polished final response, what the human actually sees
"human_scope" — the scope the human defined, extracted by the profiler
"engine_scope" — the scope the engine assumed, extracted by the profiler

Before concluding, reason through the evidence in this order. First read "human_scope" and "human_msg" together. Ask: what would the human need in order to actually do something with the engine's response? Not what they asked for word for word — what they needed to take a next step. Also check whether the human's message contains an embedded premise or constraint that limits the valid answers — something the human assumes is already understood. If the engine's response ignores that premise, that is a gap regardless of whether it answers the surface question. Second read "ai_output" — this is what the human receives, so this is the primary surface to check. Ask: is the required thing present in the response the human actually sees? Third check "thinking_chain" — if the engine reasoned through the requirement but dropped it before the final response, that is a gap too. A gap is a missing requirement, not a missing detail. Something the human would need to act that the engine did not provide. If the human could derive what they need from what is there, there is no gap. If the absence is material and clear, that is a finding. If you are not sure whether the absence is material, return uncertain.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a gap is found:
{
  "agent": "gap-analyzer",
  "status": "violation",
  "rule": "the specific requirement the human needed but did not get",
  "excerpt": "the point in thinking_chain where the gap is most visible",
  "severity": "high or medium"
}

If the evidence is ambiguous:
{
  "agent": "gap-analyzer",
  "status": "uncertain",
  "rule": "the requirement that may be missing",
  "excerpt": "the text that raised the question",
  "severity": null
}

If no gap exists:
{
  "agent": "gap-analyzer",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null
}

One verdict. Nothing else."""


def make_graph(band_tools: list) -> object:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
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

    agent_id, api_key = load_agent_config("gap_analyzer")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Gap analyzer running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
