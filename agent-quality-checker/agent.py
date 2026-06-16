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

SYSTEM_PROMPT = f"""You are the quality checker. Your job is to read a full conversation exchange and assess whether the AI's output is genuinely useful relative to what the human asked.

You receive a JSON object containing:
- "input_id": the unique ID for this exchange
- "human_input": what the human said
- "ai_thinking": the AI's internal reasoning before responding
- "ai_output": the AI's response

Read the full exchange. The human_input tells you what was needed. The ai_output tells you what was delivered. Use the reference criteria below as context to help you assess what you are seeing. Quality failures are often about what is absent — what the human needed that the output did not provide.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a quality failure is found:
{{
  "agent": "quality-checker",
  "input_id": "the input_id from the incoming message",
  "status": "violation",
  "rule": "criteria ID and name",
  "excerpt": "the exact failing text or a description of what is missing from ai_output",
  "severity": "high, medium, or low — use the severity defined for that criterion in the reference"
}}

If quality is acceptable:
{{
  "agent": "quality-checker",
  "input_id": "the input_id from the incoming message",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null
}}

If multiple criteria fail, return the highest severity only. One verdict. Nothing else.

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
