from src.fin_platform.aggregation import aggregate_state
from src.fin_platform.state import AnalystOutput, PlatformState, SupervisorDecision


def test_aggregation_partial_failure() -> None:
    state: PlatformState = {
        "request_id": "r1",
        "thread_id": "t1",
        "route_coverage": ["analyst", "news"],
        "supervisor_decision": SupervisorDecision(routes=["analyst", "news"], ticker="AAPL", confidence=0.7),
        "analyst_output": AnalystOutput(
            ticker="AAPL",
            technical_trend="up",
            price_movement_summary="up 1%",
            indicator_explanation="sma20>sma50",
            confidence=0.8,
        ),
        "specialist_errors": {"news": "timeout"},
    }
    out = aggregate_state(state)
    assert "analyst" in out.specialist_outputs
    assert any("news failed" in w for w in out.warnings)
    assert out.metadata["completeness"] == 0.5
