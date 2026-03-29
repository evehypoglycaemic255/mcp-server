import psycopg2
import time

def run():
    for _ in range(5):
        try:
            from core.config import settings
            conn = psycopg2.connect(settings.DATABASE_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO projects (project_name) VALUES ('MCP_SERVER') ON CONFLICT DO NOTHING")
            cur.execute("INSERT INTO projects (project_name) VALUES ('DemoProject') ON CONFLICT DO NOTHING")
            
            cur.execute("INSERT INTO sprints (project_id, sprint_name, status) SELECT id, 'Sprint 1', 'Active' FROM projects WHERE project_name='MCP_SERVER' LIMIT 1")
            conn.commit()
            conn.close()
            print("DB Seeded.")
            return
        except Exception as e:
            print("Waiting for DB:", e)
            time.sleep(2)

if __name__ == "__main__":
    run()
