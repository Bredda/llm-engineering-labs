
from fastapi import APIRouter, HTTPException
from ..indexer.cloner import repo_id
from ..indexer.kuzu_graph import get_nodes, get_edges, is_indexed
 
router = APIRouter(prefix="/graph", tags=["graph"])
 
 
@router.get("/nodes")
async def graph_nodes(repo_url: str) -> list[dict]:
    rid = repo_id(repo_url)
    if not is_indexed(rid):
        raise HTTPException(404, "Repo not indexed")
    return get_nodes(rid)
 
 
@router.get("/edges")
async def graph_edges(repo_url: str) -> list[dict]:
    rid = repo_id(repo_url)
    if not is_indexed(rid):
        raise HTTPException(404, "Repo not indexed")
    return get_edges(rid)
 