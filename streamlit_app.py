"""
Streamlit UI for AI Operations Assistant
Dark, professional dashboard-style interface
"""

import streamlit as st
import requests
import time
from datetime import datetime

# =========================
# Page configuration
# =========================
st.set_page_config(
    page_title="AI Operations Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Dark Professional CSS
# =========================
st.markdown("""
<style>

/* ---------- Global ---------- */
html, body, [class*="css"] {
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: radial-gradient(1200px 600px at 10% 10%, #111827, #020617);
    color: #e5e7eb;
}

/* Main container */
.main .block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* ---------- Header ---------- */
.main-header {
    font-size: 2.6rem;
    font-weight: 700;
    text-align: center;
    color: #f9fafb;
    margin-bottom: 0.25rem;
}

.sub-header {
    text-align: center;
    color: #9ca3af;
    font-size: 1rem;
    margin-bottom: 2.25rem;
}

/* ---------- Cards ---------- */
.card {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    margin-bottom: 1rem;
}

/* ---------- Status ---------- */
.status-success {
    background: linear-gradient(90deg, #064e3b, #022c22);
    border-left: 4px solid #10b981;
    color: #ecfdf5;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}

.status-warning {
    background: linear-gradient(90deg, #78350f, #451a03);
    border-left: 4px solid #f59e0b;
    color: #fffbeb;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}

/* ---------- Section headers ---------- */
.section-header {
    font-size: 1.2rem;
    font-weight: 600;
    color: #f3f4f6;
    margin: 1.75rem 0 1rem;
}

/* ---------- Inputs ---------- */
textarea, input {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    font-weight: 600;
    border-radius: 10px;
    padding: 0.75rem 1.5rem;
    border: none;
    width: 100%;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    transform: translateY(-1px);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020617);
    border-right: 1px solid rgba(148,163,184,0.1);
}

section[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* ---------- Expanders ---------- */
.stExpander {
    background: rgba(15, 23, 42, 0.85);
    border-radius: 12px;
    border: 1px solid rgba(148,163,184,0.15);
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab"] {
    background: #020617;
    color: #cbd5f5;
    border-radius: 8px 8px 0 0;
}

.stTabs [aria-selected="true"] {
    background: #1e293b;
}

/* ---------- Metrics ---------- */
[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.85);
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid rgba(148,163,184,0.15);
}

/* ---------- Links ---------- */
a {
    color: #60a5fa;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}

/* ---------- Remove dimming/loading overlay effects ---------- */
div[data-testid="stAppViewContainer"] > div:first-child {
    opacity: 1 !important;
    transition: none !important;
}

.stApp {
    opacity: 1 !important;
    transition: none !important;
}

div[data-testid="stDecoration"] {
    display: none !important;
}

* {
    transition: none !important;
}

.stButton > button:hover {
    transition: transform 0.2s ease-in-out !important;
}

.main .block-container {
    opacity: 1 !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# API Configuration
# =========================
API_BASE_URL = "http://localhost:8000"

# =========================
# Session state initialization
# =========================
if "history" not in st.session_state:
    st.session_state.history = []
if "task_input" not in st.session_state:
    st.session_state.task_input = ""

# =========================
# CACHED API Helpers
# =========================
@st.cache_data(ttl=60)
def check_api_health():
    """Cached health check"""
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=2).status_code == 200
    except:
        return False

@st.cache_data(ttl=300)
def get_available_tools():
    """Cached tools list"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/tools", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=300)
def get_example_tasks():
    """Cached examples"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/examples", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def submit_task(task: str):
    """NOT cached - always fresh results"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/task/execute",
            json={"task": task},
            timeout=60
        )
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# =========================
# UI Components
# =========================
def workflow_diagram():
    st.markdown("""
    <div class="card" style="text-align:center;">
        <strong>User Task</strong> → <strong>Planner</strong> → 
        <strong>Executor</strong> → <strong>Verifier</strong> → <strong>Result</strong>
    </div>
    """, unsafe_allow_html=True)

