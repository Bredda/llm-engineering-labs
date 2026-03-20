from fastapi import Depends, Response, APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph, RunnableConfig
import json
import logging

from react_agent_mcp_api.mcps import fetch_mcps_tools
from react_agent_mcp_api.agent.state import ReactAgentGraph, AgentState, AgentContextSchema

logger = logging.getLogger("Agent router" \
"")
from react_agent_mcp_api.dependencies import get_compiled_graph

class AgentRequest(BaseModel):
    message: str    # New user message
    thread_id: str  # identifies the conversation (stored in SQLite)
    tool_ids: List[str]



router = APIRouter(prefix="/agent", tags=["mcps"])

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"

@router.post("/stream")
async def chat_stream(
    req: AgentRequest,
    g: ReactAgentGraph = Depends(get_compiled_graph)):
    """
    Streams the LLM response token by token via Server-Sent Events.

    The thread_id is passed as LangGraph config so the checkpointer
    can restore and persist the conversation history automatically.
    """
    tools =  await fetch_mcps_tools(req.tool_ids)

    config = RunnableConfig(configurable={"thread_id": req.thread_id})
    context= AgentContextSchema(tools=tools, model_name="")
    input = AgentState(messages= [HumanMessage(content=req.message)])

    async def event_generator():
        try:
            async for event in g.astream(
                input=input,
                stream_mode="custom", 
                context=context,
                config=config,
                ):
                # If custom stream event has key token 
                # propagate token in SSE payload format
                # SSE format: data: <payload>\n\n
                print("event: %r", event)
                if "token" in event:
                    yield _sse({"type": "token", "content": event["token"]})
 
                elif "tool_start" in event:
                    yield _sse({"type": "tool_start", "name": event["tool_start"]["name"]})
 
                elif "tool_call" in event:
                    yield _sse({"type": "tool_call", **event["tool_call"]})
            # Yield a final SSE payload to signal the end of the stream to client
            yield _sse({"type": "done"})

        except Exception as e:
            logger.exception("Stream error")
            yield _sse({"type": "error", "content": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.get("/graph")
async def get_graph_img(
    g: CompiledStateGraph = Depends(get_compiled_graph)):
    """
    Returns the png mermaid representation of the graph
    """
    from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
    image_bytes = g.get_graph().draw_mermaid_png(
        curve_style=CurveStyle.NATURAL,
        node_colors=NodeStyles(first="#baffc9", last="#baffc9", default="#ffdfba"),
        wrap_label_n_words=9,
        output_file_path=None,
        draw_method=MermaidDrawMethod.PYPPETEER,
        background_color="#0c0a0b",
        padding=10,
    )
    return Response(content=image_bytes, media_type="image/png")

@router.get("/{thread_id}/history")
async def get_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
    """
    Serializes the full message history from the SQLite checkpoint.
 
    Message types returned:
      { type: "human",   content }
      { type: "ai",      content }
      { type: "tool_call", id, name, args, result }   ← reconciled tool call+result pair
 
    AIMessages that only contain tool_calls (no content) are skipped —
    they are represented by their associated tool_done entries instead.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = await g.aget_state(config) # type: ignore

    if not state or not state.values:
        return {"messages": []}

    raw_messages = state.values.get("messages", [])
 
    # Index ToolMessages by tool_call_id for reconciliation
    tool_results: dict[str, ToolMessage] = {
        msg.tool_call_id: msg
        for msg in raw_messages
        if isinstance(msg, ToolMessage)
    }
 
    serialized = []
    for msg in raw_messages:
        match msg.type:
            case "human":
                serialized.append({"type": "human", "content": msg.content})
            case "ai":
                if msg.content:
                    # Intermediate or final text response
                    serialized.append({"type": "ai", "content": msg.content})
                if msg.tool_calls:
                    # Reconcile each tool call with its result
                    for tc in msg.tool_calls:
                        result_msg = tool_results.get(tc["id"])
                        serialized.append({
                            "type": "tool_call",
                            "id": tc["id"],
                            "name": tc["name"],
                            "args": tc["args"],
                            "result": result_msg.content if result_msg else None,
                        })
 
            case "tool":
                # Already handled via ai.tool_calls reconciliation above
                pass

    return {"messages": serialized}

@router.delete("/{thread_id}")
async def clear_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
    """Clears a conversation by writing an empty state to the checkpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    await g.aupdate_state(config, {"messages": []}) # type: ignore
    return {"cleared": True}

@router.delete("/{thread_id}/last")
async def delete_last_exchange(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
    """
    Removes the last user exchange (human + all following ai/tool messages)
    from the checkpoint.
    """
    config = RunnableConfig(configurable={"thread_id": thread_id})
    state = await g.aget_state(config)  # type: ignore
 
    if not state or not state.values:
        return {"ok": True}
 
    msgs = state.values.get("messages", [])
 
    # Walk back until we find and remove the last human message
    # and everything after it (ai + tool messages from that turn)
    while msgs and msgs[-1].type != "human":
        msgs.pop()
    if msgs and msgs[-1].type == "human":
        msgs.pop()
 
    await g.aupdate_state(config, {"messages": msgs})
    return {"ok": True}
