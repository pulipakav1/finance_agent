from langchain_core.messages import AIMessage
from graph.graph_builder import route_from_supervisor
from graph import nodes


def test_route_from_supervisor_defaults_to_analyst():
    result = route_from_supervisor({'next_agent': 'unknown'})
    assert result == ['analyst_node']


def test_route_from_supervisor_supports_parallel_targets():
    result = route_from_supervisor({'next_agent': 'analyst,news'})
    assert result == ['analyst_node', 'news_node']


def test_aggregator_node_single_agent_bypasses_llm():
    state = {'agents_called': ['news'], 'news_output': 'News summary', 'analyst_output': '', 'portfolio_output': '', 'user_query': ''}
    result = nodes.aggregator_node(state)
    assert result['final_response'] == 'News summary'
    assert isinstance(result['messages'][0], AIMessage)
