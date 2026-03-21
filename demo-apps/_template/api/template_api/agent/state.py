from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict


# ── State ──────────────────────────────────────────────────────────────────────
class State(TypedDict):
    messages: Annotated[list, add_messages]