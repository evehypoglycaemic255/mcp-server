import functools
import json
import logging
from time import perf_counter
from core.metrics import tool_calls_counter, tool_latency


SENSITIVE_KEYS = {"token", "password", "secret", "authorization", "api_key", "prompt", "content", "body"}


def _sanitize_payload(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _sanitize_payload(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_payload(item) for item in value)
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "...[truncated]"
    return value


def safe_tool(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        from core.security import get_current_user_role
        from core.config import settings

        role = get_current_user_role()

        try:
            params_json = json.dumps(_sanitize_payload(kwargs), ensure_ascii=False)
        except Exception:
            params_json = "{}"

        status = "SUCCESS"
        message = ""

        # RBAC enforcement
        if settings.AUTH_ENABLED and fn.__name__ in settings.RBAC_ADMIN_TOOLS and role != "admin":
            status = "FORBIDDEN"
            message = f"RBAC denied: {role} cannot execute {fn.__name__}"
            logging.warning(message)
            return {"error": message}

        start_ts = perf_counter()
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, dict) and result.get("error"):
                status = "ERROR"
            message = str(_sanitize_payload(result))[:500]
            return result
        except Exception as exc:
            status = "ERROR"
            message = str(_sanitize_payload(str(exc)))
            logging.error("TOOL ERROR %s: %s", fn.__name__, exc)
            return {"error": str(exc)}
        finally:
            duration = perf_counter() - start_ts
            try:
                tool_calls_counter.labels(tool_name=fn.__name__, status=status).inc()
                tool_latency.labels(tool_name=fn.__name__).observe(duration)
            except Exception:
                logging.warning("Metrics update failed for tool %s", fn.__name__)

            try:
                from core.database import get_db_conn

                conn = get_db_conn()
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO system_tool_logs (tool_name, parameters, status, message) VALUES (%s, %s, %s, %s)",
                        (fn.__name__, params_json, status, message),
                    )
                conn.commit()
                conn.close()
            except Exception as dbe:
                logging.error("Tool logger error: %s", dbe)

    return wrapper
