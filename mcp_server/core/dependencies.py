import functools
import logging
import json

def safe_tool(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # Format params để nhét vào DB
        try:
            params_json = json.dumps(kwargs, ensure_ascii=False)
        except Exception:
            params_json = "{}"
            
        status = "SUCCESS"
        message = ""
        
        try:
            result = fn(*args, **kwargs)
            message = str(result)[:500] # Giới hạn để khỏi tràn ổ cứng
            return result
        except Exception as e:
            status = "ERROR"
            message = str(e)
            logging.error(f"🔥 TOOL ERROR {fn.__name__}: {e}")
            return {"error": str(e)}
        finally:
            # Luộn bắn log ngầm xuống Database
            try:
                from core.database import get_db_conn
                conn = get_db_conn()
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO system_tool_logs (tool_name, parameters, status, message) VALUES (%s, %s, %s, %s)",
                        (fn.__name__, params_json, status, message)
                    )
                conn.commit()
                conn.close()
            except Exception as dbe:
                logging.error(f"Lỗi Middleware Tool Logger: {dbe}")
                
    return wrapper
