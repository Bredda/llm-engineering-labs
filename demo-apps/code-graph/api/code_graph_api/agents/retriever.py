"""
Hybrid retriever: vector search + Cypher graph traversal.

Vector search  → finds semantically similar functions/files
Cypher queries → enriches with structural context (callers, callees, imports)
"""
import logging
from dataclasses import dataclass

import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from ..indexer.kuzu_graph import get_nodes, query as kuzu_query

logger = logging.getLogger(__name__)

# In-memory FAISS index per repo_id
_vector_stores: dict[str, FAISS] = {}


# ── Vector index ──────────────────────────────────────────────────────────────

def build_vector_index(repo_id: str, embeddings: OpenAIEmbeddings) -> FAISS:
    """Builds a FAISS index from all Function and File nodes in the graph."""
    nodes = get_nodes(repo_id)
    docs = [
        Document(
            page_content=f"{n['type']} {n['name']}\n{n.get('content', '')}",
            metadata={"id": n["id"], "type": n["type"], "name": n["name"], "file": n["file"]},
        )
        for n in nodes
        if n["type"] in ("Function", "Class", "File")
    ]
    if not docs:
        raise ValueError(f"No indexable nodes found for repo {repo_id}")

    store = FAISS.from_documents(docs, embeddings)
    _vector_stores[repo_id] = store
    logger.info("Built vector index with %d docs for repo %s", len(docs), repo_id)
    return store


def get_or_build_vector_index(repo_id: str, embeddings: OpenAIEmbeddings) -> FAISS:
    if repo_id not in _vector_stores:
        return build_vector_index(repo_id, embeddings)
    return _vector_stores[repo_id]


# ── Cypher enrichment ─────────────────────────────────────────────────────────

def _get_callers(repo_id: str, node_id: str) -> list[dict]:
    """Who calls this function?"""
    return kuzu_query(
        repo_id,
        """
        MATCH (caller:CodeNode)-[:CALLS]->(fn:CodeNode {id: $id})
        RETURN caller.id AS id, caller.name AS name, caller.file AS file
        LIMIT 10
        """,
        {"id": node_id},
    )


def _get_callees(repo_id: str, node_id: str) -> list[dict]:
    """What does this function call?"""
    return kuzu_query(
        repo_id,
        """
        MATCH (fn:CodeNode {id: $id})-[:CALLS]->(callee:CodeNode)
        RETURN callee.id AS id, callee.name AS name, callee.file AS file
        LIMIT 10
        """,
        {"id": node_id},
    )


def _get_file_symbols(repo_id: str, file_id: str) -> list[dict]:
    """All symbols defined in a file."""
    return kuzu_query(
        repo_id,
        """
        MATCH (f:CodeNode {id: $id})-[:DEFINES]->(sym:CodeNode)
        RETURN sym.id AS id, sym.type AS type, sym.name AS name, sym.start_line AS start_line
        ORDER BY sym.start_line
        LIMIT 30
        """,
        {"id": file_id},
    )


def _get_imports(repo_id: str, file_id: str) -> list[dict]:
    """What does this file import?"""
    return kuzu_query(
        repo_id,
        """
        MATCH (f:CodeNode {id: $id})-[:IMPORTS]->(dep:CodeNode)
        RETURN dep.id AS id, dep.name AS name
        LIMIT 20
        """,
        {"id": file_id},
    )


# ── Main retrieval ────────────────────────────────────────────────────────────

@dataclass
class RetrievalContext:
    query: str
    vector_hits: list[dict]        # top-k similar nodes
    graph_context: list[dict]      # structural enrichment per hit
    formatted: str                 # ready-to-inject string for the LLM


def retrieve(
    query: str,
    repo_id: str,
    embeddings: OpenAIEmbeddings,
    top_k: int = 5,
) -> RetrievalContext:
    store = get_or_build_vector_index(repo_id, embeddings)

    # ── Vector search ─────────────────────────────────────────────────────────
    hits = store.similarity_search(query, k=top_k)
    vector_hits = [
        {"id": h.metadata["id"], "type": h.metadata["type"],
         "name": h.metadata["name"], "file": h.metadata["file"],
         "content": h.page_content}
        for h in hits
    ]

    # ── Graph enrichment per hit ──────────────────────────────────────────────
    graph_context = []
    for hit in vector_hits:
        node_id = hit["id"]
        node_type = hit["type"]
        enrichment: dict = {"node": hit}

        if node_type == "Function":
            enrichment["callers"] = _get_callers(repo_id, node_id)
            enrichment["callees"] = _get_callees(repo_id, node_id)
        elif node_type == "File":
            enrichment["defines"] = _get_file_symbols(repo_id, node_id)
            enrichment["imports"] = _get_imports(repo_id, node_id)

        graph_context.append(enrichment)

    # ── Format for LLM ────────────────────────────────────────────────────────
    sections = []
    for ctx in graph_context:
        node = ctx["node"]
        lines = [f"### {node['type']}: `{node['name']}` ({node['file']})"]
        lines.append(node["content"])

        if callers := ctx.get("callers"):
            lines.append("**Called by:** " + ", ".join(f"`{c['name']}`" for c in callers))
        if callees := ctx.get("callees"):
            lines.append("**Calls:** " + ", ".join(f"`{c['name']}`" for c in callees))
        if defines := ctx.get("defines"):
            lines.append("**Defines:** " + ", ".join(f"`{s['name']}`" for s in defines))
        if imports := ctx.get("imports"):
            lines.append("**Imports:** " + ", ".join(f"`{i['name']}`" for i in imports))

        sections.append("\n".join(lines))

    formatted = "\n\n---\n\n".join(sections)
    return RetrievalContext(
        query=query,
        vector_hits=vector_hits,
        graph_context=graph_context,
        formatted=formatted,
    )