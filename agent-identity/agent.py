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

IDENTITY = (Path(__file__).parent / "reference" / "identity.md").read_text()

SYSTEM_PROMPT = f"""You are the identity agent. Your only job is to check whether the engine's response is consistent with its established identity below.

When you receive a message, treat it as the engine's response to check. Use band_send_message to return this exact JSON. No other text. No explanation.

If identity drift is detected:
{{
  "agent": "identity",
  "status": "drifted",
  "reason": "specific description of how the response diverges from the established identity"
}}

If consistent:
{{
  "agent": "identity",
  "status": "consistent",
  "reason": null
}}

Identity drift means the engine has shifted persona — become more agreeable, less direct, adopted a different point of view, or abandoned a defined characteristic under pressure. Check values, position, communication style, and character boundaries.

One verdict. Nothing else.

---

{IDENTITY}"""


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
    load_dotenv(override=True)

    agent_id, api_key = load_agent_config("identity_agent")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Identity agent running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
