import random
import hashlib
from datetime import datetime, timedelta
BASE_PRICES = {'AAPL': 182.5, 'TSLA': 245.0, 'NVDA': 875.0, 'MSFT': 415.0, 'AMZN': 188.0, 'GOOGL': 175.0, 'META': 505.0, 'NFLX': 625.0, 'AMD': 178.0, 'INTC': 42.0}
BULLISH_HEADLINES = ['{symbol} beats Q3 earnings expectations by 12%, raises full-year guidance', "Analysts upgrade {symbol} to 'Strong Buy' citing AI-driven growth", '{symbol} announces $5B share buyback program, stock surges', 'Record revenue quarter for {symbol} as demand outpaces supply', '{symbol} secures major government contract worth $2.3B', 'Wall Street raises {symbol} price target by 18% on new product cycle', '{symbol} reports 28% YoY revenue growth, margin expansion accelerates']
BEARISH_HEADLINES = ['{symbol} misses revenue estimates amid macro headwinds', 'Short-seller report targets {symbol}, alleging accounting irregularities', '{symbol} CEO sells $50M in shares, raising investor concerns', 'Supply chain disruptions to impact {symbol} margins for next two quarters', "Regulatory probe into {symbol}'s business practices widens", '{symbol} lowers forward guidance citing slower consumer spending', 'Competitive pressure mounts as rivals undercut {symbol} on pricing']
NEUTRAL_HEADLINES = ['{symbol} announces new product line slated for Q1 release', '{symbol} holds annual investor day; maintains current outlook', '{symbol} completes acquisition of startup for undisclosed sum', "Analysts maintain 'Hold' on {symbol} ahead of earnings next week", '{symbol} partners with Microsoft on cloud infrastructure expansion']

def _seed_for_symbol(symbol: str) -> random.Random:
    seed = int(hashlib.md5(symbol.upper().encode()).hexdigest()[:8], 16)
    return random.Random(seed)

def get_mock_price(symbol: str) -> dict:
    rng = _seed_for_symbol(symbol)
    base = BASE_PRICES.get(symbol.upper(), rng.uniform(50, 500))
    drift = rng.uniform(-0.03, 0.03)
    price = round(base * (1 + drift), 2)
    prev_close = round(base * (1 + rng.uniform(-0.02, 0.02)), 2)
    change = round(price - prev_close, 2)
    change_pct = round(change / prev_close * 100, 2)
    return {'symbol': symbol.upper(), 'price': price, 'change': change, 'change_pct': change_pct, 'volume': rng.randint(10000000, 80000000), 'market_cap': f'${round(price * rng.randint(5, 30) * 1000000000.0 / 1000000000000.0, 2)}T', 'high_52w': round(price * rng.uniform(1.05, 1.45), 2), 'low_52w': round(price * rng.uniform(0.55, 0.9), 2), 'pe_ratio': round(rng.uniform(15, 55), 1), 'timestamp': datetime.now().isoformat()}

def get_mock_technicals(symbol: str) -> dict:
    rng = _seed_for_symbol(symbol)
    price_data = get_mock_price(symbol)
    price = price_data['price']
    rsi = round(rng.uniform(30, 80), 1)
    macd = round(rng.uniform(-5, 5), 3)
    macd_signal = round(macd + rng.uniform(-2, 2), 3)
    if rsi > 60 and macd > macd_signal:
        trend = 'BULLISH'
    elif rsi < 40 and macd < macd_signal:
        trend = 'BEARISH'
    else:
        trend = 'NEUTRAL'
    return {'symbol': symbol.upper(), 'rsi': rsi, 'macd': macd, 'macd_signal': macd_signal, 'ma_50': round(price * rng.uniform(0.92, 1.08), 2), 'ma_200': round(price * rng.uniform(0.85, 1.15), 2), 'bollinger_upper': round(price * 1.05, 2), 'bollinger_lower': round(price * 0.95, 2), 'atr': round(price * rng.uniform(0.01, 0.03), 2), 'trend': trend, 'momentum_score': round(rng.uniform(0, 100), 1)}

