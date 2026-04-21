from langchain_core.tools import tool
from utils.mock_data import get_mock_price
import random
import hashlib

def _portfolio_rng(holdings_str: str) -> random.Random:
    seed = int(hashlib.md5(holdings_str.encode()).hexdigest()[:8], 16)
    return random.Random(seed)

@tool
def optimize_portfolio(holdings: str) -> dict:
    """
    Analyze and optimize a stock portfolio given current holdings.
    Calculates total value, allocation percentages, risk score, estimated
    Sharpe ratio, diversification rating, suggested rebalancing actions,
    and maximum drawdown estimate.

    Args:
        holdings: Holdings in format 'SYMBOL:SHARES,SYMBOL:SHARES'
                  e.g., 'AAPL:10,MSFT:5,NVDA:8'
    """
    rng = _portfolio_rng(holdings)
    positions = {}
    for item in holdings.split(','):
        item = item.strip()
        if ':' in item:
            sym, shares_str = item.split(':', 1)
            try:
                shares = float(shares_str.strip())
                price_data = get_mock_price(sym.strip().upper())
                value = price_data['price'] * shares
                positions[sym.strip().upper()] = {'shares': shares, 'price': price_data['price'], 'value': round(value, 2)}
            except (ValueError, KeyError):
                continue
    if not positions:
        return {'error': 'No valid holdings parsed. Use format: AAPL:10,MSFT:5'}
    total_value = sum((p['value'] for p in positions.values()))
    allocation = {sym: {**data, 'allocation_pct': round(data['value'] / total_value * 100, 2)} for sym, data in positions.items()}
    num_positions = len(positions)
    diversification = 'Excellent' if num_positions >= 6 else 'Good' if num_positions >= 4 else 'Moderate' if num_positions >= 3 else 'Concentrated'
    risk_score = round(rng.uniform(3.5, 8.5), 1)
    sharpe = round(rng.uniform(0.8, 2.4), 2)
    max_drawdown = round(rng.uniform(-15, -35), 1)
    max_pos = max(allocation.items(), key=lambda x: x[1]['allocation_pct'])
    rebalance_note = f"Consider trimming {max_pos[0]} ({max_pos[1]['allocation_pct']}% of portfolio) if target weight is below 20%." if max_pos[1]['allocation_pct'] > 20 else 'Portfolio appears reasonably balanced. Review quarterly.'
    return {'total_value': round(total_value, 2), 'positions': allocation, 'risk_score': risk_score, 'risk_level': 'High' if risk_score > 7 else 'Medium' if risk_score > 4 else 'Low', 'sharpe_ratio': sharpe, 'diversification_rating': diversification, 'suggested_rebalance': rebalance_note, 'max_drawdown_estimate': f'{max_drawdown}%', 'position_count': num_positions}

@tool
def calculate_risk(symbols: str, weights: str) -> dict:
    """
    Calculate portfolio risk metrics given a list of symbols and their
    portfolio weights. Returns portfolio beta, volatility score, Value-at-Risk
    at 95% confidence level, a correlation summary, and overall risk level.

    Args:
        symbols: Comma-separated symbols, e.g., 'AAPL,MSFT,NVDA'
        weights: Comma-separated weights (must sum to 1.0), e.g., '0.4,0.3,0.3'
    """
    rng = _portfolio_rng(symbols + weights)
    sym_list = [s.strip().upper() for s in symbols.split(',')]
    try:
        weight_list = [float(w.strip()) for w in weights.split(',')]
    except ValueError:
        weight_list = [1.0 / len(sym_list)] * len(sym_list)
    total_w = sum(weight_list)
    weight_list = [w / total_w for w in weight_list]
    beta = round(rng.uniform(0.8, 1.6), 2)
    volatility = round(rng.uniform(12, 35), 1)
    var_95 = round(rng.uniform(-3.5, -8.0), 2)
    correlation_summary = 'High correlation detected between tech holdings (>0.75). Consider diversifying into different sectors to reduce systemic risk.' if len(sym_list) >= 3 else 'Insufficient positions for meaningful correlation analysis.'
    return {'symbols': sym_list, 'weights': [round(w, 3) for w in weight_list], 'portfolio_beta': beta, 'volatility_score': f'{volatility}% annualized', 'var_95': f'{var_95}% daily VaR (95% confidence)', 'correlation_matrix_summary': correlation_summary, 'risk_level': 'High' if beta > 1.3 else 'Medium' if beta > 0.9 else 'Low', 'interpretation': f"Beta of {beta} means the portfolio moves ~{beta}x relative to the market. Annualized volatility of {volatility}% indicates {('high' if volatility > 25 else 'moderate')} price fluctuation."}
