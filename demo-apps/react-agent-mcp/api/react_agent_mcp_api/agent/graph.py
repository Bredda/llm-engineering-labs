from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from .state import ReactAgentGraph, AgentState, AgentContextSchema
from .nodes import llm_call, tool_node, should_continue


def build_graph(checkpointer: BaseCheckpointSaver) -> ReactAgentGraph:
    return (
        StateGraph(AgentState, context_schema=AgentContextSchema )
        .add_node("llm_call", llm_call)
        .add_node("tool_node", tool_node)

        .add_edge("__start__", "llm_call")
        .add_conditional_edges(
            "llm_call",
            should_continue,
            ["tool_node", "__end__"]
        )
        .add_edge("tool_node", "llm_call")
        .compile(checkpointer=checkpointer)
    )