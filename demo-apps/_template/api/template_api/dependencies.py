
from template_api.agent import ChatGraph


def set_graph(g: ChatGraph) -> None:
    global _rag_graph
    _rag_graph = g

async def get_graph() -> ChatGraph:
    assert _rag_graph is not None, "Graph not initialized"
    return _rag_graph