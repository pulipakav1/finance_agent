"""
Tool: get_financial_statements
Fetches income statement, balance sheet, and cash flow data.
"""

import yfinance as yf
import pandas as pd
from loguru import logger


def _safe_info(stock) -> dict:
    """Yahoo quoteSummary is rate-limited; statements may still load when this fails."""
    try:
        raw = stock.info
        return raw if isinstance(raw, dict) else {}
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "too many" in err:
            logger.warning("yfinance .info skipped in financials (rate limit): {}", e)
        else:
            logger.warning("yfinance .info failed in financials: {}", e)
        return {}


def _safe_val(val) -> float | None:
    """Convert pandas/numpy values to plain Python floats."""
    try:
        if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'NaT'):
            return None
        f = float(val)
        return None if pd.isna(f) else round(f, 2)
    except:
        return None


def get_financial_statements(ticker: str) -> dict:
    """
    Fetch key financial statement data: income statement, balance sheet,
    cash flow, and computed financial ratios.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with financials and computed ratios
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info  = stock.info

        # ── Income Statement ──────────────────────────────────────────────
        income_stmt = stock.income_stmt
        income = {}
        if not income_stmt.empty:
            col = income_stmt.columns[0]  # Most recent year
            def ig(key):
                return _safe_val(income_stmt.loc[key, col]) if key in income_stmt.index else None

            income = {
                "period":            str(col.date()) if hasattr(col, 'date') else str(col),
                "total_revenue":     ig("Total Revenue"),
                "gross_profit":      ig("Gross Profit"),
                "operating_income":  ig("Operating Income"),
                "net_income":        ig("Net Income"),
                "ebitda":            ig("EBITDA"),
                "interest_expense":  ig("Interest Expense"),
            }

        # ── Balance Sheet ─────────────────────────────────────────────────
        balance = stock.balance_sheet
        bs = {}
        if not balance.empty:
            col = balance.columns[0]
            def bg(key):
                return _safe_val(balance.loc[key, col]) if key in balance.index else None

            bs = {
                "total_assets":       bg("Total Assets"),
                "total_liabilities":  bg("Total Liabilities Net Minority Interest"),
                "total_equity":       bg("Stockholders Equity"),
                "cash":               bg("Cash And Cash Equivalents"),
                "total_debt":         bg("Total Debt"),
                "current_assets":     bg("Current Assets"),
                "current_liabilities":bg("Current Liabilities"),
            }

        # ── Cash Flow ─────────────────────────────────────────────────────
        cf_stmt = stock.cashflow
        cf = {}
        if not cf_stmt.empty:
            col = cf_stmt.columns[0]
            def cg(key):
                return _safe_val(cf_stmt.loc[key, col]) if key in cf_stmt.index else None

            cf = {
                "operating_cash_flow": cg("Operating Cash Flow"),
                "capital_expenditure": cg("Capital Expenditure"),
                "free_cash_flow":      cg("Free Cash Flow"),
            }

        info = _safe_info(stock)

        # ── Key Ratios (from info + computed) ─────────────────────────────
        ratios = {
            "pe_ratio":           _safe_val(info.get("trailingPE")),
            "forward_pe":         _safe_val(info.get("forwardPE")),
            "ps_ratio":           _safe_val(info.get("priceToSalesTrailing12Months")),
            "pb_ratio":           _safe_val(info.get("priceToBook")),
            "debt_to_equity":     _safe_val(info.get("debtToEquity")),
            "current_ratio":      _safe_val(info.get("currentRatio")),
            "roe":                _safe_val(info.get("returnOnEquity")),
            "roa":                _safe_val(info.get("returnOnAssets")),
            "profit_margin":      _safe_val(info.get("profitMargins")),
            "gross_margin":       _safe_val(info.get("grossMargins")),
            "operating_margin":   _safe_val(info.get("operatingMargins")),
            "revenue_growth":     _safe_val(info.get("revenueGrowth")),
            "earnings_growth":    _safe_val(info.get("earningsGrowth")),
            "dividend_yield":     _safe_val(info.get("dividendYield")),
            "payout_ratio":       _safe_val(info.get("payoutRatio")),
            "beta":               _safe_val(info.get("beta")),
            "eps":                _safe_val(info.get("trailingEps")),
            "forward_eps":        _safe_val(info.get("forwardEps")),
        }

        sym = ticker.upper()
        result = {
            "ticker":              sym,
            "company_name":        info.get("longName") or info.get("shortName") or sym,
            "sector":              info.get("sector", "N/A"),
            "industry":            info.get("industry", "N/A"),
            "employees":           info.get("fullTimeEmployees"),
            "description":         info.get("longBusinessSummary", "")[:500],
            "income_statement":    income,
            "balance_sheet":       bs,
            "cash_flow":           cf,
            "key_ratios":          ratios,
        }

        logger.info(f"Financial statements fetched: {ticker}")
        return result

    except Exception as e:
        logger.error(f"get_financial_statements failed for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}
