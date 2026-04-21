from src.fin_platform.agents import AnalystAgent, NewsAgent, PortfolioAgent
from src.fin_platform.providers import MockDataProvider


def test_analyst_contract() -> None:
    out = AnalystAgent(MockDataProvider()).run("NVDA")
    assert out.ticker == "NVDA"
    assert out.technical_trend


def test_news_contract() -> None:
    out = NewsAgent(MockDataProvider()).run("MSFT")
    assert out.headlines
    assert out.extracted_events


def test_portfolio_contract() -> None:
    out = PortfolioAgent(MockDataProvider()).run()
    assert out.position_summaries
    assert out.allocation_breakdown
