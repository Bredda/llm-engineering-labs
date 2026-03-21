"""
POST /index        { repo_url }  → SSE progress stream
GET  /index/status { repo_url }  → { status: indexed|indexing|not_found }
"""
import asyncio
import json
import logging
from enum import Enum

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from code_graph_api.indexer.cloner import clone_or_pull, repo_id, is_cloned
from code_graph_api.indexer.parser import parse_repo
from code_graph_api.indexer.kuzu_graph import ingest, is_indexed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/index", tags=["index"])

# Track repos currently being indexed (in-memory, single process)
_indexing: set[str] = set()


class IndexStatus(str, Enum):
    indexed  = "indexed"
    indexing = "indexing"
    not_found = "not_found"


class IndexRequest(BaseModel):
    repo_url: str


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.post("")
async def index_repo(req: IndexRequest) -> StreamingResponse:
    """
    Clones, parses and ingests a repo into Kuzu.
    Streams progress events so the UI can show a live status.

    SSE events:
      { type: "progress", step: "cloning"|"parsing"|"ingesting", message: "..." }
      { type: "done",     repo_id: "..." }
      { type: "error",    message: "..." }
    """
    rid = repo_id(req.repo_url)

    async def run():
        try:
            _indexing.add(rid)

            # ── Clone ────────────────────────────────────────────────────────
            yield sse({"type": "progress", "step": "cloning",
                        "message": f"Cloning {req.repo_url}…"})
            path = await asyncio.to_thread(clone_or_pull, req.repo_url)

            # ── Parse ────────────────────────────────────────────────────────
            yield sse({"type": "progress", "step": "parsing",
                        "message": "Parsing source files…"})
            result = await asyncio.to_thread(parse_repo, path, rid)
            yield sse({"type": "progress", "step": "parsing",
                        "message": f"Found {len(result.nodes)} nodes, {len(result.edges)} edges"})

            # ── Ingest ───────────────────────────────────────────────────────
            yield sse({"type": "progress", "step": "ingesting",
                        "message": "Ingesting into graph database…"})
            await asyncio.to_thread(ingest, rid, result)

            yield sse({"type": "done", "repo_id": rid,
                        "stats": {"nodes": len(result.nodes), "edges": len(result.edges)}})

        except Exception as e:
            logger.exception("Indexing failed for %s", req.repo_url)
            yield sse({"type": "error", "message": str(e)})
        finally:
            _indexing.discard(rid)

    return StreamingResponse(
        run(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/status")
async def index_status(repo_url: str) -> dict:
    rid = repo_id(repo_url)
    if rid in _indexing:
        return {"status": IndexStatus.indexing, "repo_id": rid}
    if is_indexed(rid):
        return {"status": IndexStatus.indexed, "repo_id": rid}
    return {"status": IndexStatus.not_found, "repo_id": rid}