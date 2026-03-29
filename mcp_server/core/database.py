import os
import psycopg2
import time
import logging
from core.config import settings

DATABASE_URL = settings.DATABASE_URL

def get_db_conn():
    for i in range(5):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
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
            conn.commit()
            return conn
        except Exception as e:
            logging.error(f"DB connect fail (try {i+1}): {e}")
            time.sleep(3)
    raise Exception("❌ Cannot connect DB")
