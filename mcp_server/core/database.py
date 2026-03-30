import os
import psycopg2
import time
import logging
from core.config import settings
from core.schema import ensure_schema

DATABASE_URL = settings.DATABASE_URL

def get_db_conn():
    for i in range(5):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            ensure_schema(conn)
            return conn
        except Exception as e:
            logging.error(f"DB connect fail (try {i+1}): {e}")
            time.sleep(3)
    raise Exception("❌ Cannot connect DB")
