from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState
from graph.nodes import supervisor_node, analyst_node, news_node, portfolio_node, aggregator_node

def route_from_supervisor(state: AgentState) -> list[str]:
    routing = state.get('next_agent', 'analyst')
    agents = [a.strip() for a in routing.split(',')]
    node_map = {'analyst': 'analyst_node', 'news': 'news_node', 'portfolio': 'portfolio_node'}
    next_nodes = [node_map[a] for a in agents if a in node_map]
    return next_nodes if next_nodes else ['analyst_node']

def build_graph() -> tuple:
    graph = StateGraph(AgentState)
    graph.add_node('supervisor_node', supervisor_node)
    graph.add_node('analyst_node', analyst_node)
    graph.add_node('news_node', news_node)
    graph.add_node('portfolio_node', portfolio_node)
    graph.add_node('aggregator_node', aggregator_node)
    graph.set_entry_point('supervisor_node')
    graph.add_conditional_edges('supervisor_node', route_from_supervisor, {'analyst_node': 'analyst_node', 'news_node': 'news_node', 'portfolio_node': 'portfolio_node'})
    graph.add_edge('analyst_node', 'aggregator_node')
    graph.add_edge('news_node', 'aggregator_node')
    graph.add_edge('portfolio_node', 'aggregator_node')
    graph.add_edge('aggregator_node', END)
    checkpointer = MemorySaver()
    compiled = graph.compile(checkpointer=checkpointer)
    return (compiled, checkpointer)
