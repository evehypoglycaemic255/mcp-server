import psycopg2
import os

DATABASE_URL = "postgresql://mcp:mcp@localhost:5434/mcp_server_db"

def init_project():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO projects (project_name, description) 
            VALUES ('MCP_SERVER', 'Cỗ máy Trí nhớ AI tự động') 
            ON CONFLICT (project_name) DO NOTHING;
        """)
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    init_project()
