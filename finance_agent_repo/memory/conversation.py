import uuid
import streamlit as st

def get_or_create_thread_id() -> str:
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    return st.session_state.thread_id

def get_graph_config(thread_id: str) -> dict:
    return {'configurable': {'thread_id': thread_id}}

def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if 'active_symbols' not in st.session_state:
        st.session_state.active_symbols = []
    if 'last_tool_calls' not in st.session_state:
        st.session_state.last_tool_calls = []
    if 'last_routing' not in st.session_state:
        st.session_state.last_routing = {}
    if 'watchlist_prices' not in st.session_state:
        st.session_state.watchlist_prices = {}

def add_user_message(content: str):
    st.session_state.messages.append({'role': 'user', 'content': content})

def add_assistant_message(content: str, metadata: dict=None):
    st.session_state.messages.append({'role': 'assistant', 'content': content, 'metadata': metadata or {}})

def clear_conversation():
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.active_symbols = []
    st.session_state.last_tool_calls = []
    st.session_state.last_routing = {}
