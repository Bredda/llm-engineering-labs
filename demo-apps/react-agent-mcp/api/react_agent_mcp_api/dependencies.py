from react_agent_mcp_api.agent.state import ReactAgentGraph
# Populated by main.py at startup via set_graph()
_graph: ReactAgentGraph | None = None

def set_graph(g: ReactAgentGraph) -> None:
    global _graph
    _graph = g

def get_compiled_graph() -> ReactAgentGraph:
    assert _graph is not None, "Graph not initialized"
    return _graph