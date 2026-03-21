from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 
from contextlib import asynccontextmanager
import os
import logging
from .dependencies import set_graph
from template_api.agent import build_graph
from template_api.routers import chat_router

logger = logging.getLogger("main")


# ── Graph ────────────────────────────────────────────────────────────────

# Variable module-level, initialized at startup through server lifespan
# in order to wrap graph compilation in AsyncSqliteSaver connection context manager
graph: CompiledStateGraph | None = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
        set_graph(build_graph(checkpointer))
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

app.include_router(chat_router)

if os.getenv("SERVE_STATIC") == "true":
    app.mount("/", StaticFiles(directory="static", html=True), name="static")