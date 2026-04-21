from src.fin_platform.providers import MockDataProvider


def test_mock_provider_shapes() -> None:
    provider = MockDataProvider()
    snap = provider.get_market_snapshot("AAPL")
    assert snap.ticker == "AAPL"
    assert provider.get_news("AAPL")
    assert provider.get_portfolio()
