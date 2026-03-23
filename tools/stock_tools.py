from langchain_core.tools import tool
from utils.mock_data import get_mock_price, get_mock_news, get_mock_sentiment, get_mock_company_info
from datetime import datetime
import yfinance as yf

def _fmt_market_cap(value) -> str:
    try:
        v = float(value)
    except Exception:
        return 'N/A'
    if v >= 1_000_000_000_000:
        return f'${round(v / 1_000_000_000_000, 2)}T'
    if v >= 1_000_000_000:
        return f'${round(v / 1_000_000_000, 2)}B'
    if v >= 1_000_000:
        return f'${round(v / 1_000_000, 2)}M'
    return f'${round(v, 2)}'

def _safe_num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def _get_live_price(symbol: str) -> dict | None:
    ticker = yf.Ticker(symbol)
    fast = getattr(ticker, 'fast_info', None) or {}
    info = getattr(ticker, 'info', None) or {}
    price = _safe_num(fast.get('last_price') or info.get('currentPrice'))
    prev_close = _safe_num(fast.get('previous_close') or info.get('previousClose'))
    if price <= 0:
        hist = ticker.history(period='2d')
        if len(hist) == 0:
            return None
        price = _safe_num(hist['Close'].iloc[-1])
        prev_close = _safe_num(hist['Close'].iloc[-2] if len(hist) > 1 else price)
    if price <= 0:
        return None
    if prev_close <= 0:
        prev_close = price
    change = round(price - prev_close, 2)
    change_pct = round(change / prev_close * 100, 2) if prev_close else 0.0
    volume = int(_safe_num(fast.get('last_volume') or info.get('volume'), 0))
    market_cap_raw = fast.get('market_cap') or info.get('marketCap')
    pe_ratio = _safe_num(info.get('trailingPE') or info.get('forwardPE'), 0.0)
    high_52w = _safe_num(fast.get('year_high') or info.get('fiftyTwoWeekHigh'), price)
    low_52w = _safe_num(fast.get('year_low') or info.get('fiftyTwoWeekLow'), price)
    return {'symbol': symbol, 'price': round(price, 2), 'change': change, 'change_pct': change_pct, 'volume': volume, 'market_cap': _fmt_market_cap(market_cap_raw), 'high_52w': round(high_52w, 2), 'low_52w': round(low_52w, 2), 'pe_ratio': round(pe_ratio, 1) if pe_ratio else 'N/A', 'timestamp': datetime.now().isoformat(), 'source': 'yfinance'}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Get the current stock price and key market data for a given ticker symbol.
    Returns price, price change, percent change, volume, market cap,
    52-week high/low, P/E ratio, and timestamp.
    Use this first before any stock analysis.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'NVDA')
    """
    normalized = symbol.upper().strip()
    try:
        live = _get_live_price(normalized)
        if live:
            return live
    except Exception:
        pass
    fallback = get_mock_price(normalized)
    fallback['source'] = 'mock_fallback'
    return fallback

@tool
def compare_stocks(symbols: str) -> dict:
    """
    Compare multiple stocks side by side using key financial metrics.
    Returns a structured comparison with a recommended winner and reasoning.

    Args:
        symbols: Comma-separated ticker symbols, e.g. 'AAPL,MSFT,GOOGL'
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    comparison = {}
    for sym in symbol_list:
        data = get_stock_price.invoke({'symbol': sym})
        comparison[sym] = {'price': data['price'], 'change_pct': data['change_pct'], 'pe_ratio': data['pe_ratio'], 'market_cap': data['market_cap']}
    best = max(comparison.items(), key=lambda x: x[1]['change_pct'])
    return {'comparison': comparison, 'winner': best[0], 'reasoning': f"{best[0]} leads with {best[1]['change_pct']}% daily change. Consider P/E ratios and market cap for deeper valuation analysis.", 'symbols_compared': symbol_list}

@tool
def get_company_info(symbol: str) -> dict:
    """
    Get fundamental company information for a ticker: sector, industry,
    employee count, business description, founding year, and headquarters.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
    """
    return get_mock_company_info(symbol.upper().strip())

@tool
def get_stock_news(symbol: str) -> dict:
    """
    Retrieve the latest news articles for a stock, including sentiment scores.
    Each article includes headline, sentiment label (POSITIVE/NEGATIVE/NEUTRAL),
    numerical sentiment score from -1.0 to 1.0, source, and a brief summary.

    Args:
        symbol: Stock ticker symbol (e.g., 'TSLA')
    """
    news = get_mock_news(symbol.upper().strip())
    return {'symbol': symbol.upper(), 'articles': news, 'article_count': len(news), 'avg_sentiment': round(sum((a['score'] for a in news)) / len(news), 3) if news else 0}

@tool
def get_market_sentiment(symbol: str) -> dict:
    """
    Get overall market sentiment metrics for a stock: bull/bear ratio,
    analyst consensus rating, price target, and insider trading activity summary.

    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA')
    """
    return get_mock_sentiment(symbol.upper().strip())
