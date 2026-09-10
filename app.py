"""
AI Deep-Agent v3  —  Streamlit Web Interface
=============================================
Runs the full autonomous agent pipeline in a browser.
Deploy to Streamlit Cloud for a shareable portfolio URL.

Local dev:  streamlit run app.py
"""
import sys, os, time, threading, queue
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

# ------------------------------------------------------------------ #
#  Page config  (must be first Streamlit call)                        #
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="AI-AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  Load secrets / env                                                 #
# ------------------------------------------------------------------ #
def _load_secrets():
    """Pull keys from Streamlit Cloud secrets or fall back to .env file."""
    for key in ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "GEMINI_API_KEY",
                "GEMINI_MODEL", "GEMINI_ROLES", "TAVILY_API_KEY"]:
        if key in st.secrets and not os.environ.get(key):
            os.environ[key] = st.secrets[key]

try:
    _load_secrets()
except Exception:
    # st.secrets not configured — fall back to .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

# ------------------------------------------------------------------ #
#  Sidebar                                                            #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4616/4616013.png", width=64)
    st.title("AI-AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS")
    st.caption("Deep-Research · Long Horizon Tasks · Autonomous Multi-Agent System")
    st.divider()

    st.markdown("### 🧠 Agent Architecture")
    st.markdown("""
| Agent | Role |
|-------|------|
| 📝 Planner | Decomposes query into tasks |
| 🔍 Search | Multi-query web research |
| 🔬 Research | Deep analytical reasoning |
| 🧮 Math | Step-by-step computation |
| 💻 Coding | Code + complexity analysis |
| ✍️ Writer | Polished final report |
| ⚖️ Critic | Quality gatekeeper |
""")
    st.divider()
    st.markdown("### ⚙️ Config")
    model = os.environ.get("ANTHROPIC_MODEL", "not set")
    st.code(f"Model: {model}")
    st.divider()
    st.caption("👨‍💻 Built by Manishka | Placement Project")

# ------------------------------------------------------------------ #
#  Main UI                                                            #
# ------------------------------------------------------------------ #
st.markdown("""
<h1 style='text-align:center;'>
    🧠 AI-AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS
</h1>
<p style='text-align:center; color:gray;'>
    Ask anything — the agent plans, researches, reasons, and writes a full report.
</p>
""", unsafe_allow_html=True)

st.divider()

# Example queries
EXAMPLES = [
    "How has India asserted its geopolitical influence in the last decade?",
    "Compare Rust and Go for building high-throughput microservices.",
    "What is the current state of AI regulation globally? Compare EU AI Act vs US approaches.",
    "Explain the new world of AI and how humans can keep their jobs and earn more.",
    "Implement binary search in Java with full complexity analysis.",
]

with st.expander("💡 Example queries (click to expand)", expanded=False):
    for i, ex in enumerate(EXAMPLES):
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["query_input"] = ex

