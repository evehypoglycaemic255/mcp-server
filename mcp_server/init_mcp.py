from core.config import settings
from core.database import get_db_conn


def init_project():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (project_name, description, repo_path)
                VALUES (%s, %s, %s)
                ON CONFLICT (project_name)
                DO UPDATE SET description = EXCLUDED.description, repo_path = EXCLUDED.repo_path
                """,
                (
                    settings.DEFAULT_PROJECT_NAME,
                    "Default MCP Commander tracking project",
                    settings.PROJECT_ROOT,
                ),
            )
            cur.execute("SELECT id FROM projects WHERE project_name = %s", (settings.DEFAULT_PROJECT_NAME,))
            project_row = cur.fetchone()
            if project_row:
                project_id = project_row[0]
                cur.execute(
                    """
                    INSERT INTO sprints (project_id, sprint_name, goals, status)
                    SELECT %s, %s, %s, 'Active'
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM sprints
                        WHERE project_id = %s AND status = 'Active'
                    )
                    """,
                    (
                        project_id,
                        settings.DEFAULT_SPRINT_NAME,
                        "Bootstrap sprint created automatically during MCP initialization.",
                        project_id,
                    ),
                )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_project()
