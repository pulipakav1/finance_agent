import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor import SupervisorAgent
from agents.analyst_agent import AnalystAgent
from agents.news_agent import NewsAgent
from tools.portfolio_tools import optimize_portfolio, calculate_risk
from prompts.templates import AGGREGATOR_PROMPT
from graph.state import AgentState
load_dotenv()
_supervisor = SupervisorAgent()
_analyst = AnalystAgent()
_news_agent = NewsAgent()
_aggregator_llm = ChatOpenAI(model='gpt-4o', temperature=0.3, openai_api_key=os.getenv('OPENAI_API_KEY'))

def supervisor_node(state: AgentState) -> dict:
    user_query = state.get('user_query', '')
    messages = state.get('messages', [])
    routing = _supervisor.route(user_query, messages)
    new_symbols = routing.get('symbols', [])
    existing_symbols = state.get('active_symbols', [])
    all_symbols = list(set(existing_symbols + new_symbols))
    return {'next_agent': ','.join(routing.get('route', ['analyst'])), 'routing_reasoning': routing.get('reasoning', ''), 'active_symbols': all_symbols, 'agents_called': [], 'analyst_output': '', 'news_output': '', 'portfolio_output': '', 'iteration_count': state.get('iteration_count', 0) + 1, 'messages': [HumanMessage(content=user_query)]}

def analyst_node(state: AgentState) -> dict:
    user_query = state.get('user_query', '')
    symbols = state.get('active_symbols', [])
    enriched_query = user_query
    if symbols:
        enriched_query = f"{user_query}\nFocus on these symbols: {', '.join(symbols)}"
    result = _analyst.analyze(enriched_query)
    existing_log = state.get('tool_calls_log', [])
    new_log = result.get('tool_calls_log', [])
    agents_called = state.get('agents_called', [])
    return {'analyst_output': result['output'], 'tool_calls_log': existing_log + new_log, 'agents_called': agents_called + ['analyst']}

def news_node(state: AgentState) -> dict:
    user_query = state.get('user_query', '')
    symbols = state.get('active_symbols', [])
    enriched_query = user_query
    if symbols:
        enriched_query = f"{user_query}\nAnalyze news for: {', '.join(symbols)}"
    result = _news_agent.analyze(enriched_query)
    existing_log = state.get('tool_calls_log', [])
    new_log = result.get('tool_calls_log', [])
    agents_called = state.get('agents_called', [])
    return {'news_output': result['output'], 'tool_calls_log': existing_log + new_log, 'agents_called': agents_called + ['news']}

def portfolio_node(state: AgentState) -> dict:
    user_query = state.get('user_query', '').lower()
    symbols = state.get('active_symbols', [])
    import re
    holdings_match = re.search('([A-Z]+:\\d+(?:,[A-Z]+:\\d+)+)', state.get('user_query', ''), re.IGNORECASE)
    if holdings_match:
        holdings_str = holdings_match.group(1).upper()
    elif symbols:
        default_shares = 10
        holdings_str = ','.join((f'{sym}:{default_shares}' for sym in symbols[:5]))
    else:
        holdings_str = 'AAPL:10,MSFT:5,NVDA:8,AMZN:12'
    portfolio_result = optimize_portfolio.invoke({'holdings': holdings_str})
    symbols_str = ','.join(symbols[:4] if symbols else ['AAPL', 'MSFT', 'NVDA'])
    weights_str = ','.join(['0.25'] * len(symbols[:4])) if symbols else '0.33,0.33,0.34'
    risk_result = calculate_risk.invoke({'symbols': symbols_str, 'weights': weights_str})
    output = f"**Portfolio Analysis**\n\n**Holdings Analyzed:** {holdings_str}\n**Total Portfolio Value:** ${portfolio_result.get('total_value', 0):,.2f}\n\n**Risk Profile:**\n- Risk Score: {portfolio_result.get('risk_score', 'N/A')} / 10 ({portfolio_result.get('risk_level', 'N/A')})\n- Sharpe Ratio: {portfolio_result.get('sharpe_ratio', 'N/A')}\n- Diversification: {portfolio_result.get('diversification_rating', 'N/A')}\n- Max Drawdown Estimate: {portfolio_result.get('max_drawdown_estimate', 'N/A')}\n\n**Portfolio Beta:** {risk_result.get('portfolio_beta', 'N/A')}\n**Volatility:** {risk_result.get('volatility_score', 'N/A')}\n**Value at Risk (95%):** {risk_result.get('var_95', 'N/A')}\n\n**Rebalancing Suggestion:** {portfolio_result.get('suggested_rebalance', 'N/A')}\n\n**Correlation Note:** {risk_result.get('correlation_matrix_summary', 'N/A')}\n"
    tool_calls = [{'tool': 'optimize_portfolio', 'input': holdings_str, 'output_summary': f"Total value: ${portfolio_result.get('total_value', 0):,.2f}"}, {'tool': 'calculate_risk', 'input': f'symbols={symbols_str}', 'output_summary': f"Beta: {risk_result.get('portfolio_beta', 'N/A')}"}]
    existing_log = state.get('tool_calls_log', [])
    agents_called = state.get('agents_called', [])
    return {'portfolio_output': output, 'tool_calls_log': existing_log + tool_calls, 'agents_called': agents_called + ['portfolio']}

def aggregator_node(state: AgentState) -> dict:
    user_query = state.get('user_query', '')
    analyst_output = state.get('analyst_output', '')
    news_output = state.get('news_output', '')
    portfolio_output = state.get('portfolio_output', '')
    agents_called = state.get('agents_called', [])
    if len(agents_called) == 1:
        if 'analyst' in agents_called and analyst_output:
            final = analyst_output
        elif 'news' in agents_called and news_output:
            final = news_output
        elif 'portfolio' in agents_called and portfolio_output:
            final = portfolio_output
        else:
            final = "I couldn't retrieve the requested information. Please try again."
    else:
        prompt_val = AGGREGATOR_PROMPT.format_messages(user_query=user_query, analyst_output=analyst_output or 'Not applicable for this query.', news_output=news_output or 'Not applicable for this query.', portfolio_output=portfolio_output or 'Not applicable for this query.')
        response = _aggregator_llm.invoke(prompt_val)
        final = response.content
    return {'final_response': final, 'messages': [AIMessage(content=final)]}
