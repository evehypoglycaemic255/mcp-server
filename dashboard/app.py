import streamlit as st
import pandas as pd
import psycopg2
import os

st.set_page_config(page_title="MCP Commander", layout="wide", page_icon="🚀")
st.title("🚀 MCP Commander Dashboard")

from dotenv import load_dotenv

# Load .env from mcp_server to share DB credentials
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server", ".env"))
load_dotenv(dotenv_path)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        st.error("🚨 SECURITY ERROR: `DATABASE_URL` is not configured in `.env`.")
        st.stop()
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as e:
        st.error(f"❌ Cannot connect to Database. Please check Docker or `.env`. Error: {e}")
        st.stop()

def load_projects():
    conn = get_conn()
    df = pd.read_sql("SELECT id, project_name, description FROM projects", conn)
    conn.close()
    return df

def load_sprints(project_id):
    conn = get_conn()
    df = pd.read_sql(f"SELECT id as sprint_id, sprint_name, status, start_date, end_date FROM sprints WHERE project_id = {project_id} ORDER BY start_date DESC", conn)
    conn.close()
    return df

def load_backlogs(project_id):
    conn = get_conn()
    q = f"""
    SELECT b.id, b.task_name, b.status, s.sprint_name 
    FROM backlog_items b 
    LEFT JOIN sprints s ON b.sprint_id = s.id 
    WHERE b.project_id = {project_id}
    ORDER BY b.created_at DESC
    """
    df = pd.read_sql(q, conn)
    conn.close()
    # Convert None to empty string for UI compatibility
    df['sprint_name'] = df['sprint_name'].fillna("")
    return df

def save_backlog_changes(edited_df, original_df, project_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for idx, row in edited_df.iterrows():
                orig_row = original_df.iloc[idx]
                if row['status'] != orig_row['status'] or row['sprint_name'] != orig_row['sprint_name'] or row['task_name'] != orig_row['task_name']:
                    task_id = row['id']
                    new_status = row['status']
                    new_sprint = row['sprint_name'] if row['sprint_name'] else None
                    new_task_name = row['task_name']
                    
                    sprint_id = None
                    if new_sprint:
                        cur.execute("SELECT id FROM sprints WHERE sprint_name = %s AND project_id = %s", (new_sprint, project_id))
                        res = cur.fetchone()
                        sprint_id = res[0] if res else None
                    
                    cur.execute("""
                        UPDATE backlog_items 
                        SET status = %s, sprint_id = %s, task_name = %s
                        WHERE id = %s
                    """, (new_status, sprint_id, new_task_name, task_id))
        conn.commit()
        st.success("✅ Changes seamlessly synced to Postgres!")
    except Exception as e:
        st.error(f"❌ DB save error: {e}")
    finally:
        conn.close()

projects_df = load_projects()
if projects_df.empty:
    st.warning("No projects found in the database.")
    st.stop()

# ========================
# CONFIGURATION HEADER
# ========================
col_head, col_warn = st.columns([1, 2])
with col_head:
    project_name = st.selectbox("🎯 Select Project:", projects_df['project_name'].tolist())
project_id = projects_df[projects_df['project_name'] == project_name].iloc[0]['id']

# ========================
# VIEWS (TABS)
# ========================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏃 Sprint & Backlog Window", 
    "📊 Overview Dashboard", 
    "🤖 AI Log Signals", 
    "🛠️ System Tool Logs",
    "🔌 Plugins Ecosystem",
    "🧠 Antigravity Brain Logs"
])

