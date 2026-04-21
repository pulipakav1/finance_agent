"""LangGraph orchestration for multi-agent financial intelligence."""

from __future__ import annotations

import concurrent.futures
import time
import uuid
from typing import Any

from langgraph.graph import END, StateGraph
from tenacity import retry, stop_after_attempt, wait_fixed

from src.fin_platform.agents import AnalystAgent, NewsAgent, PortfolioAgent
from src.fin_platform.aggregation import aggregate_state
from src.fin_platform.config import settings
from src.fin_platform.memory import SessionMemoryManager
from src.fin_platform.observability import logger, metrics, timed
from src.fin_platform.providers import build_provider
from src.fin_platform.state import PlatformState
from src.fin_platform.supervisor import route_query


class FinancialIntelligenceGraph:
    def __init__(self) -> None:
        self.provider = build_provider()
        self.analyst_agent = AnalystAgent(self.provider)
        self.news_agent = NewsAgent(self.provider)
        self.portfolio_agent = PortfolioAgent(self.provider)
        self.memory = SessionMemoryManager()
        self.graph = self._build()

    def _build(self):
        graph = StateGraph(PlatformState)
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("specialists", self._specialists_node)
        graph.add_node("aggregator", self._aggregator_node)
        graph.set_entry_point("supervisor")
        graph.add_edge("supervisor", "specialists")
        graph.add_edge("specialists", "aggregator")
        graph.add_edge("aggregator", END)
        return graph.compile(checkpointer=self.memory.checkpointer)

    def _supervisor_node(self, state: PlatformState) -> PlatformState:
        with timed("supervisor_ms"):
            decision = route_query(state["query"])
            logger.info(
                "supervisor request_id=%s thread_id=%s routes=%s ticker=%s confidence=%.2f",
                state["request_id"],
                state["thread_id"],
                decision.routes,
                decision.ticker,
                decision.confidence,
            )
            metrics.incr("supervisor_calls")
            return {**state, "supervisor_decision": decision, "route_coverage": decision.routes}

    @retry(stop=stop_after_attempt(settings.retry_attempts), wait=wait_fixed(0.2), reraise=True)
    def _run_specialist(self, route: str, ticker: str) -> tuple[str, Any]:
        if route == "analyst":
            return route, self.analyst_agent.run(ticker)
        if route == "news":
            return route, self.news_agent.run(ticker)
        if route == "portfolio":
            return route, self.portfolio_agent.run()
        raise ValueError(f"Unknown route: {route}")

    def _specialists_node(self, state: PlatformState) -> PlatformState:
        decision = state["supervisor_decision"]
        errors = {}
        result_state: PlatformState = dict(state)
        ticker = (decision.ticker or "AAPL").upper()
        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(self._run_specialist, route, ticker): route
                for route in decision.routes
            }
            for future in concurrent.futures.as_completed(futures, timeout=settings.specialist_timeout_s + 1):
                route = futures[future]
                try:
                    _, result = future.result(timeout=settings.specialist_timeout_s)
                    result_state[f"{route}_output"] = result
                    metrics.incr(f"{route}_success")
                except Exception as exc:
                    errors[route] = str(exc)
                    metrics.incr(f"{route}_failure")
                    logger.warning("specialist_failed route=%s request_id=%s err=%s", route, state["request_id"], exc)

        result_state["specialist_errors"] = errors
        result_state["session_metadata"] = dict(result_state.get("session_metadata", {}))
        result_state["session_metadata"]["specialists_latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return result_state

    def _aggregator_node(self, state: PlatformState) -> PlatformState:
        with timed("aggregation_ms"):
            response = aggregate_state(state)
            return {**state, "response": response}

    def invoke(
        self,
        query: str,
        thread_id: str,
        session_metadata: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        history = conversation_history or []
        start = time.perf_counter()
        initial_state: PlatformState = {
            "query": query,
            "thread_id": thread_id,
            "request_id": request_id,
            "conversation_history": self.memory.trim_history(history),
            "session_metadata": self.memory.enrich_metadata(thread_id, session_metadata),
        }
        final_state = self.graph.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
        total_ms = round((time.perf_counter() - start) * 1000, 2)
        response = final_state["response"].model_dump()
        response["metadata"]["latency_ms"] = total_ms
        if settings.summarize_history:
            response["metadata"]["history_summary"] = self.memory.summarize_history(history)
        return response
