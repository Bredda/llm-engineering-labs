from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 
from contextlib import asynccontextmanager
import os
import logging

from code_graph_api.routers import  index_router, graph_router, chat_router
from code_graph_api.dependencies import set_rag_graph
from code_graph_api.agents import build_rag_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s"
)

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
        set_rag_graph(build_rag_graph(checkpointer))
        yield

# ── API ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Code Graph", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index_router)
app.include_router(graph_router)
app.include_router(chat_router)

if os.getenv("SERVE_STATIC") == "true":
    app.mount("/", StaticFiles(directory="static", html=True), name="static")