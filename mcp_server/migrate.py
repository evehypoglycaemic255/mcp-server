import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mcp:mcp@localhost:5434/mcp_server_db")

def run_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS backlog_items (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES projects(id),
            sprint_id INTEGER REFERENCES sprints(id), -- NULL neu o trang thai backlog cho
            task_name TEXT NOT NULL,
            status TEXT DEFAULT 'To Do', -- [To Do, In Progress, Blocked, Done, Cancelled]
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Cung cấp một Task mẫu cho Sprint 1 cua MCP_SERVER
        cur.execute("SELECT id FROM projects WHERE project_name='MCP_SERVER' LIMIT 1")
        res_p = cur.fetchone()
        if res_p:
            project_id = res_p[0]
            cur.execute("SELECT id FROM sprints WHERE sprint_name='Sprint 1' AND project_id=%s", (project_id,))
            res_s = cur.fetchone()
            sprint_id = res_s[0] if res_s else None
            
            cur.execute("INSERT INTO backlog_items (project_id, sprint_id, task_name, status) VALUES (%s, %s, %s, %s)", 
                        (project_id, sprint_id, "Tái cấu trúc UI thành 3 Tabs", "In Progress"))
            
            cur.execute("INSERT INTO backlog_items (project_id, sprint_id, task_name, status) VALUES (%s, NULL, %s, %s)", 
                        (project_id, "Tích hợp Slack Notification", "To Do"))
            
        conn.commit()
        print("✅ Migration Database thành công!")
    except Exception as e:
        print(f"❌ Migration Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run_migration()
