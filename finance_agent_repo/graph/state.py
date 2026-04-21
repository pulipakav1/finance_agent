from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    next_agent: str
    analyst_output: str
    news_output: str
    portfolio_output: str
    tool_calls_log: list
    final_response: str
    active_symbols: list
    iteration_count: int
    routing_reasoning: str
    agents_called: list
