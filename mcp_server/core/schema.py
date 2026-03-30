import os


DEFAULT_PROJECT_NAME = os.getenv("MCP_DEFAULT_PROJECT", "MCP_SERVER")
DEFAULT_SPRINT_NAME = os.getenv("MCP_DEFAULT_SPRINT", "System Bootstrap")


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                project_name TEXT UNIQUE NOT NULL,
                description TEXT,
                repo_path TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sprints (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                sprint_name TEXT NOT NULL,
                goals TEXT,
                status TEXT DEFAULT 'Active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backlog_items (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                sprint_id INTEGER REFERENCES sprints(id),
                task_name TEXT NOT NULL,
                description TEXT,
                agent_tag TEXT DEFAULT '',
                claim_status TEXT DEFAULT 'Unclaimed',
                claimed_at TIMESTAMP,
                claim_version INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'Medium',
                effort TEXT DEFAULT 'M',
                status TEXT DEFAULT 'To Do',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backlog_claim_events (
                id SERIAL PRIMARY KEY,
                backlog_item_id INTEGER REFERENCES backlog_items(id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                actor_agent_tag TEXT DEFAULT '',
                previous_agent_tag TEXT DEFAULT '',
                new_agent_tag TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_sessions (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                sprint_id INTEGER REFERENCES sprints(id),
                task_performed TEXT,
                implemented_logic TEXT,
                pending_tasks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_tool_logs (
                id SERIAL PRIMARY KEY,
                tool_name VARCHAR(255),
                parameters JSONB,
                status VARCHAR(50),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS repo_path TEXT")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS description TEXT")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS agent_tag TEXT DEFAULT ''")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS claim_status TEXT DEFAULT 'Unclaimed'")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMP")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS claim_version INTEGER DEFAULT 0")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'Medium'")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS effort TEXT DEFAULT 'M'")
        cur.execute("ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        cur.execute("ALTER TABLE system_tool_logs ALTER COLUMN parameters TYPE JSONB USING parameters::jsonb")
        cur.execute("""
            INSERT INTO projects (project_name, description, repo_path)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_name)
            DO NOTHING
        """, (
            DEFAULT_PROJECT_NAME,
            "Default MCP Commander tracking project",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
        ))
        cur.execute("SELECT id FROM projects WHERE project_name = %s", (DEFAULT_PROJECT_NAME,))
        project_row = cur.fetchone()
        if project_row:
            project_id = project_row[0]
            cur.execute("""
                INSERT INTO sprints (project_id, sprint_name, goals, status)
                SELECT %s, %s, %s, 'Active'
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM sprints
                    WHERE project_id = %s AND status = 'Active'
                )
            """, (
                project_id,
                DEFAULT_SPRINT_NAME,
                "Default active sprint created automatically to align runtime assumptions.",
                project_id,
            ))
    conn.commit()
