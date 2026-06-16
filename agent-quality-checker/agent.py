import asyncio
import logging
import os
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RULES = (Path(__file__).parent / "reference" / "quality-criteria.md").read_text()

SYSTEM_PROMPT = f"""You are the quality checker. Your job is to find coverage failures — elements of the human's defined scope that the engine's verbatim hidden reasoning did not address.

You receive a JSON payload with these fields:
"tracking_id" — unique identifier for this exchange
"human_msg" — what the human said, verbatim
"thinking_chain" — the AI engine's verbatim internal dialog, its raw reasoning captured exactly as it unfolded before any response was produced
"human_scope" — the scope the human defined, extracted by the profiler
"engine_scope" — the scope the engine assumed, extracted by the profiler

Before concluding, reason through the evidence in this order. First read "human_scope" to establish what was in bounds for this exchange. Second read "human_msg" and extract each specific thing the human asked for — build a checklist. Third read "thinking_chain" and check each item: is it present, absent, or unclear? You are not evaluating the quality of coverage, only whether it happened at all. One clearly absent item is a finding. An unclear item is uncertain. Full coverage is clean. Use the reference criteria below as the authority on what each quality failure looks like.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a failure is found:
{{
  "agent": "quality-checker",
  "status": "violation",
  "rule": "the scope item that was asked for but not addressed",
  "excerpt": "the point in thinking_chain where the gap is most visible, or a description of what is missing",
  "severity": "high or medium"
}}

If the evidence is ambiguous:
{{
  "agent": "quality-checker",
  "status": "uncertain",
  "rule": "the item that may not have been covered",
  "excerpt": "the text that raised the question",
  "severity": null
}}

If coverage is complete:
{{
  "agent": "quality-checker",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null
}}

One verdict. Nothing else.

---

{RULES}"""


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

    agent_id, api_key = load_agent_config("quality_checker")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Quality checker running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
