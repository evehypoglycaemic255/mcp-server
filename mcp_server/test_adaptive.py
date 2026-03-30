import sys, os
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'postgresql://mcp:mcp@localhost:5434/mcp_server_db'

import logging
logging.disable(logging.CRITICAL)  # suppress noise

from mcp.server.fastmcp import FastMCP
from plugins import register_all_tools, get_cluster_status, activate_cluster, deactivate_cluster

mcp = FastMCP('test')
register_all_tools(mcp)

tools = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"=== BOOT ({len(tools)} tools) ===")
for t in tools:
    print(f"  - {t}")

print()
status = get_cluster_status()
for cluster, info in sorted(status.items()):
    marker = "ACTIVE" if info["active"] else "DEFERRED"
    print(f"  [{marker}] {cluster}: {info['plugins']}")

print()
print("=== ACTIVATE code_execution ===")
result = activate_cluster("code_execution")
print(f"  Status: {result['status']}")
print(f"  Tools loaded: {result.get('tools_loaded', [])}")

tools2 = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"  Total tools now: {len(tools2)}")

print()
print("=== DEACTIVATE code_execution ===")
result2 = deactivate_cluster("code_execution")
print(f"  Status: {result2['status']}")
print(f"  Tools removed: {result2.get('tools_removed', [])}")

tools3 = sorted([t.name for t in mcp._tool_manager.list_tools()])
print(f"  Total tools now: {len(tools3)}")
for t in tools3:
    print(f"  - {t}")
