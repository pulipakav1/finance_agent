"""Shared typed state and contracts for graph orchestration."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

RouteName = Literal["analyst", "news", "portfolio"]


class SupervisorDecision(BaseModel):
    routes: list[RouteName] = Field(default_factory=list)
    ticker: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    fallback_reason: str | None = None


class AnalystOutput(BaseModel):
    ticker: str | None = None
    technical_trend: str
    price_movement_summary: str
    indicator_explanation: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class NewsEvent(BaseModel):
    headline: str
    sentiment: Literal["positive", "neutral", "negative"]
    event_type: str


class NewsOutput(BaseModel):
    ticker: str | None = None
    headlines: list[str]
    sentiment_summary: str
    extracted_events: list[NewsEvent]
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class PortfolioOutput(BaseModel):
    composition_summary: str
    concentration_checks: list[str]
    position_summaries: list[str]
    risk_breakdown: str
    allocation_breakdown: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AggregatedResponse(BaseModel):
    executive_summary: str
    specialist_outputs: dict[str, dict[str, Any]]
    warnings: list[str]
    metadata: dict[str, Any]


class PlatformState(TypedDict, total=False):
    query: str
    thread_id: str
    request_id: str
    conversation_history: list[dict[str, str]]
    session_metadata: dict[str, Any]

    supervisor_decision: SupervisorDecision
    analyst_output: AnalystOutput
    news_output: NewsOutput
    portfolio_output: PortfolioOutput
    specialist_errors: dict[str, str]
    route_coverage: list[str]

    response: AggregatedResponse
