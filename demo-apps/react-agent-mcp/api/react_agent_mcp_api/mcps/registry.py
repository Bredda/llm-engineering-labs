import asyncio
import json
import os
import re
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient  , StreamableHttpConnection
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from typing import Any
import logging

logger = logging.getLogger(__name__)

MCPS_PATH = Path("mcps.json")



class McpEntry(BaseModel):
    id: str
    name: str
    description: str
    url: str
    # Resolved headers (env vars substituted) — not exposed to the client
    headers: dict[str, str] = {}
    error: str | None = None


# ── Registry (module-level, built at lifespan) ────────────────────────────────

_registry: dict[str, McpEntry] = {}


def _resolve_headers(headers: dict[str, str]) -> dict[str, str]:
    resolved = {}
    for key, value in headers.items():
        def replace(match: re.Match) -> str:
            var = match.group(1)
            val = os.getenv(var)
            if val is None:
                raise ValueError(f"Environment variable '{var}' not set")
            return val
        resolved[key] = re.sub(r'\$\{([^}]+)\}', replace, value)
    return resolved


async def fetch_mcps_tools(mcps_ids: list[str]) -> list[BaseTool]:
    """Fetches tools for a single entry and updates it in place."""
    mcps = get_by_ids(mcps_ids)
    config: dict[str, StreamableHttpConnection] = (
        { mcp.id: StreamableHttpConnection(transport= "streamable_http", url = mcp.url, headers=mcp.headers)  
            for mcp in mcps })
    try:
        client = MultiServerMCPClient(config) # type: ignore
        return await client.get_tools()
    except Exception as e:

        logger.error("Failed fetching tools", e)
        raise RuntimeError("Failed fetching tools from mcps")
        


async def build_registry() -> None:
    """
    Called once at lifespan startup.
    Loads mcps.json, resolves headers, fetches tools from all servers concurrently.
    """
    logger.info(f"Building MCP registry" )    
    if not MCPS_PATH.exists():
        raise FileNotFoundError(f"mcps.json not found at {MCPS_PATH.resolve()}")
    global _registry

    raw: dict = json.loads(MCPS_PATH.read_text())
    entries = []
    for item in raw.get("items", []):

        try:
            headers = _resolve_headers(item.get("headers", {}))
        except ValueError as e:
            # Missing env var — mark as error, still add to registry
            entry = McpEntry(**{**item, "headers": {}}, error=str(e))
            _registry[entry.id] = entry
            continue

        entry = McpEntry(**{**item, "headers": headers})
        _registry[entry.id] = entry
        entries.append(entry)

    logger.info(f"Registered {len(_registry.keys())} MCPs" )    

# ── Public accessors ──────────────────────────────────────────────────────────

def get_all() -> list[McpEntry]:
    return list(_registry.values())


def get_by_ids(ids: list[str]) -> list[McpEntry]:
    missing = [i for i in ids if i not in _registry]
    if missing:
        raise ValueError(f"Unknown MCP id(s): {', '.join(missing)}")
    return [_registry[i] for i in ids]


def build_fastmcp_config(ids: list[str]) -> dict:
    """
    Builds a fastmcp multi-server config for the given MCP ids.
    Raises ValueError if any id is unknown or had a config error.
    """
    entries = get_by_ids(ids)

    errored = [e for e in entries if e.error]
    if errored:
        raise ValueError(
            f"MCP server(s) not available: "
            + ", ".join(f"{e.id} ({e.error})" for e in errored)
        )

    return {
        "mcpServers": {
            e.id: {"transport": "http", "url": e.url, "headers": e.headers}
            for e in entries
        }
    }