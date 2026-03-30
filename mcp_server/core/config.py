import logging
import os
import json
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))


def _load_json_config(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"Warning: JSON config not loaded. {exc}")
        return {}


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logging.warning("CRITICAL MISSING DATABASE_URL. Core engine may fail without DB connection.")

    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "chroma").lower()
    DEFAULT_PROJECT_NAME = os.getenv("MCP_DEFAULT_PROJECT", "MCP_SERVER")
    DEFAULT_SPRINT_NAME = os.getenv("MCP_DEFAULT_SPRINT", "System Bootstrap")
    WORKSPACE_ROOT = os.getenv("MCP_WORKSPACE_ROOT", os.path.dirname(base_dir))

    _json_config = _load_json_config(os.path.join(base_dir, "config", "mcp_config.json"))

    SEARCH_LIMIT = _json_config.get("vector_db", {}).get("search_limit_default", 5)
    EMBEDDING_MODEL = _json_config.get("vector_db", {}).get("embedding_model", "all-MiniLM-L6-v2")

    SERVER_HOST = _json_config.get("server", {}).get("host", "0.0.0.0")
    SERVER_PORT = _json_config.get("server", {}).get("port", 8000)

    WATCHDOG_DEBOUNCE = _json_config.get("watchdog", {}).get("debounce_seconds", 5)
    WATCHDOG_MAX_SIZE = _json_config.get("watchdog", {}).get("max_file_size_bytes", 10000)
    WATCHDOG_IGNORE = _json_config.get("watchdog", {}).get("ignored_patterns", [".git", "__pycache__", "chroma"])
    WATCHDOG_ROOTS = _json_config.get("watchdog", {}).get("roots", ["mcp_server", "projects", "rules"])

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REMOTE_ENABLED = _json_config.get("github", {}).get("remote_api_enabled", False)
    GITHUB_PREFIX = _json_config.get("github", {}).get("default_branch_prefix", "ai-feature/")

    AUTH_ENABLED = os.getenv("MCP_AUTH_ENABLED", "true").lower() in {"1", "true", "yes"}
    API_KEY_HEADER = os.getenv("MCP_API_KEY_HEADER", "x-api-key")
    HEALTHCHECK_SECRET = os.getenv("MCP_HEALTHCHECK_SECRET", "")

    RBAC_ADMIN_TOOLS = _json_config.get("rbac", {}).get("admin_tools", ["create_sprint", "update_sprint", "upsert_project", "delete_project"])

    PROJECT_ROOT = WORKSPACE_ROOT


settings = Settings()
