import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import time
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='FinAgent — Multi-Agent Stock Analyst', page_icon='📈', layout='wide', initial_sidebar_state='collapsed')
from graph.graph_builder import build_graph
from memory.conversation import init_session_state, get_or_create_thread_id, get_graph_config, add_user_message, add_assistant_message, clear_conversation
from utils.mock_data import get_mock_price, get_mock_price_history
BLOOMBERG_CSS = '\n<style>\n    /* ── Base colors ── */\n    :root {\n        --bg-primary:   #0A0E1A;\n        --bg-surface:   #111827;\n        --bg-card:      #1A2235;\n        --accent-blue:  #00D4FF;\n        --accent-green: #00FF88;\n        --accent-red:   #FF4466;\n        --accent-gold:  #FFB347;\n        --text-primary: #E2E8F0;\n        --text-muted:   #8892A4;\n        --border:       #2D3748;\n    }\n\n    /* ── App background ── */\n    .stApp, .main, [data-testid="stAppViewContainer"] {\n        background-color: var(--bg-primary) !important;\n        color: var(--text-primary) !important;\n    }\n\n    [data-testid="stHeader"] { background-color: var(--bg-primary) !important; }\n    section[data-testid="stSidebar"] { background-color: var(--bg-surface) !important; }\n\n    /* ── Remove default Streamlit padding ── */\n    .block-container { padding: 1rem 1.5rem 1rem 1.5rem !important; max-width: 100% !important; }\n\n    /* ── Metric cards ── */\n    [data-testid="stMetric"] {\n        background: var(--bg-card);\n        border: 1px solid var(--border);\n        border-radius: 8px;\n        padding: 10px 14px !important;\n    }\n    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.75rem !important; }\n    [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-size: 1.1rem !important; }\n    [data-testid="stMetricDelta"] svg { display: none; }\n\n    /* ── Chat bubbles ── */\n    .user-bubble {\n        background: linear-gradient(135deg, #1E3A5F, #1A2F4E);\n        border: 1px solid #2D5A8E;\n        border-radius: 16px 16px 4px 16px;\n        padding: 12px 16px;\n        margin: 8px 0 8px 15%;\n        color: var(--text-primary);\n        font-size: 0.92rem;\n        line-height: 1.5;\n    }\n    .assistant-bubble {\n        background: var(--bg-card);\n        border: 1px solid var(--border);\n        border-left: 3px solid var(--accent-blue);\n        border-radius: 4px 16px 16px 16px;\n        padding: 14px 18px;\n        margin: 8px 15% 8px 0;\n        color: var(--text-primary);\n        font-size: 0.92rem;\n        line-height: 1.6;\n    }\n    .assistant-bubble h2 { color: var(--accent-blue) !important; font-size: 1rem !important; margin: 10px 0 6px 0 !important; }\n    .assistant-bubble h3 { color: var(--accent-gold) !important; font-size: 0.9rem !important; }\n    .assistant-bubble ul { margin: 4px 0 4px 18px !important; }\n    .assistant-bubble li { margin-bottom: 3px !important; }\n    .assistant-bubble strong { color: var(--accent-blue) !important; }\n\n    /* ── Input box ── */\n    [data-testid="stChatInput"] textarea {\n        background-color: var(--bg-card) !important;\n        border: 1px solid var(--border) !important;\n        color: var(--text-primary) !important;\n        border-radius: 10px !important;\n    }\n    [data-testid="stChatInput"] textarea:focus {\n        border-color: var(--accent-blue) !important;\n        box-shadow: 0 0 0 2px rgba(0,212,255,0.2) !important;\n    }\n\n    /* ── Buttons ── */\n    .stButton > button {\n        background: var(--bg-card) !important;\n        border: 1px solid var(--border) !important;\n        color: var(--text-primary) !important;\n        border-radius: 8px !important;\n        font-size: 0.82rem !important;\n        transition: all 0.2s !important;\n    }\n    .stButton > button:hover {\n        border-color: var(--accent-blue) !important;\n        color: var(--accent-blue) !important;\n        background: rgba(0,212,255,0.08) !important;\n    }\n\n    /* ── Expanders ── */\n    [data-testid="stExpander"] {\n        background: var(--bg-surface) !important;\n        border: 1px solid var(--border) !important;\n        border-radius: 8px !important;\n    }\n    [data-testid="stExpanderToggleIcon"] { color: var(--text-muted) !important; }\n\n    /* ── Section headers ── */\n    .section-header {\n        color: var(--accent-blue);\n        font-size: 0.7rem;\n        font-weight: 700;\n        letter-spacing: 0.12em;\n        text-transform: uppercase;\n        border-bottom: 1px solid var(--border);\n        padding-bottom: 6px;\n        margin-bottom: 12px;\n    }\n\n    /* ── Sentiment badge ── */\n    .badge-bullish { color: var(--accent-green) !important; font-weight: 700; }\n    .badge-bearish { color: var(--accent-red) !important; font-weight: 700; }\n    .badge-neutral { color: var(--accent-gold) !important; font-weight: 700; }\n\n    /* ── Watchlist ticker ── */\n    .ticker-row {\n        display: flex;\n        justify-content: space-between;\n        align-items: center;\n        padding: 8px 10px;\n        border-bottom: 1px solid var(--border);\n        cursor: pointer;\n    }\n    .ticker-symbol { color: var(--accent-blue); font-weight: 700; font-size: 0.88rem; }\n    .ticker-price { color: var(--text-primary); font-size: 0.88rem; }\n    .ticker-change-pos { color: var(--accent-green); font-size: 0.78rem; }\n    .ticker-change-neg { color: var(--accent-red); font-size: 0.78rem; }\n\n    /* ── Title ── */\n    .app-title {\n        font-size: 1.3rem;\n        font-weight: 800;\n        color: var(--accent-blue);\n        letter-spacing: 0.02em;\n    }\n    .app-subtitle { font-size: 0.75rem; color: var(--text-muted); }\n\n    /* ── Progress bar ── */\n    [data-testid="stProgress"] > div { background-color: var(--bg-card) !important; }\n    [data-testid="stProgress"] > div > div { background-color: var(--accent-blue) !important; }\n\n    /* ── Text inputs ── */\n    [data-testid="stTextInput"] input {\n        background: var(--bg-card) !important;\n        border: 1px solid var(--border) !important;\n        color: var(--text-primary) !important;\n        border-radius: 6px !important;\n        font-size: 0.85rem !important;\n    }\n\n    /* ── Info boxes ── */\n    [data-testid="stInfo"] {\n        background: rgba(0,212,255,0.08) !important;\n        border-left: 3px solid var(--accent-blue) !important;\n    }\n    [data-testid="stSuccess"] { border-left: 3px solid var(--accent-green) !important; }\n    [data-testid="stWarning"] { border-left: 3px solid var(--accent-gold) !important; }\n\n    /* ── Plotly chart background ── */\n    .js-plotly-plot .plotly { background: transparent !important; }\n\n    /* ── Scrollbar ── */\n    ::-webkit-scrollbar { width: 6px; height: 6px; }\n    ::-webkit-scrollbar-track { background: var(--bg-primary); }\n    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }\n    ::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }\n\n    /* ── Divider ── */\n    hr { border-color: var(--border) !important; margin: 8px 0 !important; }\n</style>\n'