def display_result(data):
    if data.get("verified"):
        st.markdown('<div class="status-success">Task completed successfully</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">Task completed with warnings</div>', unsafe_allow_html=True)

    # Execution Plan
    with st.expander("Execution Plan", expanded=False):
        plan = data.get("execution_plan", {})
        st.write("**Task:**", plan.get("task"))
        st.write("**Tools:**", ", ".join(plan.get("estimated_tools", [])))
        for step in plan.get("steps", []):
            st.markdown(
                f"<div class='card'><strong>Step {step['step_number']}:</strong> {step['action']}<br>"
                f"<small>Tool: {step['tool']} | {step['reasoning']}</small></div>",
                unsafe_allow_html=True
            )

    # Detailed Results
    with st.expander("Detailed Results", expanded=False):
        for tool, output in data.get("details", {}).items():
            st.subheader(tool.title())
            st.json(output)
    
    # Verification Notes
    if data.get("verification_notes"):
        with st.expander("Verification Notes", expanded=False):
            notes = data["verification_notes"]
            if isinstance(notes, str):
                for line in notes.split("\n"):
                    if line.strip():
                        if line.startswith("-"):
                            st.markdown(f"  {line}")
                        elif ":" in line and not line.startswith("  "):
                            st.markdown(f"**{line}**")
                        else:
                            st.markdown(line)
            else:
                st.warning(notes)

    # Summary
    st.markdown('<div class="section-header">Summary</div>', unsafe_allow_html=True)
    summary = data.get('summary', 'No summary available')
    st.markdown(summary)

# =========================
# Helper to populate task input WITHOUT refresh
# =========================
def set_task_text(text):
    """Updates the task input field WITHOUT causing a full page refresh"""
    st.session_state.task_input = text

# =========================
# Main App
# =========================
def main():
    st.markdown('<h1 class="main-header">AI Operations Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent System for Real-World AI Operations</p>', unsafe_allow_html=True)

    # Fast health check (cached)
    if not check_api_health():
        st.error("Backend API not running. Start FastAPI first: python main.py")
        st.stop()

    # Left sidebar - Recent Tasks
    with st.sidebar:
        st.markdown("### Recent Tasks")
        if st.session_state.history:
            for i, h in enumerate(reversed(st.session_state.history[-10:])):
                task_preview = h["task"][:50] + "..." if len(h["task"]) > 50 else h["task"]
                st.button(
                    task_preview, 
                    key=f"hist_{i}", 
                    use_container_width=True,
                    on_click=set_task_text,
                    args=(h["task"],)
                )
        else:
            st.caption("No recent tasks yet")
        
        st.divider()
        
        st.markdown("### About")
        st.info("""
        **3 AI Agents**
        - Planner
        - Executor
        - Verifier  

        **LLM-powered orchestration**
        """)
        
        st.metric("Tasks Executed", len(st.session_state.history))

    workflow_diagram()

    # Main layout: Input area and right sidebar for tools
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown('<div class="section-header">Enter Task</div>', unsafe_allow_html=True)
        
        # Task input
        task = st.text_area(
            "",
            placeholder="Example: Find top ML GitHub repos and check London weather",
            height=110,
            key="task_input"
        )

        if st.button("Execute Task", use_container_width=True):
            if task.strip():
                with st.spinner("Running multi-agent workflow..."):
                    result, code = submit_task(task)
                    if code == 200:
                        display_result(result)
                        st.session_state.history.append({
                            "task": task,
                            "time": datetime.now()
                        })
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please enter a task")

    # Right sidebar - Example Tasks and Available Tools
    with col2:
        st.markdown('<div class="section-header">Example Tasks</div>', unsafe_allow_html=True)
        
        # Fast loading with cache
        examples = get_example_tasks()
        if examples:
            for i, ex in enumerate(examples.get("examples", [])[:5]):
                st.button(
                    ex[:60] + ("..." if len(ex) > 60 else ""),
                    key=f"ex_{i}",
                    use_container_width=True,
                    on_click=set_task_text,
                    args=(ex,)
                )
        
        st.markdown('<div class="section-header" style="margin-top: 0.5rem;">Available Tools</div>', unsafe_allow_html=True)
        
        # Fast loading with cache
        tools = get_available_tools()
        if tools:
            for t in tools.get("tools", {}).values():
                with st.expander(t["name"], expanded=False):
                    st.write(t["description"])
        else:
            st.caption("Unable to load tools")

if __name__ == "__main__":
    main()