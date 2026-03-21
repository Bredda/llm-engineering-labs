from langgraph.graph import StateGraph, START, END

from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from .nodes import chat_node
from .state import State

ChatGraph = CompiledStateGraph[State, None, State, State]

def build_graph(checkpointer: BaseCheckpointSaver):
    return ( StateGraph(State)
            .add_node("chat", chat_node)
            .add_edge(START, "chat")
            .add_edge("chat", END)
            .compile(checkpointer=checkpointer))