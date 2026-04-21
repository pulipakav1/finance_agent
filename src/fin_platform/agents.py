"""Specialist agent contracts and implementations."""

from __future__ import annotations

from dataclasses import dataclass

from src.fin_platform.providers import DataProvider
from src.fin_platform.state import AnalystOutput, NewsEvent, NewsOutput, PortfolioOutput


@dataclass
class AnalystAgent:
    provider: DataProvider

    def run(self, ticker: str) -> AnalystOutput:
        snap = self.provider.get_market_snapshot(ticker)
        trend = "bullish" if snap.sma_20 > snap.sma_50 else "mixed-to-bearish"
        return AnalystOutput(
            ticker=snap.ticker,
            technical_trend=f"{snap.ticker} trend is {trend} with SMA20 {snap.sma_20:.2f} vs SMA50 {snap.sma_50:.2f}.",
            price_movement_summary=f"Last close {snap.price:.2f}, daily move {snap.change_pct:.2f}%.",
            indicator_explanation="SMA20 above SMA50 suggests near-term momentum; gap size indicates trend strength.",
            confidence=0.76,
        )


@dataclass
class NewsAgent:
    provider: DataProvider

    def run(self, ticker: str) -> NewsOutput:
        items = self.provider.get_news(ticker)
        sentiments = [item.get("sentiment", "neutral") for item in items]
        neg = sentiments.count("negative")
        pos = sentiments.count("positive")
        if pos > neg:
            summary = "News flow leans positive with product/business updates."
        elif neg > pos:
            summary = "News flow leans risk-off due to negative events."
        else:
            summary = "News flow is balanced/neutral."
        return NewsOutput(
            ticker=ticker.upper(),
            headlines=[item["headline"] for item in items],
            sentiment_summary=summary,
            extracted_events=[
                NewsEvent(
                    headline=item["headline"],
                    sentiment=item.get("sentiment", "neutral"),
                    event_type=item.get("event_type", "market"),
                )
                for item in items
            ],
            confidence=0.72,
        )


@dataclass
class PortfolioAgent:
    provider: DataProvider

    def run(self) -> PortfolioOutput:
        positions = self.provider.get_portfolio()
        max_w = max((p["weight"] for p in positions), default=0.0)
        concentration = "High single-name concentration risk detected." if max_w >= 0.3 else "Concentration appears moderate."
        return PortfolioOutput(
            composition_summary=f"{len(positions)} holdings with total notional ${sum(p['value'] for p in positions):,.0f}.",
            concentration_checks=[concentration],
            position_summaries=[f"{p['ticker']}: {p['weight']:.0%} (${p['value']:,.0f})" for p in positions],
            risk_breakdown="Primary risk is large-cap tech factor exposure and growth beta concentration.",
            allocation_breakdown=", ".join(f"{p['ticker']} {p['weight']:.0%}" for p in positions),
            confidence=0.79,
        )
