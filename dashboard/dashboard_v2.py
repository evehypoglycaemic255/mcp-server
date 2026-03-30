import datetime
import os
import sys

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

MCP_SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server"))
if MCP_SERVER_DIR not in sys.path:
    sys.path.insert(0, MCP_SERVER_DIR)

from core.schema import ensure_schema
from plugins.core_system.project_tools import (
    claim_backlog_item_record,
    create_backlog_item_record,
    release_backlog_item_record,
    update_backlog_item_record,
)


def render_app():
    st.set_page_config(page_title="MCP Commander", layout="wide", page_icon="🚀")
    st.title("🚀 MCP Commander Dashboard")

    dotenv_path = os.path.join(MCP_SERVER_DIR, ".env")
    load_dotenv(dotenv_path)
    database_url = os.environ.get("DATABASE_URL")
    plugins_dir = os.path.join(MCP_SERVER_DIR, "plugins")

    def get_conn():
        if not database_url:
            st.error("🚨 SECURITY ERROR: `DATABASE_URL` is not configured in `.env`.")
            st.stop()
        conn = psycopg2.connect(database_url)
        ensure_schema(conn)
        return conn

    def run_query(sql, params=None):
        conn = get_conn()
        try:
            return pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()

    def execute(sql, params=None):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def resolve_agent_tag(agent_tag, status, current_tag=""):
        if agent_tag and agent_tag.strip():
            return agent_tag.strip()
        if current_tag:
            return current_tag
        if status in {"In Progress", "Done", "Blocked"}:
            return "agent:unassigned"
        return ""

    def load_projects():
        return run_query("""
            SELECT id, project_name, description, COALESCE(repo_path, '') AS repo_path
            FROM projects
            ORDER BY project_name
        """)

    def load_sprints(project_id):
        return run_query("""
            SELECT id AS sprint_id, sprint_name, COALESCE(goals, '') AS goals, status, start_date, end_date
            FROM sprints
            WHERE project_id = %s
            ORDER BY start_date DESC, id DESC
        """, (project_id,))

    def load_backlogs(project_id):
        return run_query("""
            SELECT
                b.id,
                b.task_name,
                COALESCE(b.description, '') AS description,
                COALESCE(b.agent_tag, '') AS agent_tag,
                COALESCE(b.claim_status, 'Unclaimed') AS claim_status,
                b.claimed_at,
                COALESCE(b.claim_version, 0) AS claim_version,
                COALESCE(b.priority, 'Medium') AS priority,
                COALESCE(b.effort, 'M') AS effort,
                b.status,
                COALESCE(s.sprint_name, '') AS sprint_name,
                b.created_at,
                b.updated_at
            FROM backlog_items b
            LEFT JOIN sprints s ON b.sprint_id = s.id
            WHERE b.project_id = %s
            ORDER BY b.created_at DESC, b.id DESC
        """, (project_id,))

    def create_or_update_project(project_name, description, repo_path):
        execute("""
            INSERT INTO projects (project_name, description, repo_path)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_name)
            DO UPDATE SET description = EXCLUDED.description, repo_path = EXCLUDED.repo_path
        """, (project_name, description, repo_path))

    def create_sprint(project_id, sprint_name, goals, status, end_date):
        execute("""
            INSERT INTO sprints (project_id, sprint_name, goals, status, end_date)
            VALUES (%s, %s, %s, %s, NULLIF(%s, '')::timestamp)
        """, (project_id, sprint_name, goals, status, end_date))

    def create_backlog_item(project_name, task_name, description, sprint_name, priority, effort, status, agent_tag):
        conn = get_conn()
        try:
            return create_backlog_item_record(conn, project_name, task_name, description, sprint_name, status, priority, effort, agent_tag)
        finally:
            conn.close()

    def update_backlog_item(project_name, current_task_name, task_name, description, sprint_name, priority, effort, status, agent_tag=None):
        conn = get_conn()
        try:
            return update_backlog_item_record(
                conn,
                project_name=project_name,
                current_task_name=current_task_name,
                description=description,
                sprint_name=sprint_name,
                status=status,
                priority=priority,
                effort=effort,
                agent_tag=agent_tag,
                new_task_name=task_name,
            )
        finally:
            conn.close()

    def claim_backlog_item(project_name, task_name, agent_tag):
        conn = get_conn()
        try:
            return claim_backlog_item_record(conn, project_name, task_name, agent_tag)
        finally:
            conn.close()

    def release_backlog_item(project_name, task_name, agent_tag, next_status="To Do"):
        conn = get_conn()
        try:
            return release_backlog_item_record(conn, project_name, task_name, agent_tag, next_status)
        finally:
            conn.close()

    def load_plugin_data():
        import yaml

        items = []
        if not os.path.exists(plugins_dir):
            return items
        for plugin_folder in os.listdir(plugins_dir):
            p_dir = os.path.join(plugins_dir, plugin_folder)
            yaml_path = os.path.join(p_dir, "plugin.yaml")
            if os.path.isdir(p_dir) and os.path.exists(yaml_path):
                with open(yaml_path, "r", encoding="utf-8") as file:
                    cfg = yaml.safe_load(file) or {}
                items.append({
                    "folder": plugin_folder,
                    "name": cfg.get("name", plugin_folder),
                    "description": cfg.get("description", "No description provided"),
                    "enabled": cfg.get("enabled", False),
                    "version": cfg.get("version", ""),
                    "owner": cfg.get("owner", ""),
                    "managed_in": cfg.get("managed_in", []),
                    "tool_count": cfg.get("tool_count", 0),
                    "tools": cfg.get("tools", []),
                    "yaml_path": yaml_path,
                })
        return items

    def load_sync_manifest(project_name):
        import re

        slug = re.sub(r"[^A-Za-z0-9]+", "_", project_name.strip()).strip("_").lower() or "project"
        candidate_paths = [
            os.path.abspath(os.path.join(MCP_SERVER_DIR, "..", "docs", "architecture", "sync", f"{slug}_last_sync.md")),
            os.path.abspath(os.path.join(MCP_SERVER_DIR, "projects", f"{slug}_last_sync.md")),
            os.path.abspath(os.path.join(MCP_SERVER_DIR, "plugins", "core_system", f"{slug}_last_sync.md")),
        ]
        for manifest_path in candidate_paths:
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as file:
                    return manifest_path, file.read()
        return None, None

    projects_df = load_projects()
    if projects_df.empty:
        create_or_update_project("MCP_SERVER", "Primary MCP Commander project", os.path.abspath(os.path.join(MCP_SERVER_DIR, "..")))
        st.rerun()

    project_options = projects_df["project_name"].tolist()
    st.sidebar.header("Project Navigator")
    sidebar_project = st.sidebar.selectbox("Select Project", project_options)

    left, right = st.columns([1.3, 2.7])
    with left:
        project_name = st.selectbox("🎯 Active Project", project_options, index=project_options.index(sidebar_project), key="project_select_main_v2")
    selected_project = projects_df[projects_df["project_name"] == project_name].iloc[0]
    project_id = int(selected_project["id"])
    with right:
        st.caption(f"Repo Path: `{selected_project['repo_path'] or 'Not set'}`")
        st.caption(selected_project["description"] or "No project description yet.")
        sync_manifest_path, _ = load_sync_manifest(project_name)
        if sync_manifest_path:
            st.caption(f"Last Sync Manifest: `{sync_manifest_path}`")

    sprints_df = load_sprints(project_id)
    sprint_names = sprints_df["sprint_name"].tolist() if not sprints_df.empty else []
    backlogs_df = load_backlogs(project_id)

    projects_tab, sprint_tab, overview_tab, ai_tab, logs_tab, plugins_tab, brain_tab = st.tabs([
        "🗂️ Projects",
        "🏃 Sprint & Backlog Window",
        "📊 Overview Dashboard",
        "🤖 AI Log Signals",
        "🛠️ System Tool Logs",
        "🔌 Plugins Ecosystem",
        "🧠 Antigravity Brain Logs",
    ])

    with projects_tab:
        st.subheader("Projects")
        p1, p2 = st.columns([1.2, 1.8])
        with p1:
            st.dataframe(projects_df[["project_name", "repo_path", "description"]], use_container_width=True, hide_index=True)
        with p2:
            st.markdown("### Edit Active Project")
            with st.form("project_form_v2"):
                new_name = st.text_input("Project Name", value=selected_project["project_name"])
                new_desc = st.text_area("Project Description", value=selected_project["description"] or "")
                new_repo = st.text_input("Repository Path", value=selected_project["repo_path"] or "")
                submitted = st.form_submit_button("Save Project")
                if submitted and new_name.strip():
                    create_or_update_project(new_name.strip(), new_desc.strip(), new_repo.strip())
                    st.success("✅ Project saved.")
                    st.rerun()

    with sprint_tab:
        st.subheader(f"Sprint & Backlog - {project_name}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Sprints", len(sprints_df))
        m2.metric("Backlog Items", len(backlogs_df))
        m3.metric("In Progress", int((backlogs_df["status"] == "In Progress").sum()) if not backlogs_df.empty else 0)

        st.markdown("---")
        st.subheader("Sprint Window")
        if sprints_df.empty:
            st.info("No sprints found.")
        else:
            st.dataframe(sprints_df[["sprint_name", "status", "goals", "start_date", "end_date"]], use_container_width=True, hide_index=True)
            sprint_choice = st.selectbox("View sprint details", sprint_names)
            sprint_detail = sprints_df[sprints_df["sprint_name"] == sprint_choice].iloc[0]
            st.info(f"**{sprint_detail['sprint_name']}**\n\nStatus: {sprint_detail['status']}\n\nGoals: {sprint_detail['goals'] or 'No goals defined.'}")
            sync_manifest_path, sync_manifest = load_sync_manifest(project_name)
            if sync_manifest_path and sync_manifest:
                with st.expander("Latest Sync Status", expanded=False):
                    st.caption(sync_manifest_path)
                    st.markdown(sync_manifest)

        st.markdown("---")
        st.subheader("Backlog Window")
        f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1, 1.2])
        with f1:
            status_filter = st.multiselect("Filter Status", ["To Do", "In Progress", "Blocked", "Done", "Cancelled"], default=[])
        with f2:
            priority_filter = st.multiselect("Filter Priority", ["Critical", "High", "Medium", "Low"], default=[])
        with f3:
            effort_filter = st.multiselect("Filter Effort", ["S", "M", "L"], default=[])
        with f4:
            agent_options = sorted([tag for tag in backlogs_df["agent_tag"].unique().tolist() if tag])
            agent_filter = st.multiselect("Filter Agent", agent_options, default=[])
        with f5:
            view_mode = st.radio("Backlog View", ["Table", "Kanban"], horizontal=True)

        filtered_backlogs = backlogs_df.copy()
        if status_filter:
            filtered_backlogs = filtered_backlogs[filtered_backlogs["status"].isin(status_filter)]
        if priority_filter:
            filtered_backlogs = filtered_backlogs[filtered_backlogs["priority"].isin(priority_filter)]
        if effort_filter:
            filtered_backlogs = filtered_backlogs[filtered_backlogs["effort"].isin(effort_filter)]
        if agent_filter:
            filtered_backlogs = filtered_backlogs[filtered_backlogs["agent_tag"].isin(agent_filter)]

        if filtered_backlogs.empty:
            st.info("No backlog item matches the selected filters.")
        else:
            if view_mode == "Table":
                st.dataframe(filtered_backlogs[["id", "task_name", "agent_tag", "claim_status", "priority", "effort", "status", "sprint_name"]], use_container_width=True, hide_index=True)
            else:
                statuses = ["To Do", "In Progress", "Blocked", "Done", "Cancelled"]
                cols = st.columns(len(statuses))
                for idx, status in enumerate(statuses):
                    with cols[idx]:
                        st.markdown(f"**{status}**")
                        subset = filtered_backlogs[filtered_backlogs["status"] == status]
                        if subset.empty:
                            st.caption("Empty")
                        for row in subset.itertuples():
                            with st.container(border=True):
                                st.write(row.task_name)
                                st.caption(f"Agent: {row.agent_tag or 'Unassigned'}")
                                st.caption(f"Claim: {row.claim_status}")
                                st.caption(f"Priority: {row.priority} | Effort: {row.effort}")
                                st.caption(row.sprint_name or "Unassigned")

            task_options = {f"#{row.id} - {row.task_name}": int(row.id) for row in filtered_backlogs.itertuples()}
            selected_task_label = st.selectbox("Select a task to view details", list(task_options.keys()))
            selected_task_id = task_options[selected_task_label]
            selected_task = filtered_backlogs[filtered_backlogs["id"] == selected_task_id].iloc[0]

            d1, d2 = st.columns([2, 1])
            with d1:
                st.write(f"**Task:** {selected_task['task_name']}")
                st.write(f"**Purpose:** {selected_task['description'] or 'No description yet.'}")
                st.write(f"**Sprint:** {selected_task['sprint_name'] or 'Unassigned'}")
                st.write(f"**Agent:** {selected_task['agent_tag'] or 'Unassigned'}")
                st.write(f"**Claim Status:** {selected_task['claim_status']}")
            with d2:
                st.write(f"**Priority:** {selected_task['priority']}")
                st.write(f"**Effort:** {selected_task['effort']}")
                st.write(f"**Status:** {selected_task['status']}")
                st.write(f"**Claim Version:** {selected_task['claim_version']}")

            with st.expander("Assign AI Tag / Agent", expanded=False):
                with st.form(f"assign_agent_tag_form_{selected_task_id}"):
                    new_agent_tag = st.text_input("AI Agent Tag", value=selected_task['agent_tag'] or "", placeholder="agent:codex-main")
                    assign_btn = st.form_submit_button("Claim Task")
                    if assign_btn:
                        result = claim_backlog_item(project_name, selected_task["task_name"], new_agent_tag.strip())
                        if result.get("error"):
                            st.error(result["error"])
                            if result.get("claimed_by"):
                                st.caption(f"Currently claimed by: {result['claimed_by']}")
                        else:
                            st.success(f"✅ Task claimed by '{new_agent_tag.strip()}'.")
                            st.rerun()

                with st.form(f"release_agent_tag_form_{selected_task_id}"):
                    releasing_agent_tag = st.text_input("Release As Agent", value=selected_task["agent_tag"] or "", placeholder="agent:codex-main")
                    release_status = st.selectbox("Status After Release", ["To Do", "Blocked", "Done", "Cancelled"], index=0, key=f"release_status_{selected_task_id}")
                    release_btn = st.form_submit_button("Release Task")
                    if release_btn:
                        result = release_backlog_item(project_name, selected_task["task_name"], releasing_agent_tag.strip(), release_status)
                        if result.get("error"):
                            st.error(result["error"])
                            if result.get("claimed_by"):
                                st.caption(f"Currently claimed by: {result['claimed_by']}")
                        else:
                            st.success(f"✅ Task released by '{releasing_agent_tag.strip()}'.")
                            st.rerun()

            with st.expander("Edit Selected Task", expanded=False):
                with st.form(f"edit_task_{selected_task_id}_v2"):
                    edit_name = st.text_input("Task Name", value=selected_task["task_name"])
                    edit_desc = st.text_area("Task Description / Purpose", value=selected_task["description"])
                    st.caption(f"Ownership changes must go through Claim/Release. Current owner: {selected_task['agent_tag'] or 'Unassigned'}")
                    sprint_options = [""] + sprint_names
                    edit_sprint = st.selectbox("Sprint Allocation", sprint_options, index=sprint_options.index(selected_task["sprint_name"]) if selected_task["sprint_name"] in sprint_options else 0)
                    priority_options = ["Critical", "High", "Medium", "Low"]
                    effort_options = ["S", "M", "L"]
                    status_options = ["To Do", "In Progress", "Blocked", "Done", "Cancelled"]
                    edit_priority = st.selectbox("Priority", priority_options, index=priority_options.index(selected_task["priority"]) if selected_task["priority"] in priority_options else 2)
                    edit_effort = st.selectbox("Effort", effort_options, index=effort_options.index(selected_task["effort"]) if selected_task["effort"] in effort_options else 1)
                    edit_status = st.selectbox("Status", status_options, index=status_options.index(selected_task["status"]) if selected_task["status"] in status_options else 0)
                    if st.form_submit_button("Save Task Changes"):
                        result = update_backlog_item(
                            project_name,
                            selected_task["task_name"],
                            edit_name.strip(),
                            edit_desc.strip(),
                            edit_sprint,
                            edit_priority,
                            edit_effort,
                            edit_status,
                            None,
                        )
                        if result.get("error"):
                            st.error(result["error"])
                        else:
                            st.success("✅ Backlog item updated.")
                            st.rerun()

        st.markdown("---")
        a1, a2 = st.columns(2)
        with a1:
            with st.expander("Create Sprint", expanded=False):
                with st.form("create_sprint_form_v2"):
                    sprint_name = st.text_input("Sprint Name")
                    sprint_goals = st.text_area("Sprint Goals / Description")
                    sprint_status = st.selectbox("Sprint Status", ["Active", "Paused", "Completed", "Cancelled"])
                    sprint_end = st.text_input("End Date (optional, YYYY-MM-DD)")
                    if st.form_submit_button("Create Sprint") and sprint_name.strip():
                        create_sprint(project_id, sprint_name.strip(), sprint_goals.strip(), sprint_status, sprint_end)
                        st.success("✅ Sprint created.")
                        st.rerun()
        with a2:
            with st.expander("Create Backlog Item", expanded=False):
                with st.form("create_backlog_form_v2"):
                    task_name = st.text_input("Task Name")
                    task_desc = st.text_area("Task Description / Purpose")
                    task_sprint = st.selectbox("Sprint Allocation", [""] + sprint_names)
                    task_agent = st.text_input("Agent Tag", placeholder="agent:codex-main")
                    task_priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=2)
                    task_effort = st.selectbox("Effort", ["S", "M", "L"], index=1)
                    task_status = st.selectbox("Status", ["To Do", "In Progress", "Blocked", "Done", "Cancelled"])
                    if st.form_submit_button("Create Backlog Item") and task_name.strip():
                        result = create_backlog_item(project_name, task_name.strip(), task_desc.strip(), task_sprint, task_priority, task_effort, task_status, task_agent)
                        if result.get("error"):
                            st.error(result["error"])
                        else:
                            st.success("✅ Backlog item created.")
                            st.rerun()

    with overview_tab:
        df_view = run_query("SELECT * FROM v_sprint_monitoring WHERE project_name = %s", (project_name,))
        st.dataframe(df_view, use_container_width=True, hide_index=True)

    with ai_tab:
        sessions = run_query("""
            SELECT task_performed, implemented_logic, pending_tasks, created_at
            FROM ai_sessions
            WHERE project_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (project_id,))
        st.dataframe(sessions, use_container_width=True, hide_index=True)

    with logs_tab:
        logs_df = run_query("""
            SELECT id, tool_name, parameters, status, message, created_at
            FROM system_tool_logs
            ORDER BY created_at DESC
            LIMIT 50
        """)
        st.dataframe(logs_df, use_container_width=True, hide_index=True)

    with plugins_tab:
        import yaml

        st.subheader("🔌 Plugins Ecosystem Management")
        st.markdown("Plugin metadata below now shows tool scope, management surfaces, and tool ownership.")
        for plugin in load_plugin_data():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"### 📦 {plugin['name']}")
                    st.caption(f"Path: `plugins/{plugin['folder']}`")
                    st.write(plugin["description"])
                    m1, m2, m3 = st.columns(3)
                    m1.caption(f"Version: {plugin['version'] or 'N/A'}")
                    m2.caption(f"Owner: {plugin['owner'] or 'Unassigned'}")
                    m3.caption(f"Tool Count: {plugin['tool_count']}")
                    if plugin["managed_in"]:
                        st.caption("Managed in: " + ", ".join(plugin["managed_in"]))
                    if plugin["tools"]:
                        st.code(", ".join(plugin["tools"]), language="text")
                with c2:
                    new_state = st.toggle("Enable", value=plugin["enabled"], key=f"tg_{plugin['folder']}_v2")
                    if new_state != plugin["enabled"]:
                        with open(plugin["yaml_path"], "r", encoding="utf-8") as file:
                            doc = yaml.safe_load(file) or {}
                        doc["enabled"] = new_state
                        with open(plugin["yaml_path"], "w", encoding="utf-8") as file:
                            yaml.dump(doc, file, allow_unicode=True, default_flow_style=False, sort_keys=False)
                        st.rerun()

    with brain_tab:
        import yaml

        st.subheader("🧠 Antigravity Historical Brain Logs")
        plugin_yaml_path = os.path.join(plugins_dir, "antigravity_sync", "plugin.yaml")
        is_enabled = False
        if os.path.exists(plugin_yaml_path):
            with open(plugin_yaml_path, "r", encoding="utf-8") as file:
                cfg = yaml.safe_load(file)
                is_enabled = cfg.get("enabled", False)

        if not is_enabled:
            st.warning("⚠️ Plugin Antigravity đang bị vô hiệu hóa. Hãy bật nó ở tab Plugins.")
            return

        brain_dir = "/antigravity_brain"
        if not os.path.exists(brain_dir):
            st.error(f"❌ Missing mounted volume at `{brain_dir}`.")
            return

        filter_project = st.checkbox(f"Only show sessions related to [{project_name}]", value=True)
        folders = []
        for entry in os.listdir(brain_dir):
            full_path = os.path.join(brain_dir, entry)
            if os.path.isdir(full_path) and len(entry) > 10:
                is_match = False
                mapped_project = None
                mapping_file = os.path.join(full_path, ".project_mapping")
                if os.path.exists(mapping_file):
                    with open(mapping_file, "r", encoding="utf-8") as mf:
                        mapped_project = mf.read().strip()
                    is_match = mapped_project == project_name
                else:
                    for md_file in ["implementation_plan.md", "walkthrough.md", "task.md"]:
                        md_path = os.path.join(full_path, md_file)
                        if os.path.exists(md_path):
                            with open(md_path, "r", encoding="utf-8") as mf:
                                if project_name.lower() in mf.read().lower():
                                    is_match = True
                                    break
                if (not filter_project) or is_match:
                    mtime = os.path.getmtime(full_path)
                    dt_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    tag = " [Mapped]" if mapped_project == project_name else ""
                    folders.append((f"{dt_str} [ID: {entry[:8]}]{tag}", entry, mtime))

        folders.sort(key=lambda item: item[2], reverse=True)
        if not folders:
            st.info(f"No session memory found for project {project_name}.")
            return

        display_names = [item[0] for item in folders]
        folder_mapping = {item[0]: item[1] for item in folders}
        selected_display = st.selectbox("Select a past session", display_names)
        actual_folder = folder_mapping[selected_display]
        target_path = os.path.join(brain_dir, actual_folder)
        mapping_file = os.path.join(target_path, ".project_mapping")

        if not os.path.exists(mapping_file) or open(mapping_file, encoding="utf-8").read().strip() != project_name:
            if st.button(f"Pin this session to project {project_name}"):
                with open(mapping_file, "w", encoding="utf-8") as file:
                    file.write(project_name)
                st.rerun()
        else:
            st.success(f"✅ Session is pinned to project {project_name}.")

        c1, c2 = st.columns(2)
        with c1:
            plan_path = os.path.join(target_path, "implementation_plan.md")
            st.markdown("### 🗺️ Implementation Plan")
            if os.path.exists(plan_path):
                with open(plan_path, "r", encoding="utf-8") as file:
                    st.info(file.read())
            else:
                st.caption("No implementation plan for this session.")
        with c2:
            walk_path = os.path.join(target_path, "walkthrough.md")
            st.markdown("### 🏆 Walkthrough")
            if os.path.exists(walk_path):
                with open(walk_path, "r", encoding="utf-8") as file:
                    st.success(file.read())
            else:
                st.caption("No walkthrough for this session.")
