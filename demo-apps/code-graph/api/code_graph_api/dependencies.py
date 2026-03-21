
from code_graph_api.agents.rag import RagGraph


def set_rag_graph(g: RagGraph) -> None:
    global _rag_graph
    _rag_graph = g

async def get_rag_graph() -> RagGraph:
    assert _rag_graph is not None, "Graph not initialized"
    return _rag_graph