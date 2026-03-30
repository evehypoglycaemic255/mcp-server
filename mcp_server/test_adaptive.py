import sys, os
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'postgresql://mcp:mcp@localhost:5434/mcp_server_db'

import logging
logging.disable(logging.CRITICAL)

from mcp.server.fastmcp import FastMCP
from plugins import register_all_tools, get_cluster_status, activate_cluster, deactivate_cluster

mcp = FastMCP('test')
register_all_tools(mcp)

tools = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"=== BOOT: {len(tools)} tools (always_on only) ===")
for t in tools:
    print(f"  - {t}")

print()
status = get_cluster_status()
for cluster, info in sorted(status.items()):
    marker = "ON " if info["active"] else "OFF"
    print(f"  [{marker}] {cluster}: {info['plugins']}")

print()
print("=== ACTIVATE project_backlog ===")
r = activate_cluster("project_backlog")
tools2 = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"  Now: {len(tools2)} tools (+{len(tools2)-len(tools)})")
for t in sorted(set(tools2) - set(tools)):
    print(f"    + {t}")

print()
print("=== ACTIVATE ALL clusters ===")
for c in ["code_execution", "git_devops", "planning_brain"]:
    activate_cluster(c)
all_tools = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"  Full load: {len(all_tools)} tools")

print()
print("=== DEACTIVATE ALL (except always_on) ===")
for c in ["project_backlog", "code_execution", "git_devops", "planning_brain"]:
    deactivate_cluster(c)
min_tools = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"  Minimal: {len(min_tools)} tools")
for t in min_tools:
    print(f"  - {t}")
