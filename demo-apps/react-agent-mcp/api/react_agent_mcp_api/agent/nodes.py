import asyncio
from typing import Literal
from pydantic import SecretStr
from langchain.messages import ToolMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from .state import AgentState, AgentContextSchema
from react_agent_mcp_api.config import api_key
# ── Nodes ────────────────────────────────────────────────────────────────


async def llm_call(state: AgentState, runtime: Runtime[AgentContextSchema]) -> AgentState:
    """Calls the LLM with the full conversation history, streaming tokens."""
    llm = ChatOpenAI(name = runtime.context.model_name, streaming=True, api_key=SecretStr(api_key))
    llm_with_tools = llm.bind_tools(runtime.context.tools)
    
    full = None  # None | AIMessageChunk
    writer = get_stream_writer()
    # For each produced token (typed as AIMessageChunk):
        # 1. Aggregate chunks for full final response
        # 2. Use stream_writer to stream the token in a custom event 
    async for chunk in llm_with_tools.astream(state["messages"]):
        full = chunk if full is None else full + chunk
        writer({"token": chunk.text})
    return {"messages": [full]}

async def _execute_single_tool(tool_call: dict, tools: list[BaseTool]) -> ToolMessage:
    """Executes a single tool call, returns a ToolMessage."""
    tool = next(
        (tool for tool in tools if tool.name == tool_call["name"]),
        None
    )
    if tool is None:
        observation = f"No tool found named {tool_call["name"]}. Please double check your tool call"
    else:
        observation = await tool.ainvoke(tool_call["args"])
    message = ToolMessage(content=observation, tool_call_id=tool_call["id"])
    return message

async def tool_node(state: AgentState, runtime: Runtime[AgentContextSchema]):
    """
    Executes all tool calls in parallel, then streams ordered events.
 
    SSE event sequence per tool call:
      1. tool_start  { name }                     
      2. tool_call   { id, name, args, result }
 
    tool_call events are emitted in the original tool_calls order (not asyncio.gather order)
    so the client can rely on ordering without reconciliation.
    """
    writer = get_stream_writer()
    tool_calls = state["messages"][-1].tool_calls
    original_order = [tc["id"] for tc in tool_calls]
    for tc in tool_calls:
        writer({"tool_start": {"name": tc["name"]}})

    results: list[ToolMessage] = await asyncio.gather(*[
        _execute_single_tool(tool_call, runtime.context.tools)
        for tool_call in tool_calls
    ])
    results_by_id = {msg.tool_call_id: msg for msg in results}
    ordered_results = [results_by_id[tc_id] for tc_id in original_order]
    # Emit tool_done events in order, each carrying the full reconciled payload
    args_by_id = {tc["id"]: {"name": tc["name"], "args": tc["args"]} for tc in tool_calls}
    for msg in ordered_results:
        meta = args_by_id[msg.tool_call_id]
        writer({
            "tool_call": {
                "id": msg.tool_call_id,
                "name": meta["name"],
                "args": meta["args"],
                "result": msg.content,
            }
        })
 
    return {"messages": ordered_results}

def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """Routes to tool_node if the LLM made tool calls, otherwise ends."""
    return "tool_node" if state["messages"][-1].tool_calls else "__end__"
