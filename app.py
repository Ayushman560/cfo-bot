import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

from db_manager import initialize_database, get_ddl, DB_FILE
from sql_engine import execute_query, verify_sql_safety
from queries_mock import find_mock_query, get_all_suggestions
from gemini_service import translate_nl_to_sql_with_gemini

# Page configuration for a widescreen, premium layout
st.set_page_config(
    page_title="CFO-Bot: Secure Natural Language to SQL",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection for Glassmorphic Elements and Glow Effects
st.markdown("""
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600&display=swap');
    
    /* Main container styling */
    .stApp {
        background-color: #0B0F19;
        font-family: 'Outfit', sans-serif;
        color: #F8FAFC;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    
    /* Sleek card elements */
    .premium-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .premium-card:hover {
        border-color: #38BDF8;
        box-shadow: 0 10px 30px -10px rgba(56, 189, 248, 0.25);
    }
    
    /* Highlighting titles and headers */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        background: linear-gradient(to right, #38BDF8, #34D399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Glow Indicators */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-right: 10px;
    }
    
    .status-active {
        background-color: rgba(52, 211, 153, 0.1);
        border: 1px solid #34D399;
        color: #34D399;
        box-shadow: 0 0 15px rgba(52, 211, 153, 0.15);
    }
    
    .status-armed {
        background-color: rgba(56, 189, 248, 0.1);
        border: 1px solid #38BDF8;
        color: #38BDF8;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
    }
    
    .status-error {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid #EF4444;
        color: #EF4444;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.15);
    }
    
    /* Safety Audit Pipeline Step boxes */
    .audit-step {
        background-color: #1E293B;
        border-left: 4px solid #38BDF8;
        border-radius: 4px;
        padding: 10px 16px;
        margin-bottom: 8px;
        font-family: 'Space Grotesk', monospace;
        font-size: 13.5px;
    }
    
    .audit-step-success {
        border-left-color: #34D399;
    }
    
    .audit-step-fail {
        border-left-color: #EF4444;
        background-color: rgba(239, 68, 68, 0.05);
    }
    
    /* Input adjustments */
    .stTextInput input {
        background-color: #1E293B !important;
        border: 1px solid #475569 !important;
        color: #F8FAFC !important;
        border-radius: 8px !important;
        font-size: 16px !important;
    }
    
    .stTextInput input:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 1px #38BDF8 !important;
    }
</style>
""", unsafe_allow_html=True)

def render_chart(df: pd.DataFrame):
    """Dynamically parses Pandas columns and visualizes beautiful charts."""
    st.markdown("### 📊 Interactive Visualizations")
    
    cols = df.columns
    num_cols = len(cols)
    
    if num_cols < 2:
        st.caption("ℹ️ Visual charts require at least two columns of relational data (e.g. category and amount).")
        return
        
    # Check if there are numeric columns for aggregation/plotting
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    text_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    
    if not numeric_cols:
        st.caption("ℹ️ Visual charts require at least one numerical metrics column.")
        return
        
    # Default metric and category columns
    metric_col = numeric_cols[0]
    category_col = text_cols[0] if text_cols else cols[0]
    
    # Chart format selections
    chart_type = st.radio(
        "Select Chart Style:",
        ["Bar Chart", "Line Graph", "Pie Distribution", "Area Trend"],
        horizontal=True
    )
    
    # Custom vibrant palette for finance
    color_scale = px.colors.qualitative.G10
    
    try:
        if chart_type == "Bar Chart":
            fig = px.bar(
                df, 
                x=category_col, 
                y=metric_col, 
                title=f"{metric_col} by {category_col}",
                color=category_col,
                color_discrete_sequence=color_scale,
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Outfit"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Line Graph":
            fig = px.line(
                df, 
                x=category_col, 
                y=metric_col, 
                title=f"{metric_col} Trend over {category_col}",
                markers=True,
                line_shape="linear",
                template="plotly_dark"
            )
            fig.update_traces(line_color="#38BDF8", marker_color="#34D399")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Outfit"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Pie Distribution":
            fig = px.pie(
                df, 
                names=category_col, 
                values=metric_col, 
                title=f"{metric_col} Distribution",
                hole=0.4,
                color_discrete_sequence=color_scale,
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Outfit"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Area Trend":
            fig = px.area(
                df,
                x=category_col,
                y=metric_col,
                title=f"{metric_col} Cumulative over {category_col}",
                template="plotly_dark"
            )
            fig.update_traces(line_color="#34D399", fillcolor="rgba(52, 211, 153, 0.2)")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Outfit"
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as chart_err:
        st.error(f"Could not render custom chart with current query dataset: {chart_err}")

# ----------------- Database Initialization Check -----------------
if not os.path.exists(DB_FILE):
    initialize_database()

# State variables initialization
if "selected_query" not in st.session_state:
    st.session_state.selected_query = ""
if "custom_query_input" not in st.session_state:
    st.session_state.custom_query_input = ""

# ----------------- SIDEBAR PANEL -----------------
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/financial-growth-analysis.png", width=70)
    st.markdown("## **CFO-Bot Console**")
    st.markdown("Designed for secure natural language business queries.")
    
    st.divider()
    
    # Gemini Key Input Section
    st.markdown("### 🔑 API Integrations")
    gemini_key = st.text_input(
        "Gemini API Key", 
        type="password", 
        placeholder="Enter API Key...",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Optional. Paste your Gemini API key here to translate any custom natural language prompt into SQL. If left blank, you can use the predefined queries below."
    )
    
    if gemini_key:
        st.caption("✅ Live Translation Ready (gemini-1.5-flash active)")
    else:
        st.caption("ℹ️ Local fallbacks active. Connect an API Key for custom queries.")
        
    st.divider()
    
    # Database Actions
    st.markdown("### ⚙️ Database Controls")
    
    # Show active rows metric
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        txns_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM departments;")
        depts_count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        txns_count, depts_count = 0, 0
        
    st.metric(label="Ledger Records", value=f"{txns_count} Rows", delta=f"{depts_count} Depts")
    
    if st.button("🔄 Reset & Seed Database", help="Overwrites existing database with fresh financial seeds."):
        initialize_database(force_reseed=True)
        st.success("Database reset and re-seeded successfully!")
        st.rerun()
        
    st.divider()
    st.markdown("`Powered by Python 3.9 & SQLite`  \n`Secure AST Scanner v1.0`  \n`Advanced Agentic Coding Labs`")

# ----------------- MAIN PANEL -----------------

# Header Section
col1, col2 = st.columns([7, 3])
with col1:
    st.title("💰 CFO-Bot: Relational Text-to-SQL")
    st.markdown("#### Empowering non-technical leaders with secure database querying using Natural Language.")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<span class="status-pill status-active">🟢 Database: SQLite Active</span>'
        '<span class="status-pill status-armed">🛡️ Safety Scan: Armed</span>', 
        unsafe_allow_html=True
    )

st.divider()

# Primary Grid Layout
left_panel, right_panel = st.columns([6, 4])

# Load suggestions
predefined_questions = get_all_suggestions()

with left_panel:
    st.markdown("### 💬 Conversational Query Panel")
    
    # Quick buttons row
    st.markdown("**💡 Common Financial Queries (Click to Run):**")
    
    # Display query suggestions as click buttons
    # Organize buttons in 2 columns
    btn_col1, btn_col2 = st.columns(2)
    for index, q_text in enumerate(predefined_questions):
        target_col = btn_col1 if index % 2 == 0 else btn_col2
        if target_col.button(q_text, key=f"btn_{index}", use_container_width=True):
            st.session_state.selected_query = q_text
            st.session_state.custom_query_input = q_text
            
    # Natural Language Text Area
    user_input = st.text_input(
        "Or type custom question in plain English:",
        value=st.session_state.custom_query_input,
        placeholder="Type here (e.g. Which department has the largest budget?)...",
        key="nl_input_field"
    )
    
    # Handle search triggers
    if user_input:
        st.session_state.selected_query = user_input
        
    # Main translation and execution trigger
    if st.session_state.selected_query:
        query_text = st.session_state.selected_query
        st.markdown(f'<div class="premium-card">', unsafe_allow_html=True)
        st.markdown(f"**Question:** `{query_text}`")
        
        # Translation Step
        sql_query = None
        explanation = None
        translation_method = ""
        translation_error = None
        
        # 1. First check local fallbacks (deterministic matches)
        mock_match = find_mock_query(query_text)
        if mock_match["matched"]:
            sql_query = mock_match["sql"]
            explanation = mock_match["explanation"]
            translation_method = "Deterministic Offline Engine"
        # 2. If no local match, check if Gemini key is provided
        elif gemini_key:
            with st.spinner("🧠 Querying Google Gemini-1.5-Flash translator..."):
                llm_res = translate_nl_to_sql_with_gemini(gemini_key, query_text)
                if llm_res["success"]:
                    sql_query = llm_res["sql"]
                    translation_method = "Live Google Gemini AI Model"
                else:
                    translation_error = llm_res["error"]
        else:
            translation_error = "Unrecognized custom query. Please connect your **Gemini API Key** in the sidebar to ask arbitrary questions."
            
        if translation_error:
            st.error(translation_error)
        else:
            # Displays the generated query planner and translator metadata
            st.markdown(f"🤖 **Translator:** Generated using `{translation_method}`")
            
            # --- RUN SAFETY LAYER BEFORE SQL EXECUTION ---
            audit_report = verify_sql_safety(sql_query)
            
            # Display Safety Scanner visually
            st.markdown("### 🛡️ Threat Assessment Pipeline")
            is_safe = audit_report["is_safe"]
            
            if is_safe:
                st.info("🟢 SAFETY CLEARANCE: Query approved. No malicious vectors or data-altering codes identified.")
            else:
                st.error("🚨 THREAT BLOCK: Query intercepted. Safety rules violated to protect ledger integrity.")
                
            with st.expander("📝 Show Safety Inspection Log Details", expanded=not is_safe):
                for step in audit_report["steps"]:
                    is_err = "Violation" in step or "failed" in step or "Blocked" in step or "❌" in step
                    if is_err:
                        st.markdown(f'<div class="audit-step audit-step-fail">{step}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="audit-step audit-step-success">{step}</div>', unsafe_allow_html=True)
                        
                if not is_safe:
                    st.markdown("**Violations Identified:**")
                    for violation in audit_report["violations"]:
                        st.markdown(f"- 🔴 `{violation}`")
                        
            # If safe, proceed with execution
            if is_safe:
                # Query planner visual editor
                st.markdown("### 🖥️ Query Planner Output")
                st.code(sql_query, language="sql")
                if explanation:
                    st.markdown(f"ℹ️ **Query Logic:** {explanation}")
                    
                # Database execution
                execution_report = execute_query(sql_query)
                
                if execution_report["success"]:
                    df_res = execution_report["data"]
                    row_count = execution_report["row_count"]
                    speed = execution_report["execution_time"]
                    
                    st.success(f"📊 **Database Results:** Returned `{row_count}` rows in `{speed}` ms")
                    
                    if row_count > 0:
                        # RENDER DATA & GRAPH
                        st.dataframe(df_res, use_container_width=True)
                        
                        # Graph builder panel
                        render_chart(df_res)
                    else:
                        st.warning("Query execution completed successfully but returned 0 rows.")
                else:
                    st.error(f"Execution Error in SQLite Engine: {execution_report['error']}")
                    
        st.markdown('</div>', unsafe_allow_html=True)

with right_panel:
    st.markdown("### 📐 Database Schema Explorer")
    st.markdown("CFO-Bot reads the Data Definition Language (DDL) below to understand relational tables and primary-foreign key bonds:")
    
    with st.expander("🔍 Interactive Tables Definition", expanded=True):
        st.markdown("""
        * 🏢 **departments** - Department details & budget sizes
          * `id` (INTEGER, Primary Key)
          * `name` (TEXT, Unique)
          * `manager` (TEXT)
          * `budget` (REAL)
        * 💸 **transactions** - Financial ledger journal
          * `id` (INTEGER, Primary Key)
          * `date` (TEXT, YYYY-MM-DD)
          * `amount` (REAL)
          * `description` (TEXT)
          * `type` (TEXT CHECK, 'Revenue'/'Expense')
          * `category` (TEXT)
          * `department_id` (INTEGER, Foreign Key -> departments)
        * 📊 **monthly_forecasts** - Corporate targets
          * `id` (INTEGER, Primary Key)
          * `month` (TEXT, YYYY-MM)
          * `projected_revenue` (REAL)
          * `projected_expense` (REAL)
        * 📉 **cash_flow_ledger** - Treasury cash flow summary
          * `id` (INTEGER, Primary Key)
          * `date` (TEXT)
          * `cash_in` (REAL)
          * `cash_out` (REAL)
          * `balance` (REAL)
        """)
        
    with st.expander("📝 View Raw DDL Schema Structure (Postgres/SQLite format)"):
        st.code(get_ddl(), language="sql")
        
    st.divider()
    
    # Interactive direct SQL query sandbox
    st.markdown("### 🧪 Safety Threat Sandbox")
    st.markdown("Write direct SQL queries to inspect how the threat scanner detects injection attacks:")
    
    sandbox_sql = st.text_area(
        "SQL Query Sandbox Input:",
        value="SELECT * FROM transactions ORDER BY amount DESC LIMIT 3;",
        height=100
    )
    
    if st.button("🚀 Execute Sandbox Query"):
        st.markdown("---")
        # Validate sandbox query
        sandbox_audit = verify_sql_safety(sandbox_sql)
        
        # Display logs
        for step in sandbox_audit["steps"]:
            is_err = "Violation" in step or "failed" in step or "Blocked" in step or "❌" in step
            if is_err:
                st.markdown(f'<div class="audit-step audit-step-fail">{step}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="audit-step audit-step-success">{step}</div>', unsafe_allow_html=True)
                
        if sandbox_audit["is_safe"]:
            sandbox_exec = execute_query(sandbox_sql)
            if sandbox_exec["success"]:
                st.dataframe(sandbox_exec["data"], use_container_width=True)
                st.success(f"Successfully processed `{sandbox_exec['row_count']}` rows in `{sandbox_exec['execution_time']}` ms.")
            else:
                st.error(f"SQLite execution failed: {sandbox_exec['error']}")
        else:
            st.error("🚫 Execution Blocked: The safety scanner intercepted your query because it contains unsafe or disallowed syntax structures.")
            for violation in sandbox_audit["violations"]:
                st.markdown(f"- 🔴 `{violation}`")
