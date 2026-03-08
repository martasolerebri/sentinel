from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class AgentState(TypedDict):
    """State that travels through the LangGraph agent graph."""
    messages: Annotated[list, add_messages]