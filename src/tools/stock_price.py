"""
Tool: get_stock_price
Uses yfinance. Avoids stock.info until the end — it hits Yahoo quoteSummary and often 429s.
Price history + fast_info first; info is optional enrichment.
"""

import time

import pandas as pd
import yfinance as yf
from loguru import logger

# Short burst of tickers (e.g. compare) trips Yahoo limits; space calls slightly.
_LAST_FETCH = 0.0
_MIN_GAP_S = 0.35


def _throttle():
    global _LAST_FETCH
    now = time.monotonic()
    gap = now - _LAST_FETCH
    if gap < _MIN_GAP_S:
        time.sleep(_MIN_GAP_S - gap)
    _LAST_FETCH = time.monotonic()


def _load_history(stock, period: str) -> pd.DataFrame:
    _throttle()
    h = stock.history(period=period, auto_adjust=True)
    if isinstance(h, pd.DataFrame) and not h.empty:
        return h
    return pd.DataFrame()


def _safe_info(stock) -> dict:
    """Yahoo quoteSummary is rate-limited; skip if it fails."""
    try:
        raw = stock.info
        return raw if isinstance(raw, dict) else {}
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "too many" in err or "rate" in err:
            logger.warning("yfinance .info skipped (rate limit): {}", e)
        else:
            logger.warning("yfinance .info failed: {}", e)
        return {}


def _fast_last(stock):
    try:
        fast = getattr(stock, "fast_info", None)
        if isinstance(fast, dict):
            return fast.get("last_price") or fast.get("lastPrice")
        if fast is not None:
            return getattr(fast, "last_price", None) or getattr(fast, "lastPrice", None)
    except Exception as e:
        logger.debug("fast_info: {}", e)
    return None


def get_stock_price(ticker: str, period: str = "1mo") -> dict:
    try:
        sym = ticker.upper().strip()
        stock = yf.Ticker(sym)

        # 1) History first — different Yahoo endpoint, less likely to 429 than .info
        hist = _load_history(stock, period)
        used_period = period
        if hist.empty:
            for fb in ("5d", "1mo", "3mo", "1y"):
                hist = _load_history(stock, fb)
                if not hist.empty:
                    used_period = fb
                    break

        if hist.empty:
            return {"error": f"No price history for {sym}. Verify the ticker or retry later."}

        last_bar = float(hist["Close"].iloc[-1])
        fi_last = _fast_last(stock)

        # 2) Optional .info — only for names, 52w, volume, etc.
        info = _safe_info(stock)

        current = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or fi_last
            or last_bar
        )
        try:
            current = float(current)
        except (TypeError, ValueError):
            current = last_bar

        prev = info.get("previousClose")
        if prev is None and len(hist) > 1:
            prev = float(hist["Close"].iloc[-2])
        else:
            try:
                prev = float(prev) if prev is not None else current
            except (TypeError, ValueError):
                prev = current

        price_change = current - prev
        pct_change = (price_change / prev) * 100 if prev else 0.0

        prices = hist["Close"].tolist()
        high_52w = info.get("fiftyTwoWeekHigh") or max(prices)
        low_52w = info.get("fiftyTwoWeekLow") or min(prices)

        ma_20 = hist["Close"].rolling(20).mean().iloc[-1] if len(hist) >= 20 else None
        ma_50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None

        note = "Prices from yfinance; may be delayed."
        if not info:
            note += " (Full company profile skipped — Yahoo rate limit; numbers are from price history.)"

        result = {
            "ticker": sym,
            "company_name": info.get("longName") or info.get("shortName") or sym,
            "current_price": round(current, 2),
            "previous_close": round(prev, 2),
            "price_change": round(price_change, 2),
            "pct_change": round(pct_change, 2),
            "volume": info.get("volume") or 0,
            "avg_volume": info.get("averageVolume") or 0,
            "market_cap": info.get("marketCap") or 0,
            "52w_high": round(float(high_52w), 2),
            "52w_low": round(float(low_52w), 2),
            "ma_20": round(float(ma_20), 2) if ma_20 is not None and pd.notna(ma_20) else None,
            "ma_50": round(float(ma_50), 2) if ma_50 is not None and pd.notna(ma_50) else None,
            "period": used_period,
            "data_points": len(hist),
            "period_high": round(float(hist["Close"].max()), 2),
            "period_low": round(float(hist["Close"].min()), 2),
            "period_return_pct": round(
                (
                    (float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[0]))
                    / float(hist["Close"].iloc[0])
                )
                * 100,
                2,
            ),
            "note": note,
        }

        logger.info("Stock price fetched: {} @ ${}", sym, current)
        return result

    except Exception as e:
        logger.error("get_stock_price failed for {}: {}", ticker, e)
        return {"error": str(e), "ticker": ticker.upper().strip()}


def get_stock_comparison(tickers: list[str], period: str = "3mo") -> dict:
    """Compare multiple stocks; spacing reduces Yahoo 429s."""
    results = {}
    for i, t in enumerate(tickers):
        if i > 0:
            time.sleep(0.6)
        results[t] = get_stock_price(t, period)
    return results
