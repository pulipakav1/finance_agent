from src.fin_platform.supervisor import route_query


def test_supervisor_routes_news_and_analyst() -> None:
    decision = route_query("Give me AAPL trend and latest news sentiment")
    assert "analyst" in decision.routes
    assert "news" in decision.routes
    assert decision.ticker == "AAPL"


def test_supervisor_fallback_default() -> None:
    decision = route_query("hello there")
    assert decision.routes == ["analyst"]
    assert decision.fallback_reason
