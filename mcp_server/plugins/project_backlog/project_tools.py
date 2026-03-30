import os
import re
from datetime import datetime

from psycopg2.extras import RealDictCursor
from core.database import get_db_conn
from core.dependencies import safe_tool


def _project_slug(project_name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", project_name.strip()).strip("_").lower()
    return slug or "project"


def _docs_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "architecture"))


def _sync_manifest_paths(project_name: str) -> list[str]:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    slug = f"{_project_slug(project_name)}_last_sync.md"
    return [
        os.path.join(_docs_root(), "sync", slug),
        os.path.join(repo_root, "mcp_server", "projects", slug),
        os.path.join(repo_root, "mcp_server", "plugins", "core_system", slug),
    ]


def _sync_manifest_targets(project_name: str, repo_path: str = "") -> list[str]:
    repo_root = repo_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return [
        os.path.relpath(os.path.join(repo_root, "readme.md"), repo_root),
        os.path.relpath(os.path.join(repo_root, "docs", "architecture", "v1_architecture.md"), repo_root),
        os.path.relpath(os.path.join(repo_root, "docs", "architecture", "code_wiring.md"), repo_root),
    ]


def _write_sync_manifest(project_name: str, sprint_name: str, repo_path: str = "", synced_by: str = "system-trigger") -> dict:
    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    targets = _sync_manifest_targets(project_name, repo_path)
    content = "\n".join(
        [
            f"# Sync Status: {project_name}",
            "",
            f"- Project: `{project_name}`",
            f"- Last synced at: `{synced_at}`",
            f"- Triggered by sprint completion: `{sprint_name}`",
            f"- Synced by: `{synced_by}`",
            "",
            "## Tracked Documents",
            "",
            *[f"- `{target}`" for target in targets],
            "",
            "## Purpose",
            "",
            "Tài liệu này được hệ thống tự sinh khi sprint chuyển sang `Completed` để người dùng và AI agent cùng theo dõi lần sync gần nhất mà không cần yêu cầu thủ công.",
            "",
        ]
    )
    last_error = None
    for manifest_path in _sync_manifest_paths(project_name):
        try:
            parent_dir = os.path.dirname(manifest_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as handle:
                handle.write(content)
            return {"manifest_path": manifest_path, "synced_at": synced_at, "tracked_documents": targets}
        except OSError as exc:
            last_error = str(exc)
    raise OSError(last_error or "Unable to write sync manifest")


def _resolve_agent_tag(current_tag: str, requested_tag: str, status: str) -> str:
    if requested_tag:
        return requested_tag.strip()
    if current_tag:
        return current_tag
    if status in {"In Progress", "Done", "Blocked"}:
        return "agent:unassigned"
    return current_tag or ""


UNCLAIMED_AGENT_TAGS = {"", "agent:unassigned"}
CLAIMED_STATUSES = {"In Progress", "Blocked", "Done"}


def _is_unclaimed(agent_tag: str) -> bool:
    return (agent_tag or "").strip() in UNCLAIMED_AGENT_TAGS


def _insert_claim_event(cur, backlog_item_id: int, event_type: str, actor_agent_tag: str, previous_agent_tag: str, new_agent_tag: str, note: str = ""):
    cur.execute(
        """
        INSERT INTO backlog_claim_events (
            backlog_item_id, event_type, actor_agent_tag, previous_agent_tag, new_agent_tag, note
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            backlog_item_id,
            event_type,
            (actor_agent_tag or "").strip(),
            (previous_agent_tag or "").strip(),
            (new_agent_tag or "").strip(),
            note.strip(),
        ),
    )


def _get_project(cur, project_name: str):
    cur.execute("SELECT id, project_name, description, repo_path FROM projects WHERE project_name = %s", (project_name,))
    return cur.fetchone()


def _resolve_sprint_id(cur, project_id: int, project_name: str, sprint_name: str):
    if not sprint_name:
        return None, None
    cur.execute(
        "SELECT id FROM sprints WHERE project_id = %s AND sprint_name = %s",
        (project_id, sprint_name),
    )
    sprint = cur.fetchone()
    if not sprint:
        return None, {"error": f"Sprint '{sprint_name}' does not exist for project '{project_name}'"}
    return sprint["id"], None


def _get_backlog_item_for_update(cur, project_id: int, task_name: str):
    cur.execute(
        """
        SELECT id, task_name, description, agent_tag, claim_status, claimed_at, claim_version, priority, effort, status, sprint_id, updated_at
        FROM backlog_items
        WHERE project_id = %s AND task_name = %s
        FOR UPDATE
        """,
        (project_id, task_name),
    )
    return cur.fetchone()


def create_backlog_item_record(
    conn,
    project_name: str,
    task_name: str,
    description: str = "",
    sprint_name: str = "",
    status: str = "To Do",
    priority: str = "Medium",
    effort: str = "M",
    agent_tag: str = "",
):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        project = _get_project(cur, project_name)
        if not project:
            return {"error": f"Project '{project_name}' does not exist"}

        sprint_id, error = _resolve_sprint_id(cur, project["id"], project_name, sprint_name)
        if error:
            return error

        resolved_agent_tag = _resolve_agent_tag("", agent_tag, status)
        claim_status = "Claimed" if (not _is_unclaimed(resolved_agent_tag) or status in CLAIMED_STATUSES) else "Unclaimed"
        claimed_at = datetime.now() if claim_status == "Claimed" else None
        cur.execute(
            """
            INSERT INTO backlog_items (
                project_id, sprint_id, task_name, description, agent_tag, claim_status, claimed_at, priority, effort, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, task_name, description, agent_tag, claim_status, claimed_at, claim_version, priority, effort, status
            """,
            (
                project["id"],
                sprint_id,
                task_name,
                description,
                resolved_agent_tag,
                claim_status,
                claimed_at,
                priority,
                effort,
                status,
            ),
        )
        item = cur.fetchone()
        if claim_status == "Claimed":
            _insert_claim_event(cur, item["id"], "create_claimed", resolved_agent_tag, "", resolved_agent_tag, "Task created with active ownership.")
    conn.commit()
    return {"status": "created", "backlog_item": item}


def claim_backlog_item_record(conn, project_name: str, task_name: str, agent_tag: str):
    normalized_agent = (agent_tag or "").strip()
    if not normalized_agent or normalized_agent in UNCLAIMED_AGENT_TAGS:
        return {"error": "A concrete agent tag is required to claim a task"}

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        project = _get_project(cur, project_name)
        if not project:
            return {"error": f"Project '{project_name}' does not exist"}

        item = _get_backlog_item_for_update(cur, project["id"], task_name)
        if not item:
            return {"error": f"Backlog item '{task_name}' does not exist for project '{project_name}'"}

        current_owner = (item["agent_tag"] or "").strip()
        if current_owner and not _is_unclaimed(current_owner) and current_owner != normalized_agent:
            return {"error": "Task already claimed by another agent", "claimed_by": current_owner, "task_name": item["task_name"]}

        next_status = "In Progress" if item["status"] == "To Do" else item["status"]
        cur.execute(
            """
            UPDATE backlog_items
            SET agent_tag = %s,
                claim_status = 'Claimed',
                claimed_at = COALESCE(claimed_at, CURRENT_TIMESTAMP),
                status = %s,
                claim_version = claim_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, task_name, description, agent_tag, claim_status, claimed_at, claim_version, priority, effort, status, updated_at
            """,
            (normalized_agent, next_status, item["id"]),
        )
        updated = cur.fetchone()
        _insert_claim_event(
            cur,
            item["id"],
            "claim" if _is_unclaimed(current_owner) else "refresh_claim",
            normalized_agent,
            current_owner,
            normalized_agent,
            "Task claimed for execution.",
        )
    conn.commit()
    return {"status": "claimed", "backlog_item": updated}


def release_backlog_item_record(conn, project_name: str, task_name: str, agent_tag: str, next_status: str = "To Do"):
    normalized_agent = (agent_tag or "").strip()
    if not normalized_agent:
        return {"error": "Agent tag is required to release a task"}

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        project = _get_project(cur, project_name)
        if not project:
            return {"error": f"Project '{project_name}' does not exist"}

        item = _get_backlog_item_for_update(cur, project["id"], task_name)
        if not item:
            return {"error": f"Backlog item '{task_name}' does not exist for project '{project_name}'"}

        current_owner = (item["agent_tag"] or "").strip()
        if _is_unclaimed(current_owner):
            return {"error": "Task is not currently claimed", "task_name": item["task_name"]}
        if current_owner != normalized_agent:
            return {"error": "Only the current owner can release this task", "claimed_by": current_owner, "task_name": item["task_name"]}

        final_status = next_status or "To Do"
        cur.execute(
            """
            UPDATE backlog_items
            SET agent_tag = '',
                claim_status = 'Unclaimed',
                claimed_at = NULL,
                status = %s,
                claim_version = claim_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, task_name, description, agent_tag, claim_status, claimed_at, claim_version, priority, effort, status, updated_at
            """,
            (final_status, item["id"]),
        )
        updated = cur.fetchone()
        _insert_claim_event(cur, item["id"], "release", normalized_agent, current_owner, "", "Task released back to the backlog pool.")
    conn.commit()
    return {"status": "released", "backlog_item": updated}


def update_backlog_item_record(
    conn,
    project_name: str,
    current_task_name: str,
    description: str = "",
    sprint_name: str = "",
    status: str = "",
    priority: str = "",
    effort: str = "",
    agent_tag=None,
    new_task_name: str = "",
    allow_reassign: bool = False,
):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        project = _get_project(cur, project_name)
        if not project:
            return {"error": f"Project '{project_name}' does not exist"}

        item = _get_backlog_item_for_update(cur, project["id"], current_task_name)
        if not item:
            return {"error": f"Backlog item '{current_task_name}' does not exist for project '{project_name}'"}

        sprint_id = item["sprint_id"]
        if sprint_name:
            sprint_id, error = _resolve_sprint_id(cur, project["id"], project_name, sprint_name)
            if error:
                return error

        previous_owner = (item["agent_tag"] or "").strip()
        next_status = status or item["status"]
        next_agent_tag = previous_owner
        if agent_tag is not None:
            requested_agent_tag = _resolve_agent_tag(previous_owner, agent_tag, next_status)
            if previous_owner and not _is_unclaimed(previous_owner) and requested_agent_tag != previous_owner and not allow_reassign:
                return {
                    "error": "Task is claimed by another agent; use claim/release flow instead of overwriting ownership",
                    "claimed_by": previous_owner,
                    "task_name": item["task_name"],
                }
            next_agent_tag = requested_agent_tag

        next_claim_status = item["claim_status"] or "Unclaimed"
        next_claimed_at = item["claimed_at"]
        if _is_unclaimed(next_agent_tag):
            if next_status in CLAIMED_STATUSES:
                next_agent_tag = "agent:unassigned"
                next_claim_status = "Claimed"
                next_claimed_at = next_claimed_at or datetime.now()
            else:
                next_agent_tag = ""
                next_claim_status = "Unclaimed"
                next_claimed_at = None
        else:
            next_claim_status = "Claimed"
            next_claimed_at = next_claimed_at or datetime.now()

        cur.execute(
            """
            UPDATE backlog_items
            SET task_name = CASE WHEN %s = '' THEN task_name ELSE %s END,
                description = CASE WHEN %s = '' THEN description ELSE %s END,
                sprint_id = %s,
                status = CASE WHEN %s = '' THEN status ELSE %s END,
                agent_tag = %s,
                claim_status = %s,
                claimed_at = %s,
                priority = CASE WHEN %s = '' THEN priority ELSE %s END,
                effort = CASE WHEN %s = '' THEN effort ELSE %s END,
                claim_version = claim_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, task_name, description, agent_tag, claim_status, claimed_at, claim_version, priority, effort, status, sprint_id, updated_at
            """,
            (
                new_task_name,
                new_task_name,
                description,
                description,
                sprint_id,
                status,
                status,
                next_agent_tag,
                next_claim_status,
                next_claimed_at,
                priority,
                priority,
                effort,
                effort,
                item["id"],
            ),
        )
        updated_item = cur.fetchone()
        if previous_owner != next_agent_tag:
            _insert_claim_event(
                cur,
                item["id"],
                "reassign" if previous_owner and next_agent_tag else "release" if previous_owner else "claim",
                next_agent_tag or previous_owner,
                previous_owner,
                next_agent_tag,
                "Ownership changed through backlog update flow.",
            )
    conn.commit()
    return {"status": "updated", "backlog_item": updated_item}


def assign_backlog_agent_tag_record(conn, task_id: int, ai_tag: str):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT p.project_name, b.task_name
            FROM backlog_items b
            JOIN projects p ON p.id = b.project_id
            WHERE b.id = %s
            """,
            (task_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"Backlog item {task_id} not found"}
    return claim_backlog_item_record(conn, row["project_name"], row["task_name"], ai_tag)


def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def upsert_project(project_name: str, description: str = "", repo_path: str = ""):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO projects (project_name, description, repo_path)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (project_name)
                    DO UPDATE SET description = EXCLUDED.description, repo_path = EXCLUDED.repo_path
                    RETURNING id, project_name, description, repo_path
                """, (project_name, description, repo_path))
                row = cur.fetchone()
            conn.commit()
            return {"status": "saved", "project": row}
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def create_sprint(project_name: str, sprint_name: str, goals: str = "", status: str = "Active", end_date: str = ""):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM projects WHERE project_name = %s", (project_name,))
                project = cur.fetchone()
                if not project:
                    return {"error": f"Project '{project_name}' does not exist"}

                cur.execute("""
                    INSERT INTO sprints (project_id, sprint_name, goals, status, end_date)
                    VALUES (%s, %s, %s, %s, NULLIF(%s, '')::timestamp)
                    RETURNING id, sprint_name, goals, status, start_date, end_date
                """, (project["id"], sprint_name, goals, status, end_date))
                sprint = cur.fetchone()
            conn.commit()
            return {"status": "created", "sprint": sprint}
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def update_sprint(
        project_name: str,
        sprint_name: str,
        goals: str = "",
        status: str = "",
        end_date: str = "",
    ):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT s.id, s.sprint_name, s.goals, s.status, s.start_date, s.end_date
                    FROM sprints s
                    JOIN projects p ON p.id = s.project_id
                    WHERE p.project_name = %s AND s.sprint_name = %s
                    """,
                    (project_name, sprint_name),
                )
                sprint = cur.fetchone()
                if not sprint:
                    return {"error": f"Sprint '{sprint_name}' does not exist for project '{project_name}'"}

                cur.execute("SELECT id, repo_path FROM projects WHERE project_name = %s", (project_name,))
                project = cur.fetchone()

                cur.execute(
                    """
                    UPDATE sprints
                    SET goals = CASE WHEN %s = '' THEN goals ELSE %s END,
                        status = CASE WHEN %s = '' THEN status ELSE %s END,
                        end_date = CASE
                            WHEN %s = '' THEN end_date
                            ELSE NULLIF(%s, '')::timestamp
                        END
                    WHERE id = %s
                    RETURNING id, sprint_name, goals, status, start_date, end_date
                    """,
                    (goals, goals, status, status, end_date, end_date, sprint["id"]),
                )
                updated_sprint = cur.fetchone()
            conn.commit()
            sync_info = None
            next_status = status or sprint["status"]
            if next_status == "Completed":
                sync_info = _write_sync_manifest(
                    project_name=project_name,
                    sprint_name=updated_sprint["sprint_name"],
                    repo_path=(project or {}).get("repo_path", ""),
                )
            return {"status": "updated", "sprint": updated_sprint, "sync_info": sync_info}
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def create_backlog_item(
        project_name: str,
        task_name: str,
        description: str = "",
        sprint_name: str = "",
        status: str = "To Do",
        priority: str = "Medium",
        effort: str = "M",
        agent_tag: str = "",
    ):
        conn = get_db_conn()
        try:
            return create_backlog_item_record(conn, project_name, task_name, description, sprint_name, status, priority, effort, agent_tag)
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def update_backlog_item(
        project_name: str,
        task_name: str,
        description: str = "",
        sprint_name: str = "",
        status: str = "",
        priority: str = "",
        effort: str = "",
        agent_tag=None,
        new_task_name: str = "",
        allow_reassign: bool = False,
    ):
        conn = get_db_conn()
        try:
            return update_backlog_item_record(
                conn,
                project_name=project_name,
                current_task_name=task_name,
                description=description,
                sprint_name=sprint_name,
                status=status,
                priority=priority,
                effort=effort,
                agent_tag=agent_tag,
                new_task_name=new_task_name,
                allow_reassign=allow_reassign,
            )
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def assign_backlog_agent_tag(task_id: int, ai_tag: str):
        conn = get_db_conn()
        try:
            return assign_backlog_agent_tag_record(conn, task_id, ai_tag)
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def claim_backlog_item(project_name: str, task_name: str, agent_tag: str):
        conn = get_db_conn()
        try:
            return claim_backlog_item_record(conn, project_name, task_name, agent_tag)
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def release_backlog_item(project_name: str, task_name: str, agent_tag: str, next_status: str = "To Do"):
        conn = get_db_conn()
        try:
            return release_backlog_item_record(conn, project_name, task_name, agent_tag, next_status)
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def list_project_assets(project_name: str):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, project_name, description, repo_path FROM projects WHERE project_name = %s",
                    (project_name,),
                )
                project = cur.fetchone()
                if not project:
                    return {"error": f"Project '{project_name}' does not exist"}

                cur.execute("""
                    SELECT id, sprint_name, goals, status, start_date, end_date
                    FROM sprints
                    WHERE project_id = %s
                    ORDER BY start_date DESC
                """, (project["id"],))
                sprints = cur.fetchall()

                cur.execute("""
                    SELECT b.id, b.task_name, b.description, b.agent_tag, b.claim_status, b.claimed_at, b.claim_version, b.priority, b.effort, b.status, s.sprint_name
                    FROM backlog_items b
                    LEFT JOIN sprints s ON b.sprint_id = s.id
                    WHERE b.project_id = %s
                    ORDER BY b.created_at DESC
                """, (project["id"],))
                backlog = cur.fetchall()

            sync_status = None
            for manifest_path in _sync_manifest_paths(project_name):
                if os.path.exists(manifest_path):
                    sync_status = {"manifest_path": manifest_path}
                    break

            return {"project": project, "sprints": sprints, "backlog": backlog, "sync_status": sync_status}
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def list_backlog_claim_events(project_name: str, limit: int = 20):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                project = _get_project(cur, project_name)
                if not project:
                    return {"error": f"Project '{project_name}' does not exist"}
                cur.execute(
                    """
                    SELECT e.id, b.task_name, e.event_type, e.actor_agent_tag, e.previous_agent_tag, e.new_agent_tag, e.note, e.created_at
                    FROM backlog_claim_events e
                    JOIN backlog_items b ON b.id = e.backlog_item_id
                    WHERE b.project_id = %s
                    ORDER BY e.created_at DESC, e.id DESC
                    LIMIT %s
                    """,
                    (project["id"], limit),
                )
                rows = cur.fetchall()
            return {"project_name": project_name, "events": rows}
        finally:
            conn.close()

    @mcp.tool()
    @safe_tool
    def get_project_sync_status(project_name: str):
        for manifest_path in _sync_manifest_paths(project_name):
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    content = handle.read()
                return {"project_name": project_name, "manifest_path": manifest_path, "content": content}
        return {"error": f"No sync manifest found for project '{project_name}'"}
