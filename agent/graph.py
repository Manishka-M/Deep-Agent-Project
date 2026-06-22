from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.tools import search_tool
from agent.llm import llm
from agent.memory import save_notes
from reports.report_writer import save_report
from agent.critic import critique_report




def planner_node(state: AgentState):

    prompt = f"""
You are a research planning agent.

Break the following request into 4-6 research tasks.

Return ONLY the tasks.

Request:
{state['query']}
"""

    response = llm.invoke(prompt)

    tasks = []

    for line in response.content.split("\n"):

        line = line.strip()

        if not line:
            continue

        line = line.lstrip("1234567890.- ")

        tasks.append(
            {
                "task": line,
                "status": "pending"
            }
        )

    return {
        "plan": "Research plan generated",
        "todos": tasks
    }


def execute_todo_node(state: AgentState):

    todos = state["todos"]

    pending_task = None

    for todo in todos:

        if todo["status"] == "pending":
            pending_task = todo
            break

    if pending_task is None:
        return {
            "notes": state["notes"]
        }

    print(
        "Executing:",
        pending_task["task"]
    )

    result = search_tool(
        pending_task["task"]
    )

    summary = ""

    for item in result["results"][:3]:

        summary += (
            item["title"]
            + "\n"
            + item["content"][:200]
            + "\n\n"
        )

    pending_task["status"] = "completed"

    updated_notes = state["notes"] + [
        {
            "task": pending_task["task"],
            "content": summary
        }
    ]
    save_notes(updated_notes)

    return {
        "todos": todos,
        "notes": updated_notes
    }


def should_continue(state: AgentState):

    for todo in state["todos"]:

        if todo["status"] == "pending":
            return "executor"

    return "responder"


def response_node(state: AgentState):

    notes_text = ""

    for note in state["notes"]:

        notes_text += (
            f"Task: {note['task']}\n"
            f"Research:\n{note['content']}\n\n"
        )

    prompt = f"""
You are a professional research analyst.

Using the research notes below,
write a structured report.

Include:

1. Introduction
2. Key Findings
3. Challenges
4. Future Outlook
5. Conclusion

Research Notes:

{notes_text}
"""

    response = llm.invoke(prompt)

    report_path = save_report(
    response.content
)

    return {
    "answer": response.content
    + f"\n\nReport saved to: {report_path}"
}


def critic_node(state: AgentState):

    review = critique_report(
        state["answer"]
    )

    return {
        "critique": review
    }




builder = StateGraph(AgentState)


builder.add_node("planner", planner_node)
builder.add_node("executor", execute_todo_node)
builder.add_node("responder", response_node)
builder.add_node(
    "critic",
    critic_node
)


builder.add_edge(START, "planner")

builder.add_edge(
    "planner",
    "executor"
)

builder.add_conditional_edges(
    "executor",
    should_continue
)

builder.add_edge("responder", "critic")
builder.add_edge("critic", END)

graph = builder.compile()