"""
AI_AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS
Streamlit Web Interface  —  v4 (clean output: final report only)
"""
import os
import time
import streamlit as st
import sys

# Add src/ to path so ai_deep_agent package is found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# ------------------------------------------------------------------ #
#  Page config  (must be first Streamlit call)                        #
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="AI_AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS",
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
    pass   # running locally without secrets

from dotenv import load_dotenv
load_dotenv()

# ------------------------------------------------------------------ #
#  Sidebar                                                            #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4616/4616013.png", width=64)
    st.title("AI_AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS")
    st.caption("Deep-Research · Long Horizon Tasks · Autonomous Multi-Agent System")
    st.divider()

    st.markdown("### 🧠 Agent Architecture")
    st.markdown("""
| Agent | Role |
|---|---|
| 📌 Planner | Decomposes query into tasks |
| 🔍 Search | Live web search & evidence |
| 🔬 Research | Deep analysis & synthesis |
| 📊 Math | Calculations & proofs |
| 💻 Coding | Code generation & debug |
| ✍️ Writer | Final report synthesis |
| ⚖️ Critic | Quality gate on final report |
""")
    st.divider()
    st.markdown("### ⚙️ Config")
    model = os.environ.get("ANTHROPIC_MODEL") or os.environ.get("GEMINI_MODEL", "not set")
    st.code(f"Model: {model}")
    st.divider()
    st.caption("👨‍💻 Built by Manishka | Placement Project")

# ------------------------------------------------------------------ #
#  Main UI                                                            #
# ------------------------------------------------------------------ #
st.markdown("""
<h1 style='text-align:center;'>
    🧠 AI_AUTONOMOUS COGNITIVE ENGINE FOR DEEP-RESEARCH AND LONG HORIZON TASKS
</h1>
<p style='text-align:center; color:gray;'>
    Ask anything — the agent plans, researches, reasons, and writes a full report.
</p>
""", unsafe_allow_html=True)

st.divider()

query = st.text_area(
    "🔍 Enter your research query",
    placeholder="e.g. How will AI impact cybersecurity laws over the next decade?",
    height=100,
)

col1, col2 = st.columns([1, 5])
with col1:
    run_btn = st.button("🚀 Run Agent", type="primary", use_container_width=True)
with col2:
    st.markdown("*The agent will plan, research, and write a full structured report.*")

# ------------------------------------------------------------------ #
#  Run agent and display results                                      #
# ------------------------------------------------------------------ #
if run_btn and query.strip():
    # Check keys
    missing = [k for k in ["TAVILY_API_KEY"]
               if not os.environ.get(k, "").strip()]
    if missing:
        st.error(
            f"🔴 Missing API keys: {', '.join(missing)}\n\n"
            "Add them to Streamlit Cloud Secrets or your local .env file."
        )
        st.stop()

    from ai_deep_agent.graph.builder import app
    from ai_deep_agent.state.state   import AgentState

    initial: AgentState = {
        "user_query":        query.strip(),
        "todos":             [],
        "planning_complete": False,
        "execution_log":     [],
        "sources":           [],
        "retry_counts":      {},
        "all_tasks_complete": False,
        "final_report":      "",
    }

    # Progress area
    progress_container = st.container()
    with progress_container:
        st.markdown("### ⏳ Running Agent...")
        status_area = st.empty()
        task_list   = st.empty()

    with st.spinner("🧠 Agent thinking..."):
        start = time.time()
        result = app.invoke(initial)
        elapsed = time.time() - start

    # ------------------------------------------------------------------ #
    #  Display: execution summary (compact) + final report only          #
    # ------------------------------------------------------------------ #
    st.success(f"✅ Completed in {elapsed:.1f}s")
    st.divider()

    # --- Task execution summary (compact, no full outputs) ---
    execution_log = result.get("execution_log", [])
    if execution_log:
        with st.expander("📋 Task Execution Summary", expanded=False):
            worker_icons = {
                "search":   "🔍",
                "research": "🔬",
                "math":     "📊",
                "coding":   "💻",
                "writer":   "✍️",
            }
            for entry in execution_log:
                icon   = worker_icons.get(entry.get("worker", ""), "⚙️")
                task_n = entry.get("task_id", "?")
                task_t = entry.get("task", "")[:80]
                worker = entry.get("worker", "?").capitalize()
                verdict = entry.get("verdict", "PASS")
                badge  = "✅" if verdict == "PASS" else "🔄"
                st.markdown(f"{badge} **Task {task_n}** {icon} `{worker}` — {task_t}...")

    # --- Final Report (beautiful, full width) ---
    final_report = result.get("final_report", "")

    st.markdown("## 📝 Final Report")
    st.divider()

    if final_report:
        st.markdown(final_report)
    else:
        # Fallback: show last task output if writer wasn't reached
        if execution_log:
            last = execution_log[-1]
            st.markdown(last.get("result", "*No output generated.*"))
        else:
            st.warning("⚠️ No output was generated. Try a simpler query.")

    # --- Sources ---
    sources = result.get("sources", [])
    if sources:
        st.divider()
        with st.expander("🔗 Sources", expanded=False):
            seen = set()
            for s in sources:
                url = s.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    title = s.get("title", url)
                    st.markdown(f"- [{title}]({url})")

    # --- Download report ---
    st.divider()
    report_text = final_report or (execution_log[-1].get("result", "") if execution_log else "")
    if report_text:
        st.download_button(
            label="⬇️ Download Report",
            data=report_text,
            file_name="ai_research_report.md",
            mime="text/markdown",
        )
