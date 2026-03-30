import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Response, status
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

from plugins import register_all_tools, sync_active_tool_catalog
from core.watcher import start_watcher
from core.config import settings
from core.security import validate_api_key, set_current_user_role, reset_current_user_role, get_current_user_role

logging.basicConfig(level=logging.INFO)

# ==============================
# MCP INIT & AUTO-REGISTER PLUGINS
# ==============================
mcp = FastMCP("Tris-MCP-API")
register_all_tools(mcp)
sync_active_tool_catalog(mcp)

# ==============================
# FASTAPI ROOT (SSE)
# ==============================
app = FastAPI(title="Tris AI Forge Gateway")

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "MCP server is running in Plugin Architecture",
        "sse_url": "/mcp/sse",
        "auth_enabled": settings.AUTH_ENABLED,
    }


@app.get("/health")
def health(request: Request):
    if settings.HEALTHCHECK_SECRET:
        token = request.headers.get("x-healthcheck-token")
        if token != settings.HEALTHCHECK_SECRET:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid healthcheck token")

    from core.database import get_db_conn

    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "healthy", "db": "ok", "role": get_current_user_role()}
    finally:
        conn.close()


@app.get("/metrics")
def metrics():
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from core.metrics import registry

        return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
    except Exception as exc:
        logging.warning("Metrics endpoint unavailable: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Metrics backend not available")

sse_transport = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    if settings.AUTH_ENABLED:
        api_key = request.headers.get(settings.API_KEY_HEADER)
        try:
            role = validate_api_key(api_key)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    else:
        role = "anonymous"

    token = set_current_user_role(role)
    logging.info("SSE connection auth role=%s", role)
    try:
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await mcp._mcp_server.run(read_stream, write_stream, mcp._mcp_server.create_initialization_options())
    finally:
        reset_current_user_role(token)

sse_app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Mount("/messages/", app=sse_transport.handle_post_message),
])
app.mount("/mcp", sse_app)

if __name__ == "__main__":
    from core.config import settings
    start_watcher(settings.DEFAULT_PROJECT_NAME)
    if "--sse" in sys.argv:
        uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT)
    else:
        # stdio mode = local trusted connection, grant admin role
        set_current_user_role("admin")
        mcp.run()
