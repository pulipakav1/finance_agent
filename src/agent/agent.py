from typing import TypedDict

import anthropic
from langgraph.graph import END, StateGraph
from loguru import logger

from config.settings import settings
from src.tools import TOOL_DEFINITIONS, execute_tool


class AgentState(TypedDict, total=False):
    messages: list
    tool_calls: list
    iterations: int
    final_answer: str
    is_done: bool
    max_iter_cap: int


SYSTEM_PROMPT = """You are a compact finance chatbot. Tools: get_stock_price, compare tickers, financial statements, web search, read URL, Python, save report.

Hard rules for prices and quotes:
- Questions like "price", "trading at", "quote", "how much is [TICKER]", or any current stock value → call get_stock_price with that ticker. Do this FIRST. Do NOT use search_web or scrape_url to find a live price—those are for news and articles, not quotes.
- If get_stock_price returns an error, say what failed and suggest checking the ticker symbol; do not pretend you "can't access markets" unless the tool actually errored.

Speed:
- One tool is often enough for a simple price check.
- Add financials or news only if the user asked for fundamentals or recent events.
- Keep answers short: lead with the numbers from tools.

Never invent prices. Use tools."""


class FinanceAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.model_name
        self.default_max_iter = settings.max_iterations
        self.graph = self._build_graph()
        logger.info("Finance agent ready")

    def _messages_create(self, **kwargs):
        """anthropic>=0.40: tools on messages.create; older SDKs use beta.tools.messages."""
        try:
            return self.client.messages.create(**kwargs)
        except TypeError as e:
            if "tools" in str(e) and "unexpected keyword" in str(e):
                return self.client.beta.tools.messages.create(**kwargs)
            raise

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("agent", self._agent_node)
        g.add_node("tools", self._tool_node)
        g.set_entry_point("agent")
        g.add_conditional_edges(
            "agent",
            self._should_continue,
            {"tools": "tools", "end": END},
        )
        g.add_edge("tools", "agent")
        return g.compile()

    def _agent_node(self, state: AgentState) -> AgentState:
        n = state.get("iterations", 0)
        cap = state.get("max_iter_cap", self.default_max_iter)
        if n >= cap:
            logger.warning("Hit max_iter_cap={}", cap)
            return {
                **state,
                "is_done": True,
                "final_answer": "Stopped after the iteration limit.",
            }

        messages = state.get("messages", [])
        logger.info("Agent step {}", n + 1)

        response = self._messages_create(
            model=self.model,
            max_tokens=settings.max_tokens,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        logger.info("stop_reason={}", response.stop_reason)

        assistant_content = []
        tool_calls_made = []
        final_answer = ""

        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
                final_answer = block.text
            elif block.type == "tool_use":
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
                tool_calls_made.append(
                    {"id": block.id, "name": block.name, "input": block.input}
                )
                logger.info("tool {} {}", block.name, list(block.input.keys()))

        updated = messages + [{"role": "assistant", "content": assistant_content}]

        return {
            **state,
            "messages": updated,
            "tool_calls": state.get("tool_calls", []) + tool_calls_made,
            "iterations": n + 1,
            "final_answer": final_answer,
            "is_done": response.stop_reason == "end_turn",
        }

    def _tool_node(self, state: AgentState) -> AgentState:
        messages = state.get("messages", [])
        last = messages[-1]
        results = []
        for block in last.get("content", []):
            if block.get("type") == "tool_use":
                logger.info("run {}", block["name"])
                out = execute_tool(block["name"], block["input"])
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": out,
                    }
                )
        return {**state, "messages": messages + [{"role": "user", "content": results}]}

    def _should_continue(self, state: AgentState) -> str:
        if state.get("is_done"):
            return "end"
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last = messages[-1]
        if last.get("role") != "assistant":
            return "end"
        for block in last.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                return "tools"
        return "end"

    def run(self, query: str, depth: str = "quick") -> dict:
        cap = (
            settings.max_iterations_deep
            if depth == "deep"
            else settings.max_iterations
        )
        logger.info("Query depth={} cap={}: {}", depth, cap, query[:120])
        initial: AgentState = {
            "messages": [{"role": "user", "content": query}],
            "tool_calls": [],
            "iterations": 0,
            "final_answer": "",
            "is_done": False,
            "max_iter_cap": cap,
        }
        final_state = self.graph.invoke(initial)
        calls = final_state["tool_calls"]
        return {
            "answer": final_state["final_answer"],
            "tool_calls": calls,
            "iterations": final_state["iterations"],
            "tools_used": list({t["name"] for t in calls}),
            "depth": depth,
        }
