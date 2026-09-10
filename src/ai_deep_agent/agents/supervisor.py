"""
Supervisor — the full cognitive engine.
Orchestrates planning, routing, execution, critic evaluation,
retry loop, and final answer. Calls the rich console at every step.
"""
from __future__ import annotations
import time
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from ai_deep_agent.agents.critic   import evaluate_task
from ai_deep_agent.agents.planner  import run_planner
from ai_deep_agent.agents.search   import run_search
from ai_deep_agent.agents.research import run_research
from ai_deep_agent.agents.math     import run_math
from ai_deep_agent.agents.coding   import run_coding
from ai_deep_agent.agents.writer   import run_writer
from ai_deep_agent.llms.factory    import get_llm
from ai_deep_agent.memory.virtual_fs import workspace
from ai_deep_agent.state.state     import AgentState
import ai_deep_agent.display.console as ui

def _x(resp) -> str:
    """Extract text from LLM response (handles Gemini list format)."""
    c = resp.content
    if isinstance(c, list):
        return " ".join(p.get("text","") if isinstance(p,dict) else str(p) for p in c).strip()
    return str(c).strip()



MAX_RETRIES = 2

ROUTER_PROMPT = """
You are the Supervisor Router of an autonomous deep-research AI system.

Choose the single best worker for the assigned task:

  search   – retrieve current information, real-world facts, events, data from the web
  research – analyse, synthesise, compare, and reason over already-gathered information
  math     – solve mathematical, algebraic, statistical, or quantitative problems
  coding   – write, design, debug, or explain code, algorithms, implementations
  writer   – produce the polished final report or document synthesis

Decision guide:
  • If the task requires FINDING information → search
  • If search results already exist AND the task is to ANALYSE/COMPARE → research
  • If the task involves NUMBERS, ALGEBRA, STATISTICS → math
  • If the task involves CODE, ALGORITHMS, SOFTWARE → coding
  • If ALL research is done AND a final REPORT is needed → writer

Return ONLY one word: search | research | math | coding | writer
No punctuation, no explanation.
"""

_router_llm = get_llm(role="supervisor")

DISPATCH = {
    "search":   run_search,
    "research": run_research,
    "math":     run_math,
    "coding":   run_coding,
    "writer":   run_writer,
}


def _route(task: str, ctx_summary: str = "") -> str:
    msg = task
    if ctx_summary:
        msg += f"\n\nWorkspace so far: {ctx_summary[:300]}"
    response = _router_llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=f"Task:\n{msg}"),
    ])
    worker = _x(response).lower().rstrip(".")
    return worker if worker in DISPATCH else "research"


def run_supervisor(state: AgentState) -> AgentState:
    log:     list[dict] = state.get("execution_log", [])
    sources: list[dict] = state.get("sources", [])
    retries: dict       = state.get("retry_counts", {})

    # -------- PLANNING --------
    if not state.get("planning_complete", False):
        workspace.clear()
        todos = run_planner(state["user_query"])
        state.update({
            "todos":             todos,
            "planning_complete": True,
            "completed_tasks":   [],
            "writer_used":       False,
        })
        ui.planner_done(todos)
        log.append({"event": "planner_done", "tasks": [t["task"] for t in todos]})

    todos           = state.get("todos", [])
    completed_tasks = state.get("completed_tasks", [])
    completed_ids   = {t["id"] for t in completed_tasks}

    # -------- EXECUTE EACH TASK --------
    for todo in todos:
        if todo["id"] in completed_ids:
            continue

        task_id   = todo["id"]
        task_desc = todo["task"]
        ctx_sum   = workspace.build_context()[:200]   # brief context hint for router
        worker    = _route(task_desc, ctx_sum)

        ui.task_start(task_id, len(todos), task_desc, worker)
        log.append({"event": "task_start", "id": task_id, "worker": worker, "task": task_desc})

        attempt         = 0
        previous_output = ""
        feedback        = ""
        accepted_result = None
        final_review    = None

        while attempt <= MAX_RETRIES:
            # --- Run worker ---
            out    = DISPATCH[worker](
                task=task_desc, task_id=task_id,
                feedback=feedback, previous_output=previous_output,
            )
            result = out["result"]
            ui.worker_result(worker, result, attempt)

            # Accumulate sources
            for src in out.get("sources", []):
                if src not in sources:
                    sources.append(src)

            if out.get("writer_used"):
                state["writer_used"] = True

            # --- Critic ---
            review = evaluate_task(task_desc, result, agent_type=worker)
            log.append({"event": "critic", "id": task_id, "review": review})

            if review["decision"] == "pass":
                ui.critic_pass(review["reason"], review.get("strengths", []))
                accepted_result = result
                final_review    = review
                break
            else:
                ui.critic_fail(
                    review["reason"],
                    review.get("missing", []),
                    review.get("revision_instructions", []),
                )

            if attempt >= MAX_RETRIES:
                ui.max_retries_hit(task_id)
                accepted_result = result
                final_review    = review
                break

            feedback        = "; ".join(
                review.get("revision_instructions", []) or [review.get("reason", "")]
            )
            previous_output = result
            attempt        += 1
            retries[task_id] = attempt
            ui.retry_notice(attempt, MAX_RETRIES, feedback)
            log.append({"event": "retry", "id": task_id, "attempt": attempt, "feedback": feedback})

        # Mark complete
        retries_done = retries.get(task_id, 0)
        ui.task_accepted(task_id, worker, retries_done)
        completed_tasks.append({
            "id":      task_id,
            "task":    task_desc,
            "worker":  worker,
            "result":  accepted_result,
            "review":  final_review,
            "retries": retries_done,
        })
        log.append({"event": "task_complete", "id": task_id, "retries": retries_done})

    # -------- FINAL ANSWER --------
    if state.get("writer_used") and workspace.exists("final_report.md"):
        final_answer = workspace.read("final_report.md")
    else:
        final_answer = completed_tasks[-1]["result"] if completed_tasks else "No result."

    state.update({
        "completed_tasks": completed_tasks,
        "final_answer":    final_answer,
        "execution_log":   log,
        "sources":         sources,
        "retry_counts":    retries,
    })
    return state
