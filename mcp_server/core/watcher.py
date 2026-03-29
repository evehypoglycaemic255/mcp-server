import os
import time
import threading
import logging
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
import psycopg2
from core.config import settings
from core.database import DATABASE_URL

DEBOUNCE_SECONDS = settings.WATCHDOG_DEBOUNCE
recent_events = {}

class ProjectWatchdogHandler(FileSystemEventHandler):
    def __init__(self, project_name):
        self.project_name = project_name

    def on_modified(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Ignore noisy and internal files to prevent infinite loops (Docs/Sprints)
        if any(ignore in filepath for ignore in settings.WATCHDOG_IGNORE): return
        if filename.endswith(".pyc") or filename.endswith(".log"): return
        
        current_time = time.time()
        last_time = recent_events.get(filepath, 0)
        
        if current_time - last_time > DEBOUNCE_SECONDS:
            recent_events[filepath] = current_time
            self.log_to_db(filepath)

    def log_to_db(self, filepath):
        # Đọc và Vector hoá Source Code tự động
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            from core.ast_analyzer import extract_semantic_chunks
            from core.vector_db import store_memory
            
            chunks = extract_semantic_chunks(content, filename=os.path.basename(filepath))
            parsed_count = 0
            
            for chunk in chunks:
                store_memory(self.project_name, chunk["content"], chunk["metadata"], is_codebase=True)
                parsed_count += 1
                
            print(f"[{time.strftime('%H:%M:%S')}] 🧠 AST Chunked & Vectorized {os.path.basename(filepath)} into {parsed_count} nodes.")
        except Exception as e:
            logging.error(f"Watchdog failed to vectorise: {e}")

        try:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
                # Find active sprint for the project
                cur.execute("""
                    SELECT p.id, s.id
                    FROM projects p
                    JOIN sprints s ON p.id = s.project_id
                    WHERE p.project_name = %s
                    AND s.status = 'Active'
                    LIMIT 1
                """, (self.project_name,))
                result = cur.fetchone()
                if not result:
                    return # Skip silently if no sprint active
                
                project_id, sprint_id = result
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                rel_path = os.path.relpath(filepath, project_root)
                
                cur.execute("""
                    INSERT INTO ai_sessions (
                        project_id, sprint_id, task_performed, implemented_logic, pending_tasks
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (project_id, sprint_id, "[System Auto-Watch] File Modified", f"Path: {rel_path}", ""))
                conn.commit()
                logging.info(f"Watchdog recorded change for {rel_path}")
        except Exception as e:
            logging.error(f"Watchdog DB error: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

def start_watcher(project_name="MCP_SERVER"):
    watch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Watch the whole repo
    logging.info(f"Starting Workspace Watchdog for {project_name} at {watch_dir}")
    event_handler = ProjectWatchdogHandler(project_name)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=True)
    
    # Daemon thread ensures the main process can still exit cleanly
    observer.daemon = True
    observer.start()
    return observer
