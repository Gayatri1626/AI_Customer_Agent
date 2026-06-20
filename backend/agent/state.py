"""
LangGraph agent state definition.
"""
from typing import Annotated, Any
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Conversation messages (human + AI + tool results)
    messages: Annotated[list, add_messages]
    # Resolved customer data (populated after lookup)
    customer: dict | None
    # Order being discussed
    order: dict | None
    # Final decision: "approved", "denied", or None (pending)
    decision: str | None
    # Reason for the decision
    decision_reason: str | None
    # Session ID for streaming reasoning logs
    session_id: str
