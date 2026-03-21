from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from template_api.config import api_key
from .state import State

# ── Nodes ────────────────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True, api_key=SecretStr(api_key))

async def chat_node(state: State) -> State:
    """Single node: calls the LLM with the full conversation history."""
    full = None  # None | AIMessageChunk
    writer = get_stream_writer()
    # For each produced token (typed as AIMessageChunk):
        # 1. Aggregate chunks for full final response
        # 2. Use stream_writer to stream the token in a custom event 
    writer({"start": "completion"})
    async for chunk in llm.astream(state["messages"]):
        full = chunk if full is None else full + chunk
        writer({"token": chunk.text})
    return {"messages": [full]}