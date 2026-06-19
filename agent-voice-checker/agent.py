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
from band.runtime.types import SessionConfig

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.usage import report_usage
from shared.mentions import clean_messages

AGENT_NAME = "voice-checker"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RULES = (Path(__file__).parent / "reference" / "voice-rules.md").read_text()

SYSTEM_PROMPT = f"""You are the voice checker. Your job is to find register mismatches between how the human communicated and how the engine reasoned in its verbatim hidden dialog.

You receive a JSON payload with these fields:
"tracking_id" — unique identifier for this exchange
"human_msg" — what the human said, verbatim
"thinking_chain" — the AI engine's verbatim internal dialog, its raw reasoning captured exactly as it unfolded before any response was produced
"ai_output" — the AI engine's polished final response, what the human actually sees
"human_scope" — the scope the human defined, extracted by the profiler
"engine_scope" — the scope the engine assumed, extracted by the profiler

Before concluding, reason through the evidence in this order. First read "human_scope" to calibrate what register is appropriate for this type of exchange. Second read "human_msg" and score the human's register on three dimensions: formality (casual to formal), directness (blunt to diplomatic), density (sparse to detailed). Third read "ai_output" — this is what the human sees, so this is the primary register to compare against the human's. Also check "thinking_chain" to see if the register in the reasoning matches the register in the output. Fourth compare. A finding requires a visible gap on at least one dimension large enough that a reader switching from the human's message to the engine's response would notice the shift. Marginal variation across all three dimensions is not a finding. One large gap on one dimension is. Use the reference rules below as the authority on what each voice violation looks like.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a violation is found:
{{
  "agent": "voice-checker",
  "status": "violation",
  "rule": "the dimension where the gap is largest: formality, directness, or density",
  "excerpt": "the exact text from thinking_chain that shows the mismatch",
  "severity": "high or medium"
}}

If the evidence is ambiguous:
{{
  "agent": "voice-checker",
  "status": "uncertain",
  "rule": "the dimension that may have a gap",
  "excerpt": "the text that raised the question",
  "severity": null
}}

If no violation is found:
{{
  "agent": "voice-checker",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null
}}

One verdict. Nothing else.

---

{RULES}"""


def make_graph(band_tools: list) -> object:
    send_tools = [t for t in band_tools if getattr(t, "name", None) == "band_send_message"]
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(send_tools, tool_choice={"type": "tool", "name": "band_send_message"})

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
    graph.add_edge("tools", END)

    return graph.compile(checkpointer=InMemorySaver())


async def main():
    load_dotenv()

    agent_id, api_key = load_agent_config("voice_checker")

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

    logger.info("Voice checker running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
