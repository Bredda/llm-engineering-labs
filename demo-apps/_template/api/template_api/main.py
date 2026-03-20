from fastapi import Depends, FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.config import get_stream_writer
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 
from typing import Annotated, TypedDict
from contextlib import asynccontextmanager
import json
import os
import logging
from dotenv import load_dotenv


logger = logging.getLogger("main")

# Load and check OPENAI_API_KEY env var presence
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY must be set in .env file")


# ── State ──────────────────────────────────────────────────────────────────────
class State(TypedDict):
    messages: Annotated[list, add_messages]

# ── Nodes ────────────────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True, api_key=SecretStr(api_key))

async def chat_node(state: State) -> State:
    """Single node: calls the LLM with the full conversation history."""
    full = None  # None | AIMessageChunk
    writer = get_stream_writer()
    # For each produced token (typed as AIMessageChunk):
        # 1. Aggregate chunks for full final response
        # 2. Use stream_writer to stream the token in a custom event 
    writer({"start": "completion"})
    async for chunk in llm.astream(state["messages"]):
        full = chunk if full is None else full + chunk
        writer({"token": chunk.text})
    return {"messages": [full]}

# ── Graph ────────────────────────────────────────────────────────────────

# Variable module-level, initialized at startup through server lifespan
# in order to wrap graph compilation in AsyncSqliteSaver connection context manager
graph: CompiledStateGraph | None = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
        graph = (
            StateGraph(State)
            .add_node("chat", chat_node)
            .add_edge(START, "chat")
            .add_edge("chat", END)
            .compile(checkpointer=checkpointer)
        )
        yield  # App runs here, SQLite conn is open
    # After yield : conn is gracefully stopped at shutdown

# ── API ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Chatbot Template", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_compiled_graph() -> CompiledStateGraph:
    assert graph is not None, "Graph not initialized"
    return graph

class ChatRequest(BaseModel):
    message: str    # New user message
    thread_id: str  # identifies the conversation (stored in SQLite)

@app.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
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

@app.get("/graph")
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

@app.get("/chat/{thread_id}/history")
async def get_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
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

@app.delete("/chat/{thread_id}")
async def clear_history(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
    """Clears a conversation by writing an empty state to the checkpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    await g.aupdate_state(config, {"messages": []}) # type: ignore
    return {"cleared": True}

@app.delete("/chat/{thread_id}/last")
async def delete_last_exchange(
    thread_id: str,
    g: CompiledStateGraph = Depends(get_compiled_graph)):
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

if os.getenv("SERVE_STATIC") == "true":
    app.mount("/", StaticFiles(directory="static", html=True), name="static")