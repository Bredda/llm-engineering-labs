from pathlib import Path

from fastapi import APIRouter
from .registry import get_all, McpEntry

router = APIRouter(prefix="/mcps", tags=["mcps"])

# mcps.json lives next to this file
MCPS_PATH = Path(__file__).parent / "mcps.json"

# ── Route ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[McpEntry])
async def list_mcps() -> list[McpEntry]:
    """
    Returns all configured MCP servers with their live tool list.
    Unreachable servers are returned with tools=[] and a non-null error field.
    """

    return get_all()