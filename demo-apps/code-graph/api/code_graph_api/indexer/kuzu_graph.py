"""
Kuzu graph database layer.

Schema
──────
Nodes : CodeNode(id STRING, type STRING, name STRING, file STRING,
                 start_line INT64, end_line INT64, content STRING)
Edges : DEFINES(CodeNode→CodeNode)
        IMPORTS(CodeNode→CodeNode)
        CALLS  (CodeNode→CodeNode)

One Kuzu database per repo, stored under .kuzu/<repo_id>/
"""
import logging
from pathlib import Path

import kuzu

from .parser import CodeEdge, CodeNode, ParseResult

logger = logging.getLogger(__name__)

KUZU_ROOT = Path(".kuzu")


def db_path(repo_id: str) -> Path:
    return KUZU_ROOT / repo_id


def is_indexed(repo_id: str) -> bool:
    return db_path(repo_id).exists()


def get_db(repo_id: str) -> kuzu.Database:
    return kuzu.Database(str(db_path(repo_id)))


def _init_schema(conn: kuzu.Connection) -> None:
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS CodeNode (
            id     STRING PRIMARY KEY,
            type   STRING,
            name   STRING,
            file   STRING,
            start_line INT64,
            end_line   INT64,
            content    STRING
        )
    """)
    for rel in ("DEFINES", "IMPORTS", "CALLS"):
        conn.execute(f"""
            CREATE REL TABLE IF NOT EXISTS {rel} (
                FROM CodeNode TO CodeNode
            )
        """)


def ingest(repo_id: str, result: ParseResult) -> None:
    """
    Creates (or recreates) the Kuzu DB for this repo and ingests
    all nodes and edges from the parse result.
    """
    path = db_path(repo_id)
    path.mkdir(parents=True, exist_ok=True)

    db = kuzu.Database(str(path))
    conn = kuzu.Connection(db)
    _init_schema(conn)

    # Deduplicate nodes by id
    seen_ids: set[str] = set()
    unique_nodes: list[CodeNode] = []
    for node in result.nodes:
        if node.id not in seen_ids:
            seen_ids.add(node.id)
            unique_nodes.append(node)

    # Insert nodes in batches
    logger.info("Ingesting %d nodes", len(unique_nodes))
    for node in unique_nodes:
        conn.execute(
            """
            MERGE (n:CodeNode {id: $id})
            SET n.type = $type, n.name = $name, n.file = $file,
                n.start_line = $start_line, n.end_line = $end_line,
                n.content = $content
            """,
            {
                "id": node.id,
                "type": node.type,
                "name": node.name,
                "file": node.file,
                "start_line": node.start_line,
                "end_line": node.end_line,
                "content": node.content,
            },
        )

    # Insert edges — skip if src or dst not in seen_ids
    logger.info("Ingesting %d edges", len(result.edges))
    for edge in result.edges:
        if edge.src not in seen_ids or edge.dst not in seen_ids:
            continue
        try:
            conn.execute(
                f"""
                MATCH (a:CodeNode {{id: $src}}), (b:CodeNode {{id: $dst}})
                MERGE (a)-[:{edge.type}]->(b)
                """,
                {"src": edge.src, "dst": edge.dst},
            )
        except Exception as e:
            logger.debug("Edge skipped (%s→%s): %s", edge.src, edge.dst, e)

    logger.info("Kuzu ingest complete for repo %s", repo_id)


def get_nodes(repo_id: str) -> list[dict]:
    """Returns all nodes for Cytoscape rendering."""
    conn = kuzu.Connection(get_db(repo_id))
    result = conn.execute(
        "MATCH (n:CodeNode) RETURN n.id, n.type, n.name, n.file, n.start_line, n.end_line"
    )
    rows = []
    while result.has_next():
        r = result.get_next()
        rows.append({
            "id": r[0], "type": r[1], "name": r[2],
            "file": r[3], "start_line": r[4], "end_line": r[5],
        })
    return rows


def get_edges(repo_id: str) -> list[dict]:
    """Returns all edges for Cytoscape rendering."""
    rows = []
    conn = kuzu.Connection(get_db(repo_id))
    for rel in ("DEFINES", "IMPORTS", "CALLS"):
        try:
            result = conn.execute(
                f"MATCH (a:CodeNode)-[r:{rel}]->(b:CodeNode) RETURN a.id, b.id, '{rel}'"
            )
            while result.has_next():
                r = result.get_next()
                rows.append({"src": r[0], "dst": r[1], "type": r[2]})
        except Exception:
            pass
    return rows


def query(repo_id: str, cypher: str, params: dict | None = None) -> list[dict]:
    """Generic Cypher query for the RAG retriever."""
    conn = kuzu.Connection(get_db(repo_id))
    result = conn.execute(cypher, params or {})
    rows = []
    while result.has_next():
        rows.append(dict(zip(result.get_column_names(), result.get_next())))
    return rows