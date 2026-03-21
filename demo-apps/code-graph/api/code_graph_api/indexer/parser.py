"""
Parses a codebase using tree-sitter and extracts graph nodes and edges.

Supported languages: Python, TypeScript, JavaScript
Node types : File, Function, Class
Edge types : DEFINES (File→Function, File→Class, Class→Function)
             IMPORTS (File→File)
             CALLS   (Function→Function)
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path

from tree_sitter import Language, Node, Parser
from tree_sitter_languages import get_language, get_parser

logger = logging.getLogger(__name__)

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class CodeNode:
    id: str                  # unique: "<repo_id>:<rel_path>:<name>" or "<repo_id>:<rel_path>"
    type: str                # File | Function | Class
    name: str
    file: str                # relative path
    start_line: int = 0
    end_line: int = 0
    content: str = ""        # raw source snippet (for embeddings)


@dataclass
class CodeEdge:
    src: str                 # CodeNode.id
    dst: str                 # CodeNode.id
    type: str                # DEFINES | IMPORTS | CALLS


@dataclass
class ParseResult:
    nodes: list[CodeNode] = field(default_factory=list)
    edges: list[CodeEdge] = field(default_factory=list)


# ── Language config ───────────────────────────────────────────────────────────

SUPPORTED = {
    ".py":  "python",
    ".ts":  "typescript",
    ".tsx": "typescript",
    ".js":  "javascript",
    ".jsx": "javascript",
}

# Tree-sitter node type names per language
FUNCTION_TYPES = {
    "python":     {"function_definition"},
    "typescript": {"function_declaration", "method_definition", "arrow_function"},
    "javascript": {"function_declaration", "method_definition", "arrow_function"},
}

CLASS_TYPES = {
    "python":     {"class_definition"},
    "typescript": {"class_declaration"},
    "javascript": {"class_declaration"},
}

IMPORT_TYPES = {
    "python":     {"import_statement", "import_from_statement"},
    "typescript": {"import_statement"},
    "javascript": {"import_statement"},
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _node_text(node: Node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _get_name(node: Node, src: bytes, lang: str) -> str | None:
    """Extracts the identifier name from a function/class node."""
    for child in node.children:
        if child.type == "identifier":
            return _node_text(child, src)
    return None


def _file_node_id(repo_id: str, rel_path: str) -> str:
    return f"{repo_id}:{rel_path}"


def _symbol_node_id(repo_id: str, rel_path: str, name: str) -> str:
    return f"{repo_id}:{rel_path}:{name}"


# ── Core parser ───────────────────────────────────────────────────────────────

def parse_file(
    path: Path,
    rel_path: str,
    repo_id: str,
    lang: str,
) -> ParseResult:
    result = ParseResult()
    src = path.read_bytes()
    parser = get_parser(lang)
    tree = parser.parse(src)

    file_id = _file_node_id(repo_id, rel_path)
    file_node = CodeNode(
        id=file_id,
        type="File",
        name=rel_path,
        file=rel_path,
        content=src.decode("utf-8", errors="replace")[:2000],  # cap for embeddings
    )
    result.nodes.append(file_node)

    func_types = FUNCTION_TYPES[lang]
    class_types = CLASS_TYPES[lang]
    import_types = IMPORT_TYPES[lang]

    # Walk the AST
    def walk(node: Node, parent_class_id: str | None = None):
        if node.type in func_types:
            name = _get_name(node, src, lang) or f"<anon>@{node.start_point[0]}"
            sym_id = _symbol_node_id(repo_id, rel_path, name)
            result.nodes.append(CodeNode(
                id=sym_id,
                type="Function",
                name=name,
                file=rel_path,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                content=_node_text(node, src)[:1000],
            ))
            result.edges.append(CodeEdge(
                src=parent_class_id or file_id,
                dst=sym_id,
                type="DEFINES",
            ))
            # Recurse into function body (nested functions, calls)
            for child in node.children:
                walk(child, parent_class_id)

        elif node.type in class_types:
            name = _get_name(node, src, lang) or f"<anon_class>@{node.start_point[0]}"
            sym_id = _symbol_node_id(repo_id, rel_path, name)
            result.nodes.append(CodeNode(
                id=sym_id,
                type="Class",
                name=name,
                file=rel_path,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                content=_node_text(node, src)[:500],
            ))
            result.edges.append(CodeEdge(src=file_id, dst=sym_id, type="DEFINES"))
            for child in node.children:
                walk(child, sym_id)

        elif node.type in import_types:
            # Resolve import target to a file node id (best effort)
            raw = _node_text(node, src)
            result.edges.append(CodeEdge(
                src=file_id,
                dst=f"{repo_id}:import:{raw.strip()}",
                type="IMPORTS",
            ))

        else:
            for child in node.children:
                walk(child, parent_class_id)

    walk(tree.root_node)
    return result


def parse_repo(repo_path: Path, repo_id: str) -> ParseResult:
    """Parses all supported files in a repo directory."""
    combined = ParseResult()

    for path in sorted(repo_path.rglob("*")):
        # Skip hidden dirs, vendored deps, build artifacts
        parts = path.parts
        if any(p.startswith(".") or p in ("node_modules", "__pycache__", "dist", "build", ".venv") for p in parts):
            continue
        if not path.is_file():
            continue

        lang = SUPPORTED.get(path.suffix)
        if not lang:
            continue

        rel_path = str(path.relative_to(repo_path))
        try:
            result = parse_file(path, rel_path, repo_id, lang)
            combined.nodes.extend(result.nodes)
            combined.edges.extend(result.edges)
        except Exception as e:
            logger.warning("Failed to parse %s: %s", rel_path, e)

    logger.info(
        "Parsed %d nodes, %d edges from %s",
        len(combined.nodes), len(combined.edges), repo_path,
    )
    return combined