@st.cache_resource
def load_graph():
    return build_graph()

def run_agent(user_input: str, graph, thread_id: str) -> dict:
    config = get_graph_config(thread_id)
    initial_state = {'user_query': user_input, 'messages': [], 'next_agent': '', 'analyst_output': '', 'news_output': '', 'portfolio_output': '', 'tool_calls_log': [], 'final_response': '', 'active_symbols': st.session_state.get('active_symbols', []), 'iteration_count': 0, 'routing_reasoning': '', 'agents_called': []}
    result = graph.invoke(initial_state, config=config)
    return result

def build_candlestick_chart(symbol: str) -> go.Figure:
    history = get_mock_price_history(symbol, days=30)
    fig = go.Figure(data=[go.Candlestick(x=[d['date'] for d in history], open=[d['open'] for d in history], high=[d['high'] for d in history], low=[d['low'] for d in history], close=[d['close'] for d in history], increasing_line_color='#00FF88', decreasing_line_color='#FF4466', increasing_fillcolor='rgba(0,255,136,0.3)', decreasing_fillcolor='rgba(255,68,102,0.3)')])
    fig.update_layout(height=200, margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17,24,39,0.8)', xaxis=dict(showgrid=True, gridcolor='#1F2937', color='#8892A4', showticklabels=True, tickfont=dict(size=9), rangeslider=dict(visible=False)), yaxis=dict(showgrid=True, gridcolor='#1F2937', color='#8892A4', tickfont=dict(size=9)), font=dict(color='#E2E8F0'), title=dict(text=f'{symbol} — 30 Day', font=dict(size=11, color='#8892A4'), x=0.5))
    return fig

