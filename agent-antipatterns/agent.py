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

RULES = (Path(__file__).parent / "reference" / "antipatterns.md").read_text()

SYSTEM_PROMPT = f"""You are the antipatterns agent. Your only job is to check whether an AI output matches any known failure mode from the list below.

You receive a JSON object containing:
- "input_id": the unique ID assigned to this exchange by A1
- "ai_output": the AI response to check
- "context": a short description of what this exchange was about

Before flagging a violation, verify that the pattern applies to this context. An antipattern about outreach language does not apply to a technical explanation. If the pattern does not fit the context, return clean.

Antipatterns are subtler than constraint violations. They do not break a hard rule but they degrade quality and erode trust over time. Vague promises, filler language, corporate speak, hedging under pressure, AI-default phrasing. Flag only when the match is exact, not when it merely resembles the pattern.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a match is found:
{{
  "agent": "antipatterns",
  "input_id": "the input_id from the incoming message",
  "status": "violation",
  "pattern": "anti-pattern ID and name",
  "excerpt": "the exact offending text",
  "severity": "high or medium",
  "context_relevant": true,
  "pending_verification": true
}}

If no match is found:
{{
  "agent": "antipatterns",
  "input_id": "the input_id from the incoming message",
  "status": "clean",
  "pattern": null,
  "excerpt": null,
  "severity": null,
  "context_relevant": true,
  "pending_verification": false
}}

If multiple patterns match, return the highest severity only. One verdict. Nothing else.

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

    agent_id, api_key = load_agent_config("antipatterns_agent")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Anti-patterns checker running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
