from langchain_core.tools import tool
from utils.mock_data import get_mock_technicals, get_mock_price_history

@tool
def get_technical_indicators(symbol: str) -> dict:
    """
    Get technical analysis indicators for a stock.
    Returns RSI (momentum oscillator), MACD and signal line (trend following),
    50-day and 200-day moving averages, Bollinger Bands (volatility),
    ATR (average true range), an overall trend signal (BULLISH/BEARISH/NEUTRAL),
    and a momentum score from 0–100.

    Use this to determine buy/sell signals and market momentum.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
    """
    return get_mock_technicals(symbol.upper().strip())

@tool
def get_price_history(symbol: str, days: int=30) -> dict:
    """
    Get historical OHLCV (Open, High, Low, Close, Volume) price data
    for a stock over a specified number of trading days.
    Useful for charting, trend analysis, and pattern recognition.

    Args:
        symbol: Stock ticker symbol (e.g., 'MSFT')
        days: Number of historical days to retrieve (default: 30, max: 90)
    """
    days = min(max(int(days), 5), 90)
    history = get_mock_price_history(symbol.upper().strip(), days)
    return {'symbol': symbol.upper(), 'days_requested': days, 'data_points': len(history), 'history': history, 'period_high': max((d['high'] for d in history)), 'period_low': min((d['low'] for d in history)), 'period_return_pct': round((history[-1]['close'] - history[0]['open']) / history[0]['open'] * 100, 2)}
