from langchain_core.tools import tool
from utils.mock_data import get_mock_price, get_mock_news, get_mock_sentiment, get_mock_company_info

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
    return get_mock_price(symbol.upper().strip())

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
        data = get_mock_price(sym)
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
