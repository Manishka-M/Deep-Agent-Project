from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.tools import search_tool


def planner_node(state: AgentState):

    query = state["query"].lower()

    search_keywords = [
        "latest",
        "news",
        "current",
        "today",
        "recent"
    ]

    need_search = any(
        word in query
        for word in search_keywords
    )

    return {
        "plan": f"Plan for: {state['query']}",
        "need_search": need_search
    }


def route_after_planner(state: AgentState):

    if state["need_search"]:
        return "researcher"

    return "responder"


def research_node(state: AgentState):

    result = search_tool(state["query"])

    summaries = []

    for item in result["results"]:
        summaries.append(
            f"{item['title']}\n{item['content'][:200]}"
        )

    return {
        "research": "\n\n".join(summaries)
    }


def response_node(state: AgentState):

    if state["research"]:

        answer = f"""
Query:
{state['query']}

Research Findings:
{state['research']}
"""

    else:

        answer = f"""
Query:
{state['query']}

No web search required.
Answer generated directly.
"""

    return {
        "answer": answer
    }


builder = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("researcher", research_node)
builder.add_node("responder", response_node)

builder.add_edge(START, "planner")

builder.add_conditional_edges(
    "planner",
    route_after_planner
)

builder.add_edge("researcher", "responder")
builder.add_edge("responder", END)

graph = builder.compile()
