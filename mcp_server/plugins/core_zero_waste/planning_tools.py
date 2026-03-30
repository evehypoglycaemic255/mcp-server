import uuid

from core.config import settings
from core.database import get_db_conn
from core.dependencies import safe_tool


def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def create_execution_plan(
        task_intent: str,
        target_files: list,
        strategy_type: str,
        project_name: str = settings.DEFAULT_PROJECT_NAME,
    ) -> dict:
        """Create a tracked execution plan and log it into ai_sessions for the active sprint."""
        plan_id = str(uuid.uuid4())[:8]
        conn = get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_sessions (
                        project_id,
                        sprint_id,
                        task_performed,
                        implemented_logic,
                        pending_tasks
                    )
                    SELECT
                        p.id,
                        s.id,
                        %s,
                        %s,
                        %s
                    FROM projects p
                    JOIN sprints s ON p.id = s.project_id
                    WHERE p.project_name = %s
                    AND s.status = 'Active'
                    LIMIT 1
                    """,
                    (
                        f"Plan [{plan_id}]: {task_intent}",
                        f"Targets: {target_files} | Strategy: {strategy_type}",
                        "Awaiting execution",
                        project_name,
                    ),
                )
                if cur.rowcount == 0:
                    return {"error": f"No active sprint found for project '{project_name}'"}
            conn.commit()
            return {
                "status": "APPROVED",
                "plan_id": plan_id,
                "directive": f"Strategy {strategy_type} locked for {target_files}. Proceed to validation/sandbox.",
                "enforced_targets": target_files,
                "project_name": project_name,
            }
        finally:
            conn.close()
