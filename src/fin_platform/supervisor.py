"""Supervisor node that routes user requests to specialist agents."""

from __future__ import annotations

import re

from pydantic import ValidationError

from src.fin_platform.state import SupervisorDecision

TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")

_STOPWORDS = {
    "I", "A", "AN", "THE", "IS", "ARE", "WAS", "WERE", "BE", "BEEN",
    "HAS", "HAVE", "HAD", "DO", "DID", "DOES", "WILL", "CAN", "COULD",
    "SHOULD", "WOULD", "MAY", "MIGHT", "SHALL", "NOT", "AND", "OR",
    "BUT", "IF", "IN", "ON", "AT", "TO", "OF", "FOR", "BY", "WITH",
    "FROM", "UP", "MY", "YOUR", "HIS", "HER", "ITS", "OUR", "US",
    "IT", "ME", "YOU", "HE", "SHE", "WE", "THEY", "THEM", "WHAT",
    "WHO", "HOW", "WHY", "WHEN", "WHERE", "WHICH", "ALL", "ETF", "CEO",
    "IPO", "GDP", "SEC", "FED", "AI", "EPS",
}


def _extract_ticker(query: str) -> str | None:
    matches = [m for m in TICKER_RE.findall(query) if m not in _STOPWORDS]
    return matches[0] if matches else None


def route_query(query: str) -> SupervisorDecision:
    lower = query.lower()
    routes: list[str] = []
    ticker = _extract_ticker(query)

    if any(k in lower for k in ["price", "trend", "technical", "valuation", "stock"]):
        routes.append("analyst")
    if any(k in lower for k in ["news", "headline", "event", "sentiment"]):
        routes.append("news")
    if any(k in lower for k in ["portfolio", "allocation", "position", "risk", "holdings"]):
        routes.append("portfolio")

    if not routes:
        routes = ["analyst"]
        fallback_reason = "No explicit route keywords found; defaulting to analyst."
        confidence = 0.45
    else:
        fallback_reason = None
        confidence = 0.8 if len(routes) == 1 else 0.68

    raw = {
        "routes": routes,
        "ticker": ticker or "AAPL",
        "confidence": confidence,
        "fallback_reason": fallback_reason,
    }

    try:
        return SupervisorDecision.model_validate(raw)
    except ValidationError:
        return SupervisorDecision(
            routes=["analyst"],
            ticker="AAPL",
            confidence=0.3,
            fallback_reason="Invalid structured supervisor output; fallback engaged.",
        )
