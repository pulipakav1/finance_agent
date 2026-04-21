import uuid

import requests
import streamlit as st

from src.fin_platform.config import settings

API_BASE = settings.streamlit_api_base_url.rstrip("/")

st.set_page_config(page_title="Financial Intelligence Platform", layout="wide")


def health_ok() -> bool:
    try:
        return requests.get(f"{API_BASE}/health", timeout=2).ok
    except OSError:
        return False


def query_endpoint_available() -> bool:
    """Validate this API base serves the expected FinAgent routes."""
    try:
        resp = requests.get(f"{API_BASE}/openapi.json", timeout=3)
        if not resp.ok:
            return False
        paths = (resp.json() or {}).get("paths", {})
        return "/query" in paths
    except OSError:
        return False


def run_query(query: str, thread_id: str, history: list[dict[str, str]]) -> dict:
    payload = {
        "query": query,
        "thread_id": thread_id,
        "conversation_history": history,
        "session_metadata": {"ui_client": "streamlit"},
    }
    resp = requests.post(f"{API_BASE}/query", json=payload, timeout=45)
    if not resp.ok:
        raise RuntimeError(resp.text)
    return resp.json()


if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"streamlit-{uuid.uuid4()}"
if "history" not in st.session_state:
    st.session_state.history = []
if "responses" not in st.session_state:
    st.session_state.responses = []

st.markdown(
    """
    <style>
    .stApp { background-color: #0b0f18; color: #dce3ef; }
    .panel { border: 1px solid #202b3a; border-radius: 10px; padding: 12px; background: #101826; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Multi-Agent Financial Intelligence Platform")
st.caption(f"API base: `{API_BASE}`")

online = health_ok()
query_available = query_endpoint_available()
if not online:
    st.error(
        f"API offline at {API_BASE}. Start API and/or set STREAMLIT_API_BASE_URL."
    )
elif not query_available:
    st.error(
        f"Connected service at {API_BASE} does not expose `/query`. "
        "Point Streamlit to FinAgent API using STREAMLIT_API_BASE_URL."
    )

query = st.text_input("Ask market, news, or portfolio questions", placeholder="Example: What is NVDA trend and latest sentiment?")
if st.button("Run Analysis", type="primary", disabled=not (online and query_available)) and query.strip():
    with st.spinner("Routing across specialists..."):
        try:
            output = run_query(
                query,
                st.session_state.thread_id,
                st.session_state.history,
            )
        except RuntimeError as exc:
            st.error(
                f"Query failed: {exc}. "
                "Likely wrong API base URL. Set STREAMLIT_API_BASE_URL to the FinAgent server."
            )
            output = None
    if output:
        st.session_state.history.extend(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": output["executive_summary"]},
            ]
        )
        st.session_state.responses.append(output)

if st.session_state.responses:
    latest = st.session_state.responses[-1]
    st.subheader("Executive Summary")
    st.markdown(f"<div class='panel'>{latest['executive_summary']}</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Analyst")
        st.json(latest["specialist_outputs"].get("analyst", {"status": "not_routed_or_failed"}))
    with col2:
        st.markdown("#### News")
        st.json(latest["specialist_outputs"].get("news", {"status": "not_routed_or_failed"}))
    with col3:
        st.markdown("#### Portfolio")
        st.json(latest["specialist_outputs"].get("portfolio", {"status": "not_routed_or_failed"}))

    st.subheader("Routing and Diagnostics")
    m = latest.get("metadata", {})
    st.write(f"Routes: `{', '.join(m.get('route_coverage', []))}`")
    st.write(f"Latency: `{m.get('latency_ms', 'n/a')} ms` | Completeness: `{m.get('completeness', 'n/a')}`")
    if latest.get("warnings"):
        st.warning("Warnings: " + " | ".join(latest["warnings"]))

st.subheader("Conversation History")
for item in st.session_state.history[-12:]:
    st.write(f"**{item['role']}**: {item['content']}")
