"""
LangGraph agent graph — ReAct-style agent for refund processing.
"""
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from agent.state import AgentState
from agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are a professional AI Customer Support Agent for ShopEase, an e-commerce platform.
Your job is to handle refund requests efficiently by:
1. Identifying the customer — if the user gives a customer ID (e.g. C001) call lookup_customer immediately.
2. Their lookup response contains order IDs — call get_order_details with the first order ID right away.
3. Call validate_refund_eligibility with that order ID — do NOT call get_refund_policy unless the case is ambiguous.
4. Based on the eligibility result, call approve_refund or deny_refund immediately.
5. Then write a short, empathetic reply to the customer explaining the decision.

Speed matters: skip steps you don't need. If the customer gives you both a customer ID and describes the issue clearly, go straight to validate_refund_eligibility after the order lookup — don't fetch the policy text unless you're unsure.

Always be polite and transparent. When denying, cite the policy section. When approving, state the refund amount, method, and 5–7 business day timeline.
Always use approve_refund or deny_refund to finalise — never just say the decision in text without calling the tool."""


def build_graph() -> StateGraph:
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        streaming=True,
        api_key=os.environ["OPENAI_API_KEY"],
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    def agent_node(state: AgentState):
        messages = state["messages"]
        # Prepend system message if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # If the LLM called a tool, route to tool_node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Singleton compiled graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
