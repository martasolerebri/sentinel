from datetime import date

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import ALL_TOOLS

memory = MemorySaver()

_graph_cache: dict = {}

def _build_system_prompt() -> str:
    today = date.today()
    weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][today.weekday()]
    date_str = today.strftime("%d %B %Y")

    return (
        f"You are a smart, friendly personal finance assistant — think of yourself like Cleo, "
        f"but focused on data and insight rather than chat. "
        f"Today is {weekday}, {date_str}. "
        f"Always use £ (GBP) when referring to amounts. "
        f"When the user asks about their finances, always use the available tools — never invent numbers. "
        f"Be concise, direct, and human. Lead with the most important insight first. "
        f"If something looks unusual or worth flagging (e.g. an anomaly, overspending in a category), "
        f"mention it briefly without being preachy. "
        f"If the user asks what date/day it is, answer directly without using a tool."
    )

NODE_LLM   = "llm"
NODE_TOOLS = "tools"

def build_graph(api_key: str):
    """
    Builds and compiles the LangGraph agent.
    Cached per API key — compiled once, reused on subsequent requests.
    """
    if api_key in _graph_cache:
        return _graph_cache[api_key]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        google_api_key=api_key,
    ).bind_tools(ALL_TOOLS)

    def llm_node(state: AgentState) -> dict:
        system = SystemMessage(content=_build_system_prompt())
        response = llm.invoke([system] + state["messages"])
        return {"messages": [response]}

    def should_use_tool(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return NODE_TOOLS
        return END

    builder = StateGraph(AgentState)
    builder.add_node(NODE_LLM, llm_node)
    builder.add_node(NODE_TOOLS, ToolNode(ALL_TOOLS))
    builder.set_entry_point(NODE_LLM)
    builder.add_conditional_edges(
        NODE_LLM,
        should_use_tool,
        {NODE_TOOLS: NODE_TOOLS, END: END},
    )
    builder.add_edge(NODE_TOOLS, NODE_LLM)

    compiled = builder.compile(checkpointer=memory)
    _graph_cache[api_key] = compiled
    return compiled