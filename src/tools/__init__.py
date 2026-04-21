"""
Tool registry.
Defines all tools as Anthropic-compatible tool schemas and maps
tool names to their Python implementations.
"""

from .stock_price import get_stock_price, get_stock_comparison
from .financials import get_financial_statements
from .web_search import search_web, scrape_url
from .code_executor import run_python
from .report_generator import generate_report, list_reports, read_report


# ── Tool Schemas (Anthropic format) ──────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_stock_price",
        "description": (
            "PRIMARY source for live/current stock prices and intraday-style quotes from market data (yfinance). "
            "Use for ANY question about what a stock is trading at, its price today, or ticker quote. "
            "Always prefer this over web search for prices. Optional period for history (default 1mo)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'MSFT')",
                },
                "period": {
                    "type": "string",
                    "description": "Time period for historical data: '1d','5d','1mo','3mo','6mo','1y','2y','5y'",
                    "default": "3mo",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_stock_comparison",
        "description": (
            "Compare multiple stocks side by side over a given period. "
            "Use this when the user wants to compare two or more companies."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ticker symbols to compare",
                },
                "period": {
                    "type": "string",
                    "description": "Time period: '1mo','3mo','6mo','1y'",
                    "default": "3mo",
                },
            },
            "required": ["tickers"],
        },
    },
    {
        "name": "get_financial_statements",
        "description": (
            "Fetch income statement, balance sheet, cash flow statement, and "
            "key financial ratios (P/E, P/B, ROE, margins, debt/equity, etc.) "
            "for a company. Use this for fundamental analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "search_web",
        "description": (
            "Search the web for news, opinions, or events. "
            "Do NOT use this for stock prices or live quotes—use get_stock_price for that."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'Apple earnings Q4 2024', 'Tesla news this week')",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "scrape_url",
        "description": (
            "Fetch and extract clean text content from a specific URL. "
            "Use this after search_web to read the full content of a relevant article."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to scrape",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return",
                    "default": 3000,
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "run_python",
        "description": (
            "Execute Python code for financial calculations. Use this to: "
            "calculate ratios, compute percentage changes, compare metrics, "
            "estimate valuations, or perform any numerical analysis. "
            "Always print() your results so they appear in output."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Use print() to show results.",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "generate_report",
        "description": (
            "Save a structured investment report as a markdown file. "
            "Use this as the FINAL step after completing analysis to deliver "
            "a formatted report with recommendation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                },
                "title": {
                    "type": "string",
                    "description": "Report title",
                },
                "content": {
                    "type": "string",
                    "description": "Full markdown report content with analysis",
                },
                "recommendation": {
                    "type": "string",
                    "description": "Investment recommendation: BUY, HOLD, SELL, or NEUTRAL",
                    "enum": ["BUY", "HOLD", "SELL", "NEUTRAL"],
                },
            },
            "required": ["ticker", "title", "content", "recommendation"],
        },
    },
]


# ── Tool Executor ─────────────────────────────────────────────────────────────

TOOL_MAP = {
    "get_stock_price":         get_stock_price,
    "get_stock_comparison":    get_stock_comparison,
    "get_financial_statements": get_financial_statements,
    "search_web":              search_web,
    "scrape_url":              scrape_url,
    "run_python":              run_python,
    "generate_report":         generate_report,
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return result as string."""
    import json
    if tool_name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = TOOL_MAP[tool_name](**tool_input)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": tool_name})


__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_MAP",
    "execute_tool",
]
