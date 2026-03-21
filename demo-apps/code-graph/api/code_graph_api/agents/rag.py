"""
LangGraph RAG chain for codebase Q&A.

Graph:
  START → retrieve → llm_call → END

The retrieve node runs the hybrid retriever and injects context
into the state. The llm_call node streams the response.
"""
import logging
from typing import Annotated, TypedDict
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from pydantic import SecretStr

from code_graph_api.config import api_key
from code_graph_api.agents.retriever import RetrievalContext, retrieve
from code_graph_api.indexer.cloner import repo_id as make_repo_id

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert software engineer assistant.
You answer questions about a codebase using the retrieved context below.
Always reference specific file paths and function names in your answers.
If the context doesn't contain enough information, say so clearly.

Retrieved context:
{context}
"""

@dataclass
class RagContextSchema:
    model_name: str
    embeddings_model: str

# ── State ──────────────────────────────────────────────────────────────────────

class RAGState(TypedDict):
    messages: Annotated[list, add_messages]
    repo_url: str
    retrieval_context: str   # formatted context injected into system prompt

RagGraph = CompiledStateGraph[RAGState, RagContextSchema, RAGState, RAGState]

# ── Nodes ──────────────────────────────────────────────────────────────────────


async def retrieve_node(state: RAGState, runtime: Runtime[RagContextSchema]):
    writer = get_stream_writer()
    query = state["messages"][-1].content
    repo_id = make_repo_id(state["repo_url"])

    writer({"type": "retrieving", "message": "Searching codebase…"})
    embeddings = OpenAIEmbeddings(model=runtime.context.embeddings_model)
    import asyncio
    ctx: RetrievalContext = await asyncio.to_thread(
        retrieve, query, repo_id, embeddings
    )

    writer({
        "type": "retrieved",
        "hits": [
            {"name": h["name"], "type": h["type"], "file": h["file"]}
            for h in ctx.vector_hits
        ],
    })

    return {"retrieval_context": ctx.formatted}



async def llm_call(state: RAGState, runtime: Runtime[RagContextSchema]):
    writer = get_stream_writer()
    llm = ChatOpenAI(name = runtime.context.model_name, streaming=True, api_key=SecretStr(api_key))
    system = SystemMessage(content=SYSTEM_PROMPT.format(
        context=state.get("retrieval_context", "")
    ))
    messages = [system] + state["messages"]
    llm = ChatOpenAI(name = runtime.context.model_name, streaming=True, api_key=SecretStr(api_key))
    full = None
    async for chunk in llm.astream(messages):
        full = chunk if full is None else full + chunk
        if chunk.content:
            writer({"type": "token", "content": chunk.content})

    return {"messages": [full]}



# ── Graph factory ──────────────────────────────────────────────────────────────

def build_graph(
    checkpointer: BaseCheckpointSaver,
) -> RagGraph:

    return (
        StateGraph(RAGState, context_schema=RagContextSchema)
        .add_node("retrieve", retrieve_node)
        .add_node("llm", llm_call)
        .add_edge(START, "retrieve")
        .add_edge("retrieve", "llm")
        .add_edge("llm", END)
        .compile(checkpointer=checkpointer)
    )