query = st.text_area(
    label="🔎 Your Research Query",
    height=100,
    placeholder="e.g. What is quantum computing and how will it change cybersecurity?",
    key="query_input",
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_btn = st.button("🚀 Run Deep-Research Engine", use_container_width=True, type="primary")

st.divider()

# ------------------------------------------------------------------ #
#  Monkey-patch display.console to stream to Streamlit               #
# ------------------------------------------------------------------ #
def _setup_streamlit_console(log_container):
    """
    Replaces the rich console functions with Streamlit equivalents
    so every agent step appears live in the browser.
    """
    import ai_deep_agent.display.console as _con
    from rich.console import Console
    from io import StringIO

    def _emit(md: str):
        log_container.markdown(md)

    def header(query: str):
        log_container.markdown(f"## 🧠 Query\n> {query}")

    def planner_done(todos):
        rows = "\n".join(f"| {t['id']} | {t['task']} |" for t in todos)
        log_container.markdown(
            f"### ✅ Planner created **{len(todos)} tasks**\n"
            f"| # | Task |\n|---|------|\n{rows}"
        )

    def task_start(task_id, total, task_desc, worker):
        icons = {"search": "🔍", "research": "🔬",
                 "math": "🧮", "coding": "💻", "writer": "✍️"}
        icon = icons.get(worker, "🧠")
        log_container.markdown(
            f"---\n#### Task {task_id}/{total} → {icon} **{worker.title()} Agent**\n"
            f"`{task_desc}`"
        )

    def worker_result(worker, result, attempt):
        attempt_str = f" (attempt {attempt+1})" if attempt > 0 else ""
        with log_container.expander(
            f"📤 {worker.title()} Agent Output{attempt_str}", expanded=True
        ):
            st.markdown(result)

    def critic_pass(reason, strengths):
        log_container.success(f"✔️ **Critic: PASS** — {reason}")

    def critic_fail(reason, missing, instructions):
        items = "\n".join(f"- {x}" for x in (instructions or [reason]))
        log_container.warning(f"⚠️ **Critic: FAIL** — {reason}\n\n**Fixes needed:**\n{items}")

    def retry_notice(attempt, max_retries, feedback):
        log_container.info(f"🔄 **Retry {attempt}/{max_retries}** — {feedback[:120]}...")

    def max_retries_hit(task_id):
        log_container.warning(f"⚠️ Max retries reached for task {task_id}. Using best attempt.")

    def task_accepted(task_id, worker, retries):
        retry_str = f" after {retries} retr{'y' if retries==1 else 'ies'}" if retries else ""
        log_container.markdown(f"✅ Task {task_id} accepted [{worker}]{retry_str}")

    def final_answer(answer, writer_used):
        pass  # handled separately below

    def sources_panel(sources):
        pass  # handled separately below

    def summary_table(completed_tasks, duration):
        pass  # handled separately below

    # Patch all functions
    _con.header        = header
    _con.planner_done  = planner_done
    _con.task_start    = task_start
    _con.worker_result = worker_result
    _con.critic_pass   = critic_pass
    _con.critic_fail   = critic_fail
    _con.retry_notice  = retry_notice
    _con.max_retries_hit = max_retries_hit
    _con.task_accepted = task_accepted
    _con.final_answer  = final_answer
    _con.sources_panel = sources_panel
    _con.summary_table = summary_table


# ------------------------------------------------------------------ #
#  Run agent and display results                                      #
# ------------------------------------------------------------------ #
if run_btn and query.strip():
    # Check keys
    missing = [k for k in ["ANTHROPIC_API_KEY", "TAVILY_API_KEY"]
               if not os.environ.get(k, "").strip()]
    if missing:
        st.error(
            f"🔴 Missing API keys: {', '.join(missing)}\n\n"
            "Add them to Streamlit Cloud Secrets or your local .env file."
        )
        st.stop()

    st.markdown("### 📡 Agent Running...")
    log_area = st.container()
    _setup_streamlit_console(log_area)

    from ai_deep_agent.graph.builder import app
    from ai_deep_agent.state.state   import AgentState

    initial: AgentState = {
        "messages":          [],
        "user_query":        query.strip(),
        "todos":             [],
        "planning_complete": False,
        "completed_tasks":   [],
        "final_answer":      "",
        "writer_used":       False,
        "retry_counts":      {},
        "execution_log":     [],
        "sources":           [],
    }

    t0     = time.time()
    result = app.invoke(initial)
    dur    = time.time() - t0

    # ---- Final Answer ----
    st.divider()
    st.markdown("## 📊 Final Report")
    st.markdown(result["final_answer"])

    # ---- Sources ----
    sources = result.get("sources", [])
    if sources:
        st.divider()
        st.markdown("## 🔗 Sources")
        for s in sources:
            title = s.get("title", "Source")
            url   = s.get("url", "")
            if url:
                st.markdown(f"- [{title}]({url})")

    # ---- Summary Table ----
    st.divider()
    st.markdown("## 📋 Execution Summary")
    tasks = result.get("completed_tasks", [])
    if tasks:
        import pandas as pd
        df = pd.DataFrame([{
            "#":        t["id"],
            "Task":     t["task"][:70] + ("..." if len(t["task"]) > 70 else ""),
            "Agent":    t["worker"].title(),
            "Retries":  t.get("retries", 0),
            "Status":   "✅ Pass" if t.get("review", {}) and t["review"].get("decision") == "pass" else "✔️ Done",
        } for t in tasks])
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.success(f"⏱️ Completed in **{dur:.1f}s** | {len(tasks)} tasks")

elif run_btn:
    st.warning("⚠️ Please enter a query before running.")
