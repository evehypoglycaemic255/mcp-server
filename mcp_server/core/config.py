import os
import json
from dotenv import load_dotenv

# Tìm file .env từ thư mục gốc mcp_server
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

def _load_json_config(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: JSON config not loaded. {e}")
        return {}

class Settings:
    # 1. From Environment Variables (.env) - Sensitive/Infrastructure
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Critical warning if .env was not loaded properly
        logging.warning("⚠️ CRITICAL MISSING DATABASE_URL! Core Engine might fail without DB connection.")
    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "chroma").lower()
    
    # 2. Config from JSON - Operations
    _json_config = _load_json_config(os.path.join(base_dir, "config", "mcp_config.json"))
    
    # Vector DB limits
    SEARCH_LIMIT = _json_config.get("vector_db", {}).get("search_limit_default", 5)
    
    # API Server Config
    SERVER_HOST = _json_config.get("server", {}).get("host", "0.0.0.0")
    SERVER_PORT = _json_config.get("server", {}).get("port", 8000)
    
    # 3. Git & Github Configs (V10)
    WATCHDOG_DEBOUNCE = _json_config.get("watchdog", {}).get("debounce_seconds", 5)
    WATCHDOG_MAX_SIZE = _json_config.get("watchdog", {}).get("max_file_size_bytes", 10000)
    WATCHDOG_IGNORE = _json_config.get("watchdog", {}).get("ignored_patterns", [".git", "__pycache__", "chroma"])
    
    # Machine Learning Model RAG Parameters
    EMBEDDING_MODEL = _json_config.get("vector_db", {}).get("embedding_model", "all-MiniLM-L6-v2")
    SEARCH_LIMIT = _json_config.get("vector_db", {}).get("search_limit_default", 5)
    
    # Tham số API Server
    SERVER_HOST = _json_config.get("server", {}).get("host", "0.0.0.0")
    SERVER_PORT = _json_config.get("server", {}).get("port", 8000)
    
    # 3. Tham số Git & Github (V10)
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REMOTE_ENABLED = _json_config.get("github", {}).get("remote_api_enabled", False)
    GITHUB_PREFIX = _json_config.get("github", {}).get("default_branch_prefix", "ai-feature/")
    
    # Absolute Root System Memory 
    PROJECT_ROOT = base_dir

settings = Settings()
