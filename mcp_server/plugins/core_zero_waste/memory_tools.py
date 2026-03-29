from psycopg2.extras import RealDictCursor
from core.database import get_db_conn
from core.dependencies import safe_tool

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def log_session_v2(project_name: str, task: str, logic: str, pending: str):
        conn = get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
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
                        %s, %s, %s
                    FROM projects p
                    JOIN sprints s ON p.id = s.project_id
                    WHERE p.project_name = %s
                    AND s.status = 'Active'
                    LIMIT 1
                """, (task, logic, pending, project_name))

                conn.commit()
                return {"status": "logged"}
        finally:
            conn.close()


    @mcp.tool()
    def get_project_context(project_name: str):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.session_date, s.task_performed, s.implemented_logic, s.pending_tasks
                    FROM ai_sessions s
                    JOIN projects p ON s.project_id = p.id
                    WHERE p.project_name = %s
                    ORDER BY s.session_date DESC LIMIT 3;
                """, (project_name,))
                return cur.fetchall()
        finally:
            conn.close()
