import os
import contextvars

current_user_role = contextvars.ContextVar("current_user_role", default="anonymous")

# Key => role mapping for API key auth
API_KEY_ROLE_MAPPING = {
    os.getenv("MCP_API_KEY", "default-api-key"): os.getenv("MCP_API_KEY_ROLE", "admin")
}

# Default secondary key for read-only
SECONDARY_API_KEY = os.getenv("MCP_API_READONLY_KEY", "readonly-api-key")
SECONDARY_API_ROLE = os.getenv("MCP_API_READONLY_ROLE", "readonly")

if SECONDARY_API_KEY:
    API_KEY_ROLE_MAPPING.setdefault(SECONDARY_API_KEY, SECONDARY_API_ROLE)


def validate_api_key(api_key: str) -> str:
    """Return role for given API key or raise ValueError."""
    if not api_key:
        raise ValueError("API key required")

    role = API_KEY_ROLE_MAPPING.get(api_key)
    if not role:
        raise ValueError("Invalid API key")

    return role


def set_current_user_role(role: str):
    return current_user_role.set(role)


def get_current_user_role() -> str:
    return current_user_role.get("anonymous")


def reset_current_user_role(token):
    current_user_role.reset(token)