with tab1:
    st.subheader(f"Sprints Status - {project_name}")
    sprints_df = load_sprints(project_id)
    if not sprints_df.empty:
        # Status coloring UI
        def color_status(val):
            if val == 'Active': return 'color: limegreen; font-weight: bold;'
            if val == 'Completed': return 'color: gray; font-style: italic;'
            if val == 'Cancelled': return 'color: red; text-decoration: line-through;'
            if val == 'Paused': return 'color: orange;'
            return ''
            
        st.dataframe(sprints_df.style.map(color_status, subset=['status']), use_container_width=True)
    else:
        st.info("No Sprints found.")

    st.markdown("---")
    st.subheader("📋 Product Backlog Dashboard (Click to edit inline)")
    backlogs_df = load_backlogs(project_id)
    
    if not backlogs_df.empty:
        sprint_names = [""] + sprints_df['sprint_name'].tolist() if not sprints_df.empty else [""]
        edited_df = st.data_editor(
            backlogs_df,
            column_config={
                "id": st.column_config.NumberColumn("Task ID", disabled=True),
                "task_name": st.column_config.TextColumn("Task Name (Editable)", width="large"),
                "status": st.column_config.SelectboxColumn("Status", options=["To Do", "In Progress", "Blocked", "Done", "Cancelled"]),
                "sprint_name": st.column_config.SelectboxColumn("Sprint Allocation", options=sprint_names)
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{project_name}"
        )
        
        if st.button("💾 Sync Web Changes -> Database", type="primary"):
            save_backlog_changes(edited_df, backlogs_df, project_id)
            st.rerun()
    else:
        st.info("Backlog queue is empty.")

with tab2:
    st.subheader("Progress Report (Views)")
    conn = get_conn()
    df_view = pd.read_sql(f"SELECT * FROM v_sprint_monitoring WHERE project_name = '{project_name}'", conn)
    st.dataframe(df_view, use_container_width=True)
    conn.close()

with tab3:
    st.subheader("Latest AI Activity Logs")
    conn = get_conn()
    sessions = pd.read_sql(f"""
        SELECT task_performed, implemented_logic, created_at 
        FROM ai_sessions 
        WHERE project_id = {project_id} 
        ORDER BY created_at DESC LIMIT 20
    """, conn)
    st.dataframe(sessions, use_container_width=True)
    conn.close()

with tab4:
    st.subheader("🕵️ System Tool Footprints (Logs)")
    st.markdown("Comprehensive monitoring of AI Tool calls (interactions with MCP Server)")
    
    conn = get_conn()
    try:
        logs_df = pd.read_sql("""
            SELECT id, tool_name, parameters, status, message, created_at 
            FROM system_tool_logs 
            ORDER BY created_at DESC 
            LIMIT 50
        """, conn)
        
        if not logs_df.empty:
            def color_tool_status(val):
                if val == 'SUCCESS': return 'color: limegreen; font-weight: bold;'
                if val == 'ERROR': return 'color: red; font-weight: bold;'
                return ''
                
            st.dataframe(
                logs_df.style.map(color_tool_status, subset=['status']), 
                use_container_width=True,
                column_config={
                    "parameters": st.column_config.TextColumn("Input Params (JSON)"),
                    "message": st.column_config.TextColumn("Gateway Output Response")
                }
            )
        else:
            st.info("No Tools have been called by AI yet.")
    except Exception as e:
        st.warning("Waiting for PostgreSQL to create `system_tool_logs` table... Please reload or trigger a tool to initialize DB.")
    finally:
        conn.close()

with tab5:
    st.subheader("🔌 Plugins Ecosystem Management")
    st.markdown("Control and Toggle Feature Modules (Namespace Architecture) to limit AI Agent capabilities.")
    
    import yaml
    PLUGINS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server", "plugins"))
    
    if os.path.exists(PLUGINS_DIR):
        plugins_data = []
        for plugin_folder in os.listdir(PLUGINS_DIR):
            p_dir = os.path.join(PLUGINS_DIR, plugin_folder)
            yaml_path = os.path.join(p_dir, "plugin.yaml")
            
            if os.path.isdir(p_dir) and os.path.exists(yaml_path):
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as yf:
                        cfg = yaml.safe_load(yf)
                        plugins_data.append({
                            "folder": plugin_folder,
                            "name": cfg.get("name", plugin_folder),
                            "description": cfg.get("description", "No description provided"),
                            "enabled": cfg.get("enabled", False),
                            "yaml_path": yaml_path
                        })
                except Exception as e:
                    st.error(f"Error reading {plugin_folder}: {e}")
                    
        for p in plugins_data:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### 📦 {p['name']}")
                    st.caption(f"Path: `plugins/{p['folder']}`")
                    st.write(p['description'])
                with col2:
                    new_state = st.toggle(f"Enable", value=p['enabled'], key=f"tg_{p['folder']}")
                    if new_state != p['enabled']:
                        try:
                            with open(p['yaml_path'], 'r', encoding='utf-8') as f:
                                doc = yaml.safe_load(f)
                            doc['enabled'] = new_state
                            with open(p['yaml_path'], 'w', encoding='utf-8') as f:
                                yaml.dump(doc, f, allow_unicode=True, default_flow_style=False)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Write Config Error: {e}")
    else:
        st.warning(f"Plugins directory not found. Dashboard is tracking: {PLUGINS_DIR}")

with tab6:
    st.subheader("🧠 Antigravity Historical Brain Logs")
    
    plugin_yaml_path = os.path.join(PLUGINS_DIR, "antigravity_sync", "plugin.yaml")
    is_enabled = False
    
    if os.path.exists(plugin_yaml_path):
        with open(plugin_yaml_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            is_enabled = cfg.get("enabled", False)
            
    if not is_enabled:
        st.warning("⚠️ Bí thuật 'Antigravity Matrix' đang bị vô hiệu hóa. Vui lòng bật nó ở '🔌 Plugins Ecosystem' (Tab 5) để cấp quyền đọc Lịch sử Chat.")
    else:
        brain_dir = "/antigravity_brain"
        if not os.path.exists(brain_dir):
            st.error(f"❌ Đứt cầu nối Volume tại `{brain_dir}`. Vui lòng tắt bật lại Docker Compose!")
        else:
            st.markdown("🔎 Trích xuất bộ nhớ Phân tích & Triển khai từ các phiên bản Chat trước của AI Agent.")
            
            folders = []
            for entry in os.listdir(brain_dir):
                full_path = os.path.join(brain_dir, entry)
                if os.path.isdir(full_path) and len(entry) > 10:
                    mtime = os.path.getmtime(full_path)
                    import datetime
                    dt_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    folders.append((f"{dt_str} [ID: {entry[:8]}]", entry, mtime))
                    
            folders.sort(key=lambda x: x[2], reverse=True)
            
            if not folders:
                st.info("Chưa tìm thấy ký ức nào của Antigravity.")
            else:
                display_names = [f[0] for f in folders]
                folder_mapping = {f[0]: f[1] for f in folders}
                
                selected_display = st.selectbox("📅 Chọn Phiên Chat Quá khứ:", display_names)
                if selected_display:
                    actual_folder = folder_mapping[selected_display]
                    target_path = os.path.join(brain_dir, actual_folder)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 🗺️ Bản vẽ Kế hoạch (Implementation Plan)")
                        plan_path = os.path.join(target_path, "implementation_plan.md")
                        if os.path.exists(plan_path):
                            with open(plan_path, 'r', encoding='utf-8') as fp:
                                st.info(fp.read())
                        else:
                            st.caption("Không có Kế hoạch kỹ thuật cho Session này.")
                            
                    with c2:
                        st.markdown("### 🏆 Báo cáo Triển khai (Final Walkthrough)")
                        walk_path = os.path.join(target_path, "walkthrough.md")
                        if os.path.exists(walk_path):
                            with open(walk_path, 'r', encoding='utf-8') as fw:
                                st.success(fw.read())
                        else:
                            st.caption("Không ghi nhận lại báo cáo Walkthrough.")