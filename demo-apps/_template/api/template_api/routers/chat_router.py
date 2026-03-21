from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi import Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
import json
import logging
from template_api.dependencies import get_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str    # New user message
    thread_id: str  # identifies the conversation (stored in SQLite)

@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    g: CompiledStateGraph = Depends(get_graph)):
    """
    Streams the LLM response token by token via Server-Sent Events.

    The thread_id is passed as LangGraph config so the checkpointer
    can restore and persist the conversation history automatically.
    """
    config = {"configurable": {"thread_id": req.thread_id}}
    input_state = {"messages": [HumanMessage(content=req.message)]}

    async def event_generator():
        try:
            async for event in g.astream(
                input=input_state,
                stream_mode="custom", 
                config=config,  # type: ignore
                ):
                # If custom stream event has key token 
                # propagate token in SSE payload format
                logger.info("event: %r", event)
                if (
                    event.get("token", None) is not None
                ):
                    # SSE format: data: <payload>\n\n
                    yield f"data: {json.dumps({'token': event.get("token", None)})}\n\n"
            # Yield a final SSE payload to signal the end of the stream to client
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.get("/graph")
async def get_graph_img(
    g: CompiledStateGraph = Depends(get_graph)):
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
    g: CompiledStateGraph = Depends(get_graph)):
    """
    Returns the full message history for a thread from the SQLite checkpoint.
    Called on page load to restore the current session.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = await g.aget_state(config) # type: ignore

    if not state or not state.values:
        return {"messages": []}

    messages = []
    for msg in state.values.get("messages", []):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        messages.append({"role": role, "content": msg.content})

    return {"messages": messages}

@router.delete("/{thread_id}")
async def clear_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_graph)):
    """Clears a conversation by writing an empty state to the checkpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    await g.aupdate_state(config, {"messages": []}) # type: ignore
    return {"cleared": True}

@router.delete("/{thread_id}/last")
async def delete_last_exchange(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_graph)):
    """
    Removes the last user+assistant exchange from the checkpoint.
    Called before re-sending an edited message so the checkpoint
    doesn't accumulate the original exchange.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = await g.aget_state(config)  # type: ignore
 
    if not state or not state.values:
        return {"ok": True}
 
    msgs = state.values.get("messages", [])
 
    # Walk back from the end : drop the last assistant msg (if any)
    # and the last user msg
    trimmed = list(msgs)
    if trimmed and trimmed[-1].type == "ai":
        trimmed.pop()
    if trimmed and trimmed[-1].type == "human":
        trimmed.pop()
 
    # Overwrite state — RemoveMessage is the canonical LangGraph way
    # but rewriting the full list is simpler and safe for a single-node graph
    await g.aupdate_state(config, {"messages": trimmed})  # type: ignore
    return {"ok": True}