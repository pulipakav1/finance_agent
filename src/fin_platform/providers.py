"""Data provider abstraction for market, news, and portfolio sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.fin_platform.config import settings

_vader = SentimentIntensityAnalyzer()


@dataclass
class MarketSnapshot:
    ticker: str
    price: float
    change_pct: float
    sma_20: float
    sma_50: float


class DataProvider(ABC):
    @abstractmethod
    def get_market_snapshot(self, ticker: str) -> MarketSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_news(self, ticker: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_portfolio(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class MockDataProvider(DataProvider):
    def get_market_snapshot(self, ticker: str) -> MarketSnapshot:
        return MarketSnapshot(ticker=ticker, price=190.2, change_pct=1.3, sma_20=184.4, sma_50=178.1)

    def get_news(self, ticker: str) -> list[dict[str, Any]]:
        return [
            {"headline": f"{ticker} launches new enterprise AI feature", "sentiment": "positive", "event_type": "product"},
            {"headline": f"{ticker} faces antitrust hearing", "sentiment": "negative", "event_type": "regulatory"},
        ]

    def get_portfolio(self) -> list[dict[str, Any]]:
        return [
            {"ticker": "AAPL", "weight": 0.34, "value": 34000},
            {"ticker": "NVDA", "weight": 0.26, "value": 26000},
            {"ticker": "MSFT", "weight": 0.22, "value": 22000},
            {"ticker": "TSLA", "weight": 0.18, "value": 18000},
        ]


class YFinanceProvider(DataProvider):
    def get_market_snapshot(self, ticker: str) -> MarketSnapshot:
        hist = yf.Ticker(ticker).history(period="3mo")
        close = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else close
        change_pct = ((close - prev) / prev) * 100 if prev else 0.0
        sma_20 = float(hist["Close"].tail(20).mean())
        sma_50 = float(hist["Close"].tail(50).mean())
        return MarketSnapshot(ticker=ticker.upper(), price=close, change_pct=change_pct, sma_20=sma_20, sma_50=sma_50)

    def get_news(self, ticker: str) -> list[dict[str, Any]]:
        raw_news = yf.Ticker(ticker).news[:5]
        results = []
        for item in raw_news:
            headline = item.get("title", "Untitled")
            score = _vader.polarity_scores(headline)["compound"]
            if score >= 0.05:
                sentiment = "positive"
            elif score <= -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            results.append({
                "headline": headline,
                "sentiment": sentiment,
                "event_type": "market",
            })
        return results

    def get_portfolio(self) -> list[dict[str, Any]]:
        tickers = ["AAPL", "NVDA", "MSFT", "TSLA"]
        positions = []
        total_value = 0.0
        snapshots = []
        for t in tickers:
            try:
                hist = yf.Ticker(t).history(period="1d")
                price = float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
            except Exception:
                price = 0.0
            value = price * 100  # demo: 100 shares each
            snapshots.append((t, price, value))
            total_value += value
        for ticker_sym, price, value in snapshots:
            weight = round(value / total_value, 4) if total_value else 0.0
            positions.append({"ticker": ticker_sym, "weight": weight, "value": round(value, 2)})
        return positions


def build_provider() -> DataProvider:
    if settings.enable_live_data or settings.data_mode == "live":
        return YFinanceProvider()
    return MockDataProvider()