def render_stock_card(symbol: str):
    data = get_mock_price(symbol)
    price = data['price']
    change = data['change']
    change_pct = data['change_pct']
    high_52w = data['high_52w']
    low_52w = data['low_52w']
    color = '#00FF88' if change >= 0 else '#FF4466'
    arrow = '▲' if change >= 0 else '▼'
    sign = '+' if change >= 0 else ''
    st.markdown(f'\n    <div style="background:#1A2235;border:1px solid #2D3748;border-radius:10px;padding:14px 16px;margin-bottom:10px;">\n        <div style="font-size:0.85rem;color:#8892A4;font-weight:600;letter-spacing:0.1em;">{symbol}</div>\n        <div style="font-size:1.6rem;font-weight:800;color:#E2E8F0;line-height:1.2;">${price:,.2f}</div>\n        <div style="font-size:0.88rem;color:{color};margin-top:2px;">\n            {arrow} {sign}{change:.2f} ({sign}{change_pct:.2f}%)\n        </div>\n    </div>\n    ', unsafe_allow_html=True)
    if high_52w > low_52w:
        range_pct = (price - low_52w) / (high_52w - low_52w)
        st.caption(f'52W Range  ${low_52w:,.0f} — ${high_52w:,.0f}')
        st.progress(float(min(max(range_pct, 0), 1)))
    fig = build_candlestick_chart(symbol)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='font-size:0.75rem;color:#8892A4;'>Market Cap</div><div style='font-size:0.85rem;color:#E2E8F0;font-weight:600;'>{data['market_cap']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.75rem;color:#8892A4;margin-top:8px;'>Volume</div><div style='font-size:0.85rem;color:#E2E8F0;font-weight:600;'>{data['volume']:,}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='font-size:0.75rem;color:#8892A4;'>P/E Ratio</div><div style='font-size:0.85rem;color:#E2E8F0;font-weight:600;'>{data['pe_ratio']}</div>", unsafe_allow_html=True)
        sentiment_color = '#00FF88'
        st.markdown(f"<div style='font-size:0.75rem;color:#8892A4;margin-top:8px;'>Sentiment</div><div style='font-size:0.85rem;color:{sentiment_color};font-weight:700;'>BULLISH</div>", unsafe_allow_html=True)

def extract_symbols_from_text(text: str) -> list:
    import re
    from utils.mock_data import BASE_PRICES
    known = list(BASE_PRICES.keys())
    found = []
    for sym in known:
        if re.search(f'\\b{sym}\\b', text.upper()):
            found.append(sym)
    return found

def main():
    st.markdown(BLOOMBERG_CSS, unsafe_allow_html=True)
    init_session_state()
    thread_id = get_or_create_thread_id()
    graph, _ = load_graph()
    pending_prompt = None
    left_col, center_col, right_col = st.columns([1, 2.5, 1.2], gap='medium')
    with left_col:
        st.markdown('<div class="section-header">📡 Watchlist</div>', unsafe_allow_html=True)
        search_sym = st.text_input('Search ticker', placeholder='e.g. AAPL', label_visibility='collapsed')
        if search_sym:
            sym_upper = search_sym.upper().strip()
            if st.button(f'Analyze {sym_upper}', key='search_analyze'):
                pending_prompt = f'Analyze {sym_upper} — give me a full technical and fundamental breakdown'
        st.markdown('<hr/>', unsafe_allow_html=True)
        WATCHLIST = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN']
        for sym in WATCHLIST:
            data = get_mock_price(sym)
            change_color = '#00FF88' if data['change'] >= 0 else '#FF4466'
            sign = '+' if data['change'] >= 0 else ''
            st.markdown(f"""\n            <div style="background:#111827;border:1px solid #1F2937;border-radius:6px;\n                        padding:8px 10px;margin:4px 0;">\n                <div style="display:flex;justify-content:space-between;align-items:center;">\n                    <span style="color:#00D4FF;font-weight:700;font-size:0.85rem;">{sym}</span>\n                    <span style="color:#E2E8F0;font-size:0.85rem;">${data['price']:,.2f}</span>\n                </div>\n                <div style="color:{change_color};font-size:0.75rem;margin-top:2px;">\n                    {sign}{data['change']:.2f} ({sign}{data['change_pct']:.2f}%)\n                </div>\n            </div>\n            """, unsafe_allow_html=True)
            if st.button(f'▶ {sym}', key=f'wl_{sym}', use_container_width=True):
                pending_prompt = f'Analyze {sym}'
        st.markdown('<hr/>', unsafe_allow_html=True)
        if st.button('🔄 New Session', use_container_width=True):
            clear_conversation()
            st.rerun()
        st.markdown(f"""\n        <div style="color:#4A5568;font-size:0.65rem;margin-top:10px;">\n            Session: {thread_id[:8]}...<br/>\n            Turns: {len([m for m in st.session_state.messages if m['role'] == 'user'])}\n        </div>\n        """, unsafe_allow_html=True)
    with center_col:
        st.markdown('\n        <div style="margin-bottom:12px;">\n            <div class="app-title">🤖 FinAgent</div>\n            <div class="app-subtitle">Multi-Agent Stock Analyst · LangGraph + LangChain + GPT-4o</div>\n        </div>\n        ', unsafe_allow_html=True)
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        with col_b1:
            if st.button('📈 Analyze NVDA', use_container_width=True):
                pending_prompt = 'Analyze NVDA — give me technical indicators, price action, and a buy/sell signal'
        with col_b2:
            if st.button('⚖️ AAPL vs MSFT', use_container_width=True):
                pending_prompt = 'Compare AAPL and MSFT — which is the better investment right now?'
        with col_b3:
            if st.button('💼 $10K Portfolio', use_container_width=True):
                pending_prompt = 'Help me build a diversified $10K portfolio with AAPL:5,MSFT:5,NVDA:3,AMZN:8,META:4'
        with col_b4:
            if st.button('📰 TSLA Sentiment', use_container_width=True):
                pending_prompt = "What's the latest news and market sentiment for TSLA?"
        st.markdown('<hr/>', unsafe_allow_html=True)
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                if msg['role'] == 'user':
                    st.markdown(f"""<div class="user-bubble">👤 {msg['content']}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="assistant-bubble">{msg['content']}</div>""", unsafe_allow_html=True)
                    meta = msg.get('metadata', {})
                    if meta.get('routing'):
                        with st.expander('🧠 Agent Routing & Reasoning', expanded=False):
                            routing = meta['routing']
                            agents = routing.get('route', [])
                            reasoning = routing.get('reasoning', '')
                            symbols = routing.get('symbols', [])
                            st.markdown(f"**Agents Activated:** `{'` · `'.join(agents)}`")
                            st.markdown(f"**Symbols Detected:** `{('` `'.join(symbols) if symbols else 'none')}`")
                            st.markdown(f'**Reasoning:** {reasoning}')
                    if meta.get('tool_calls'):
                        with st.expander(f"🔧 Tools Called ({len(meta['tool_calls'])})", expanded=False):
                            for call in meta['tool_calls']:
                                st.markdown(f"""\n                                <div style="background:#0F1928;border:1px solid #1F2937;border-radius:6px;\n                                            padding:8px 12px;margin:4px 0;font-size:0.8rem;">\n                                    <span style="color:#00D4FF;font-weight:700;">{call.get('tool', '?')}</span>\n                                    <span style="color:#8892A4;"> · Input: </span>\n                                    <span style="color:#E2E8F0;">{str(call.get('input', ''))[:80]}</span><br/>\n                                    <span style="color:#8892A4;font-size:0.75rem;">{call.get('output_summary', '')[:120]}</span>\n                                </div>\n                                """, unsafe_allow_html=True)
        user_input = st.chat_input('Ask about any stock, portfolio, or market trend...')
        final_prompt = user_input or pending_prompt
        if final_prompt:
            add_user_message(final_prompt)
            found_symbols = extract_symbols_from_text(final_prompt)
            if found_symbols:
                st.session_state.active_symbols = found_symbols
                st.session_state.focused_symbol = found_symbols[0]
            with st.spinner('🤖 FinAgent is analyzing...'):
                try:
                    result = run_agent(final_prompt, graph, thread_id)
                    final_response = result.get('final_response', '')
                    tool_calls = result.get('tool_calls_log', [])
                    agents_called = result.get('agents_called', [])
                    routing_info = {'route': agents_called, 'reasoning': result.get('routing_reasoning', ''), 'symbols': result.get('active_symbols', [])}
                    st.session_state.last_tool_calls = tool_calls
                    st.session_state.last_routing = routing_info
                    add_assistant_message(final_response, metadata={'routing': routing_info, 'tool_calls': tool_calls})
                except Exception as e:
                    error_msg = f'⚠️ An error occurred: {str(e)}\n\nPlease check your OPENAI_API_KEY in .env and try again.'
                    add_assistant_message(error_msg)
            st.rerun()
    with right_col:
        st.markdown('<div class="section-header">📊 Stock Detail</div>', unsafe_allow_html=True)
        focused = getattr(st.session_state, 'focused_symbol', None)
        if not focused and st.session_state.get('active_symbols'):
            focused = st.session_state.active_symbols[0]
        if not focused:
            focused = 'NVDA'
        render_stock_card(focused)
        active = st.session_state.get('active_symbols', [])
        if len(active) > 1:
            st.markdown('<div class="section-header" style="margin-top:12px;">Quick Switch</div>', unsafe_allow_html=True)
            for sym in active[:4]:
                if st.button(sym, key=f'switch_{sym}', use_container_width=True):
                    st.session_state.focused_symbol = sym
                    st.rerun()
if __name__ == '__main__':
    main()
