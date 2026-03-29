import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import FastAPI
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

from plugins import register_all_tools
from core.watcher import start_watcher

logging.basicConfig(level=logging.INFO)

# ==============================
# MCP INIT & AUTO-REGISTER PLUGINS
# ==============================
mcp = FastMCP("Tris-MCP-API")
register_all_tools(mcp)

# ==============================
# FASTAPI ROOT (SSE)
# ==============================
app = FastAPI(title="Tris AI Forge Gateway")

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "MCP server is running in Plugin Architecture",
        "sse_url": "/mcp/sse"
    }

sse_transport = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp._mcp_server.run(read_stream, write_stream, mcp._mcp_server.create_initialization_options())

sse_app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Mount("/messages/", app=sse_transport.handle_post_message),
])
app.mount("/mcp", sse_app)

if __name__ == "__main__":
    from core.config import settings
    start_watcher()
    if "--sse" in sys.argv:
        print(f"🚀 [SSE Mode] MCP mounted at /mcp")
        print(f"👉 SSE: http://localhost:{settings.SERVER_PORT}/mcp/sse")
        uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT)
    else:
        mcp.run()