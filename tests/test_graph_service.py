from src.fin_platform.graph import FinancialIntelligenceGraph


def test_graph_invoke_returns_structured_response() -> None:
    graph = FinancialIntelligenceGraph()
    out = graph.invoke(
        query="Analyze AAPL trend and sentiment",
        thread_id="test-thread",
        conversation_history=[{"role": "user", "content": "hello"}],
    )
    assert "executive_summary" in out
    assert "specialist_outputs" in out
    assert "metadata" in out
