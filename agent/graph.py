from langgraph.graph import StateGraph, START, END
from agent.state import AgentState


def first_node(state: AgentState):
    return {
        "message": state["message"] + " -> processed"
    }


builder = StateGraph(AgentState)

builder.add_node("first_node", first_node)

builder.add_edge(START, "first_node")
builder.add_edge("first_node", END)

graph = builder.compile()