def get_mock_price_history(symbol: str, days: int=30) -> list:
    rng = _seed_for_symbol(symbol)
    base = BASE_PRICES.get(symbol.upper(), rng.uniform(50, 500))
    history = []
    price = base
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).strftime('%Y-%m-%d')
        daily_change = rng.uniform(-0.02, 0.02)
        open_price = round(price, 2)
        close_price = round(price * (1 + daily_change), 2)
        high = round(max(open_price, close_price) * rng.uniform(1.001, 1.015), 2)
        low = round(min(open_price, close_price) * rng.uniform(0.985, 0.999), 2)
        history.append({'date': date, 'open': open_price, 'high': high, 'low': low, 'close': close_price, 'volume': rng.randint(5000000, 50000000)})
        price = close_price
    return history

def get_mock_news(symbol: str) -> list:
    rng = _seed_for_symbol(symbol)
    news_items = []
    pool = [(h, 'POSITIVE', rng.uniform(0.4, 0.9)) for h in BULLISH_HEADLINES[:3]] + [(h, 'NEGATIVE', rng.uniform(-0.9, -0.3)) for h in BEARISH_HEADLINES[:1]]
    rng.shuffle(pool)
    for i, (headline_template, sentiment, score) in enumerate(pool[:4]):
        hours_ago = rng.randint(1, 48)
        published = datetime.now() - timedelta(hours=hours_ago)
        news_items.append({'headline': headline_template.format(symbol=symbol.upper()), 'sentiment': sentiment, 'score': round(score, 3), 'source': rng.choice(['Reuters', 'Bloomberg', 'CNBC', 'WSJ', 'MarketWatch']), 'published_at': published.strftime('%Y-%m-%d %H:%M'), 'summary': f'Analysis of recent developments affecting {symbol.upper()} stock performance and investor outlook.'})
    return news_items

def get_mock_sentiment(symbol: str) -> dict:
    rng = _seed_for_symbol(symbol)
    bull_pct = rng.uniform(40, 70)
    price_data = get_mock_price(symbol)
    overall = 'BULLISH' if bull_pct > 55 else 'BEARISH' if bull_pct < 45 else 'NEUTRAL'
    return {'symbol': symbol.upper(), 'overall_sentiment': overall, 'bull_bear_ratio': f'{round(bull_pct, 1)}% Bull / {round(100 - bull_pct, 1)}% Bear', 'analyst_consensus': rng.choice(['Strong Buy', 'Buy', 'Hold', 'Underperform']), 'price_target': round(price_data['price'] * rng.uniform(1.05, 1.3), 2), 'insider_trading_summary': rng.choice(['Net insider buying of $2.1M in last 30 days', 'No significant insider activity in last 30 days', 'CFO purchased 5,000 shares at market open', 'Minor insider selling; routine RSU vesting'])}

def get_mock_company_info(symbol: str) -> dict:
    rng = _seed_for_symbol(symbol)
    sectors = {'AAPL': ('Technology', 'Consumer Electronics'), 'TSLA': ('Consumer Discretionary', 'Electric Vehicles'), 'NVDA': ('Technology', 'Semiconductors'), 'MSFT': ('Technology', 'Software'), 'AMZN': ('Consumer Discretionary', 'E-Commerce & Cloud'), 'GOOGL': ('Technology', 'Internet Services'), 'META': ('Technology', 'Social Media'), 'NFLX': ('Communication Services', 'Streaming')}
    sector, industry = sectors.get(symbol.upper(), ('Technology', 'Software'))
    return {'symbol': symbol.upper(), 'sector': sector, 'industry': industry, 'employees': rng.randint(10000, 150000), 'description': f'{symbol.upper()} is a leading company in the {industry} space, known for innovation and strong shareholder returns.', 'founded': rng.randint(1975, 2005), 'headquarters': rng.choice(['Cupertino, CA', 'Seattle, WA', 'Austin, TX', 'San Jose, CA', 'Menlo Park, CA'])}
