from tools import stock_tools


def test_get_stock_price_fallback_when_live_unavailable(monkeypatch):
    monkeypatch.setattr(stock_tools, '_get_live_price', lambda _symbol: None)
    result = stock_tools.get_stock_price.invoke({'symbol': 'AAPL'})
    assert result['symbol'] == 'AAPL'
    assert result['source'] == 'mock_fallback'
    assert isinstance(result['price'], float)


def test_get_stock_price_prefers_live_data(monkeypatch):
    monkeypatch.setattr(stock_tools, '_get_live_price', lambda _symbol: {'symbol': 'AAPL', 'price': 123.45, 'change': 1.1, 'change_pct': 0.9, 'volume': 1000, 'market_cap': '$1.0T', 'high_52w': 130.0, 'low_52w': 90.0, 'pe_ratio': 25.0, 'timestamp': '2026-01-01T00:00:00', 'source': 'yfinance'})
    result = stock_tools.get_stock_price.invoke({'symbol': 'AAPL'})
    assert result['source'] == 'yfinance'
    assert result['price'] == 123.45


def test_compare_stocks_returns_winner():
    result = stock_tools.compare_stocks.invoke({'symbols': 'AAPL,MSFT'})
    assert set(result['symbols_compared']) == {'AAPL', 'MSFT'}
    assert result['winner'] in result['comparison']
