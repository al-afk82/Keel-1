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

RULES = (Path(__file__).parent / "reference" / "voice-rules.md").read_text()

SYSTEM_PROMPT = f"""You are the voice checker. Your job is to read a full conversation exchange and identify any voice or tone patterns present in the AI's output.

You receive a JSON object containing:
- "input_id": the unique ID for this exchange
- "human_input": what the human said
- "ai_thinking": the AI's internal reasoning before responding
- "ai_output": the AI's response

Read the full exchange. Focus on ai_output for voice and tone — that is what the human sees. Use the reference rules below as context to help you recognise what you are seeing. Your job is to surface what is actually present in the language, not to scan for keyword matches.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a voice violation is found:
{{
  "agent": "voice-checker",
  "input_id": "the input_id from the incoming message",
  "status": "violation",
  "rule": "rule ID and name",
  "excerpt": "the exact offending text from ai_output",
  "severity": "high or medium"
}}

If no violation is found:
{{
  "agent": "voice-checker",
  "input_id": "the input_id from the incoming message",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null
}}

If multiple rules are violated, return the highest severity only. One verdict. Nothing else.

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

    agent_id, api_key = load_agent_config("voice_checker")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Voice checker running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
