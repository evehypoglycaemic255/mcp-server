"""Gateway tools for Adaptive MCP Loader: enable/disable tool clusters on demand."""

from core.dependencies import safe_tool


def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def get_available_clusters() -> dict:
        """List all tool clusters and their activation status."""
        from plugins import get_cluster_status
        return get_cluster_status()

    @mcp.tool()
    @safe_tool
    def switch_tool_cluster(cluster_name: str, action: str = "enable") -> dict:
        """Enable or disable a tool cluster on demand. Action: 'enable' or 'disable'."""
        from plugins import activate_cluster, deactivate_cluster
        if action == "enable":
            return activate_cluster(cluster_name)
        elif action == "disable":
            return deactivate_cluster(cluster_name)
        else:
            return {"error": f"Unknown action '{action}'. Use 'enable' or 'disable'."}
