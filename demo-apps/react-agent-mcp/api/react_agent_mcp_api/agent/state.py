from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict
from dataclasses import dataclass
from typing import List
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

@dataclass
class AgentContextSchema:
    tools: List[BaseTool]
    model_name: str


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


ReactAgentGraph = CompiledStateGraph[AgentState, AgentContextSchema, AgentState, AgentState]