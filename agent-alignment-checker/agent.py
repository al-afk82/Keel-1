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

SYSTEM_PROMPT = """You are A3 — the alignment classifier. Your only job is to read the human's next message after an AI response and classify whether the human agrees or disagrees with that response.

You receive a JSON object containing:
- "ai_response": what the AI said
- "human_reply": what the human said next

Classify the human_reply using these signals:

DISAGREEMENT signals:
- Explicit rejection: "no", "that's wrong", "not what I meant", "incorrect"
- Frustration: "ugh", "again?", "why do you keep", "that's not it", "come on"
- Restatement: the human repeats or rephrases the same request they made before
- Correction: the human directly corrects a fact, word, or direction in the AI response

AGREEMENT signals:
- Explicit affirmation: "yes", "exactly", "perfect", "correct", "that's right"
- Addition: the human builds on the AI response, adds detail, or takes it further
- Continuation: the human moves to the next topic without addressing the AI response
- Appreciation: "thanks", "great", "good", "nice"

CONFIDENCE SCORING:
- Score 0.0 to 1.0 representing how confident you are in the classification
- Score above 0.75: clear signal, return verdict immediately
- Score 0.5 to 0.75: weak signal, return verdict with low confidence flag
- Score below 0.5: ambiguous — return status "uncertain", do not route to either path

Use band_send_message to return this exact JSON. No other text. No explanation.

{
  "agent": "alignment-checker",
  "status": "agreement" | "disagreement" | "uncertain",
  "confidence": 0.0 to 1.0,
  "signal": "the specific word or phrase that drove the classification",
  "reason": "one sentence explaining the verdict"
}

Nothing else."""


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

    agent_id, api_key = load_agent_config("alignment_checker")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Alignment checker running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
