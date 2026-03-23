# Results Snapshot

This file captures representative behavior after adding live `yfinance` pricing to the stock tool layer.

## Example Queries

### 1) Query
`Analyze NVDA — give me technical indicators, current price, and a signal`

- Expected route: `["analyst"]`
- Symbols extracted: `["NVDA"]`
- Tool pattern:
  - `get_stock_price` (live `yfinance` when available, mock fallback otherwise)
  - `get_technical_indicators`
  - `get_company_info`
- Output quality notes:
  - Includes concrete price/technical numbers
  - Ends with `SIGNAL` and `CONFIDENCE`
  - Uses the tool log for traceability in UI

### 2) Query
`What is the latest sentiment on TSLA and what catalyst matters most?`

- Expected route: `["news"]`
- Symbols extracted: `["TSLA"]`
- Tool pattern:
  - `get_stock_news`
  - `get_market_sentiment`
- Output quality notes:
  - Summarizes recent headlines
  - Provides sentiment class and score
  - Identifies a single key catalyst

### 3) Query
`Compare AAPL and MSFT, then suggest which is better right now`

- Expected route: `["analyst"]`
- Symbols extracted: `["AAPL","MSFT"]`
- Tool pattern:
  - `compare_stocks` (internally calls `get_stock_price` for each symbol)
  - optional technical/fundamental context tools
- Output quality notes:
  - Side-by-side numeric comparison
  - Clear recommendation with rationale

### 4) Query
`Build me a portfolio with AAPL:10,MSFT:5,NVDA:8 and assess risk`

- Expected route: `["portfolio"]` (or `["portfolio","analyst"]` depending on phrasing)
- Symbols extracted: `["AAPL","MSFT","NVDA"]`
- Tool pattern:
  - `optimize_portfolio`
  - `calculate_risk`
- Output quality notes:
  - Returns portfolio value and risk metrics
  - Includes rebalancing suggestion

## Routing Decision Shape

Supervisor returns structured JSON used by graph conditional edges:

```json
{
  "route": ["analyst", "news"],
  "reasoning": "Need both technical and sentiment context.",
  "symbols": ["TSLA"]
}
```

## What Changed the Story

- `get_stock_price` now attempts real market data via `yfinance`.
- When live fetch fails, the app still works through deterministic mock fallback.
- This means analysis can include real-time price movement while preserving demo reliability.
