import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from langgraph.graph.state import CompiledStateGraph, RunnableConfig
from ..dependencies import get_rag_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    repo_url: str


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    g: CompiledStateGraph = Depends(get_rag_graph),
):
    config = RunnableConfig(configurable={"thread_id": req.thread_id})
    input_state = {
        "messages": [HumanMessage(content=req.message)],
        "repo_url": req.repo_url,
    }

    async def event_generator():
        try:
            async for event in g.astream(
                input=input_state,
                config=config,
                stream_mode="custom",
            ):
                event_type = event.get("type")

                if event_type == "retrieving":
                    # UI shows a "Searching codebase…" spinner
                    yield sse({"type": "retrieving", "message": event["message"]})

                elif event_type == "retrieved":
                    # UI shows the list of retrieved nodes (collapsed by default)
                    yield sse({"type": "retrieved", "hits": event["hits"]})

                elif event_type == "token":
                    yield sse({"type": "token", "content": event["content"]})

            yield sse({"type": "done"})

        except Exception as e:
            logger.exception("Stream error")
            yield sse({"type": "error", "content": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{thread_id}/history")
async def get_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_rag_graph),
):
    config = RunnableConfig(configurable={"thread_id": thread_id})
    state = await g.aget_state(config)

    if not state or not state.values:
        return {"messages": []}

    messages = []
    for msg in state.values.get("messages", []):
        if msg.type == "human":
            messages.append({"type": "human", "content": msg.content})
        elif msg.type == "ai" and msg.content:
            messages.append({"type": "ai", "content": msg.content})

    return {"messages": messages}


@router.delete("/{thread_id}")
async def clear_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_rag_graph),
):
    config = RunnableConfig(configurable={"thread_id": thread_id})
    await g.aupdate_state(config, {"messages": []})
    return {"cleared": True}