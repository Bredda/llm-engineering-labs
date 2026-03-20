from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 
from contextlib import asynccontextmanager
import os
import logging

from react_agent_mcp_api.mcps import build_registry, mcp_router
from react_agent_mcp_api.agent import build_graph, agent_router
from react_agent_mcp_api.dependencies import set_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s"
)

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    await build_registry()  
    async with AsyncSqliteSaver.from_conn_string("react_agent_mcp_checkpoints.sqlite") as checkpointer:
        set_graph(build_graph(checkpointer))  # type: ignore
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


app.include_router(mcp_router)
app.include_router(agent_router)

if os.getenv("SERVE_STATIC") == "true":
    app.mount("/", StaticFiles(directory="static", html=True), name="static")