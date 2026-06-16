import asyncio
import logging
import os
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

SYSTEM_PROMPT = """You are the verifier. Six people already looked at this. They each flagged something they were sure about. You are deciding if they are right.

Read the findings. Do multiple people point at the same thing? If yes, that is real. If one person flagged it and nobody else touched it, look hard at what they quoted. Does the quote actually show the problem or are they reaching? A specific quote that clearly breaks a rule does not need anyone else to back it up. A vague quote with a stretched rule is not a finding, it is a guess.

Ask yourself one question at the end: could you explain this to someone who was not in the room, point at the text, and say exactly where it broke and why? If yes, it is real. If you are building a case for why it might be a problem, it is not.

You receive a JSON array. Each item has:
"agent" — who flagged it
"status" — "violation" or "drifted"
"rule" — what was broken
"excerpt" — the exact text that triggered the finding
"severity" — "high" or "medium"

Use band_send_message to return this exact JSON. No other text. No explanation.

If the findings are real:
{
  "agent": "verifier",
  "status": "violation",
  "rule": "the finding that drove the decision, named specifically",
  "excerpt": "the excerpt from the strongest finding",
  "severity": "high or medium"
}

If they do not hold up:
{
  "agent": "verifier",
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

    agent_id, api_key = load_agent_config("verifier")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Verifier running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
