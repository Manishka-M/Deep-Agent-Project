"""
Supervisor Agent — orchestrates planning, routing, execution.
v4-fix:
  - Keyword-based routing (no LLM router = no rate-limit, no mis-routing)
  - Critic ONLY on writer output (not every task)
  - Truncated context passing (saves tokens)
"""
from langchain_core.messages import HumanMessage, SystemMessage

from ai_deep_agent.agents.planner  import run_planner
from ai_deep_agent.agents.search   import run_search
from ai_deep_agent.agents.research import run_research
from ai_deep_agent.agents.math     import run_math
from ai_deep_agent.agents.coding   import run_coding
from ai_deep_agent.agents.writer   import run_writer
from ai_deep_agent.agents.critic   import run_critic
from ai_deep_agent.state.state     import AgentState

# ------------------------------------------------------------------ #
#  Dispatch table                                                      #
# ------------------------------------------------------------------ #
DISPATCH = {
    "search":   run_search,
    "research": run_research,
    "math":     run_math,
    "coding":   run_coding,
    "writer":   run_writer,
}

# ------------------------------------------------------------------ #
#  Keyword-based router  (zero LLM calls = no rate-limiting)          #
# ------------------------------------------------------------------ #
def _route(task: str) -> str:
    t = task.lower()

    if any(w in t for w in [
        "calculat", "mathemat", "equation", "integral",
        "derivat", "statistic", "probabilit", "formula",
        "comput numer", "algebra", "trigon",
    ]):
        return "math"

    if any(w in t for w in [
        "code", "program", "script", "implement",
        "debug", "function", "algorithm", "software", "develop",
    ]):
        return "coding"

    if any(w in t for w in [
        "write", "draft", "synthesize", "compile",
        "final report", "comprehensive report", "structured report",
        "combine all", "integrate findings",
    ]):
        return "writer"

    if any(w in t for w in [
        "analys", "evaluat", "assess", "examin",
        "investigat", "interpret", "framework", "strateg",
        "impact", "implication", "compar", "critiqu",
    ]):
        return "research"

    return "search"


# ------------------------------------------------------------------ #
#  Main supervisor                                                     #
# ------------------------------------------------------------------ #
def run_supervisor(state: AgentState) -> AgentState:
    log:     list[dict] = state.get("execution_log", [])
    sources: list[dict] = state.get("sources", [])
    retries: dict       = state.get("retry_counts", {})

    # -------- PLANNING PHASE --------
    if not state.get("planning_complete", False):
        todos = run_planner(state["user_query"])
        return {
            **state,
            "todos": todos,
            "planning_complete": True,
            "execution_log": log,
        }

    # -------- FIND NEXT PENDING TASK --------
    todos   = state.get("todos", [])
    pending = [t for t in todos if t.get("status") == "pending"]
    if not pending:
        return {**state, "all_tasks_complete": True}

    todo      = pending[0]
    task_id   = todo["id"]
    task_desc = todo["task"]

    # Pass only a short summary of previous work (saves tokens)
    ctx_sum = "\n".join(
        f"- Task {e['task_id']} [{e['worker']}]: {e['task'][:60]}... ✓"
        for e in log[-2:]   # only last 2 completed tasks
    )

    # -------- ROUTE (keyword-based, no LLM) --------
    worker = _route(task_desc)

    # -------- RECOVER PREVIOUS ATTEMPT IF RETRY --------
    prev_out = next(
        (e.get("result", "") for e in reversed(log) if e.get("task_id") == task_id),
        "",
    )
    feedback = next(
        (e.get("feedback", "") for e in reversed(log) if e.get("task_id") == task_id),
        "",
    )

    # -------- EXECUTE WORKER --------
    out     = DISPATCH[worker](task_desc, task_id, feedback=feedback, previous_output=prev_out)
    result  = out.get("result", "")
    sources.extend(out.get("sources", []))

    # -------- CRITIC  (writer output only) --------
    verdict, feedback_text = "PASS", ""
    if worker == "writer":
        raw = run_critic(result, task_desc)
        # critic may return a tuple or a string
        if isinstance(raw, tuple):
            verdict, feedback_text = raw
        else:
            verdict = "PASS" if "pass" in str(raw).lower() else "FAIL"
            feedback_text = str(raw)

    # -------- UPDATE STATE --------
    retry_key   = str(task_id)
    retry_count = retries.get(retry_key, 0)

    log_entry = {
        "task_id": task_id, "task": task_desc,
        "worker": worker, "result": result,
        "verdict": verdict, "feedback": feedback_text,
    }

    # Retry writer once on FAIL
    if worker == "writer" and verdict == "FAIL" and retry_count < 1:
        retries[retry_key] = retry_count + 1
        updated_todos = [
            {**t, "status": "pending"} if t["id"] == task_id else t
            for t in todos
        ]
        return {
            **state,
            "todos": updated_todos,
            "execution_log": log + [log_entry],
            "sources": sources,
            "retry_counts": retries,
        }

    # Mark task done
    updated_todos = [
        {**t, "status": "done"} if t["id"] == task_id else t
        for t in todos
    ]
    all_done     = all(t["status"] == "done" for t in updated_todos)
    final_report = result if worker == "writer" else state.get("final_report", "")

    return {
        **state,
        "todos": updated_todos,
        "execution_log": log + [log_entry],
        "sources": sources,
        "retry_counts": retries,
        "all_tasks_complete": all_done,
        "final_report": final_report,
    }
