"""Structured aggregation for specialist outputs."""

from __future__ import annotations

from src.fin_platform.state import AggregatedResponse, PlatformState


def aggregate_state(state: PlatformState) -> AggregatedResponse:
    warnings: list[str] = []
    specialist_outputs: dict[str, dict] = {}
    route_coverage = state.get("route_coverage", [])

    if state.get("analyst_output"):
        specialist_outputs["analyst"] = state["analyst_output"].model_dump()
    elif "analyst" in route_coverage:
        warnings.append("Analyst output unavailable.")
    if state.get("news_output"):
        specialist_outputs["news"] = state["news_output"].model_dump()
    elif "news" in route_coverage:
        warnings.append("News output unavailable.")
    if state.get("portfolio_output"):
        specialist_outputs["portfolio"] = state["portfolio_output"].model_dump()
    elif "portfolio" in route_coverage:
        warnings.append("Portfolio output unavailable.")

    for name, err in (state.get("specialist_errors") or {}).items():
        warnings.append(f"{name} failed: {err}")

    completed = len([r for r in route_coverage if r in specialist_outputs])
    completeness = round(completed / max(len(route_coverage), 1), 2)

    decision = state.get("supervisor_decision")
    executive = "Multi-agent synthesis completed."
    if decision and decision.ticker:
        executive = f"Financial intelligence synthesis for {decision.ticker} completed."

    metadata = {
        "request_id": state.get("request_id"),
        "thread_id": state.get("thread_id"),
        "route_coverage": route_coverage,
        "completeness": completeness,
        "supervisor_confidence": decision.confidence if decision else 0.0,
    }
    return AggregatedResponse(
        executive_summary=executive,
        specialist_outputs=specialist_outputs,
        warnings=warnings,
        metadata=metadata,
    )
