import importlib
import logging
import os
import yaml

from datetime import datetime
from pathlib import Path

# ==============================
# ADAPTIVE MCP LOADER v2
# ==============================
# Chỉ load cluster "always_on" khi boot.
# Các cluster khác (code_execution, git_devops, planning_brain)
# được load/unload on-demand qua tool switch_tool_cluster().

# Global state: theo dõi cluster nào đang active
_active_clusters = set()
_cluster_registry = {}  # cluster_name -> [plugin_folder, ...]
_mcp_ref = None  # reference tới FastMCP instance


def _read_plugin_yaml(yaml_path):
    try:
        with open(yaml_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:
        logging.error(f"Error parsing YAML: {yaml_path}: {exc}")
        return {}


def _sync_plugin_metadata(yaml_path, cfg, tool_names):
    cfg["tool_count"] = len(tool_names)
    cfg["tools"] = tool_names
    cfg["last_tool_catalog_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(yaml_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(cfg, handle, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _load_plugin_tools(mcp, plugin_folder, base_dir):
    """Load một plugin cụ thể và return danh sách tool names đã thêm."""
    try:
        module = importlib.import_module(f"plugins.{plugin_folder}")
        if hasattr(module, "register_tools"):
            before_tools = {tool.name for tool in mcp._tool_manager.list_tools()}
            module.register_tools(mcp)
            after_tools = {tool.name for tool in mcp._tool_manager.list_tools()}
            added = sorted(after_tools - before_tools)

            yaml_path = os.path.join(base_dir, plugin_folder, "plugin.yaml")
            if os.path.exists(yaml_path):
                cfg = _read_plugin_yaml(yaml_path)
                _sync_plugin_metadata(yaml_path, cfg, added)

            return added
    except Exception as e:
        logging.error(f"Failed to load plugin {plugin_folder}: {e}")
    return []


def _unload_plugin_tools(mcp, plugin_folder, base_dir):
    """Unload tất cả tools của một plugin."""
    yaml_path = os.path.join(base_dir, plugin_folder, "plugin.yaml")
    if not os.path.exists(yaml_path):
        return []

    cfg = _read_plugin_yaml(yaml_path)
    tool_names = cfg.get("tools", [])
    removed = []
    for tool_name in tool_names:
        try:
            mcp._tool_manager.remove_tool(tool_name)
            removed.append(tool_name)
        except Exception:
            pass  # tool might not exist

    # Update yaml
    cfg["tools"] = []
    cfg["tool_count"] = 0
    cfg["last_tool_catalog_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(yaml_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(cfg, handle, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return removed


def _build_cluster_registry(base_dir):
    """Scan tất cả plugin folders, build map cluster -> [plugin_folders]."""
    registry = {}
    for plugin_folder in sorted(os.listdir(base_dir)):
        p_dir = os.path.join(base_dir, plugin_folder)
        if not os.path.isdir(p_dir) or plugin_folder.startswith("__"):
            continue

        yaml_path = os.path.join(p_dir, "plugin.yaml")
        if not os.path.exists(yaml_path):
            continue

        cfg = _read_plugin_yaml(yaml_path)
        if not cfg.get("enabled", True):
            continue

        cluster = cfg.get("cluster", "always_on")
        registry.setdefault(cluster, []).append(plugin_folder)

    return registry


def register_all_tools(mcp):
    """Adaptive boot: chỉ load cluster 'always_on'. Các cluster khác chờ lệnh."""
    global _mcp_ref, _cluster_registry, _active_clusters
    _mcp_ref = mcp

    logging.info("Adaptive MCP Loader v2: Scanning plugins...")
    base_dir = os.path.dirname(os.path.abspath(__file__))

    _cluster_registry = _build_cluster_registry(base_dir)

    # Chỉ load always_on cluster khi boot
    boot_cluster = "always_on"
    count = 0
    for plugin_folder in _cluster_registry.get(boot_cluster, []):
        added = _load_plugin_tools(mcp, plugin_folder, base_dir)
        if added:
            logging.info(f"✅ [always_on] Loaded: {plugin_folder} ({len(added)} tools)")
            count += len(added)

    _active_clusters.add(boot_cluster)

    all_clusters = sorted(_cluster_registry.keys())
    deferred = [c for c in all_clusters if c != boot_cluster]

    logging.info(f"🎯 Boot complete: {count} tools loaded (always_on only)")
    logging.info(f"📦 Available clusters for on-demand: {deferred}")
    logging.info(f"💡 Use switch_tool_cluster() to activate: {deferred}")


def activate_cluster(cluster_name: str) -> dict:
    """Kích hoạt một cluster: load tất cả plugins của nó."""
    global _active_clusters
    if not _mcp_ref:
        return {"error": "MCP not initialized"}

    if cluster_name in _active_clusters:
        return {"status": "already_active", "cluster": cluster_name}

    if cluster_name not in _cluster_registry:
        return {"error": f"Unknown cluster '{cluster_name}'", "available": sorted(_cluster_registry.keys())}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    all_added = []
    for plugin_folder in _cluster_registry[cluster_name]:
        added = _load_plugin_tools(_mcp_ref, plugin_folder, base_dir)
        all_added.extend(added)
        if added:
            logging.info(f"✅ [{cluster_name}] Loaded: {plugin_folder} ({len(added)} tools)")

    _active_clusters.add(cluster_name)
    return {
        "status": "activated",
        "cluster": cluster_name,
        "tools_loaded": all_added,
        "active_clusters": sorted(_active_clusters),
    }


def deactivate_cluster(cluster_name: str) -> dict:
    """Tắt một cluster: unload tất cả tools của nó."""
    global _active_clusters
    if not _mcp_ref:
        return {"error": "MCP not initialized"}

    if cluster_name == "always_on":
        return {"error": "Cannot deactivate always_on cluster"}

    if cluster_name not in _active_clusters:
        return {"status": "already_inactive", "cluster": cluster_name}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    all_removed = []
    for plugin_folder in _cluster_registry.get(cluster_name, []):
        removed = _unload_plugin_tools(_mcp_ref, plugin_folder, base_dir)
        all_removed.extend(removed)
        if removed:
            logging.info(f"🔌 [{cluster_name}] Unloaded: {plugin_folder} ({len(removed)} tools)")

    _active_clusters.discard(cluster_name)
    return {
        "status": "deactivated",
        "cluster": cluster_name,
        "tools_removed": all_removed,
        "active_clusters": sorted(_active_clusters),
    }


def get_cluster_status() -> dict:
    """Trả về trạng thái hiện tại của tất cả clusters."""
    result = {}
    for cluster_name, plugins in sorted(_cluster_registry.items()):
        result[cluster_name] = {
            "active": cluster_name in _active_clusters,
            "plugins": plugins,
        }
    return result


def sync_active_tool_catalog(mcp):
    """Ghi lại catalog markdown cho các plugins đang active."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    active_tools = {tool.name for tool in mcp._tool_manager.list_tools()}
    plugin_summaries = []

    for plugin_folder in os.listdir(base_dir):
        p_dir = os.path.join(base_dir, plugin_folder)
        if not os.path.isdir(p_dir) or plugin_folder.startswith("__"):
            continue

        yaml_path = os.path.join(p_dir, "plugin.yaml")
        if not os.path.exists(yaml_path):
            continue

        cfg = _read_plugin_yaml(yaml_path)
        if not cfg.get("enabled", True):
            continue

        tool_names = [t for t in cfg.get("tools", []) if t in active_tools]
        _sync_plugin_metadata(yaml_path, cfg, tool_names)
        plugin_summaries.append({
            "folder": plugin_folder,
            "name": cfg.get("name", plugin_folder),
            "description": cfg.get("description", ""),
            "owner": cfg.get("owner", ""),
            "version": cfg.get("version", ""),
            "managed_in": cfg.get("managed_in", []),
            "cluster": cfg.get("cluster", "always_on"),
            "tool_count": len(tool_names),
            "tools": tool_names,
        })

    # Write catalog markdown
    docs_dir = Path(base_dir).resolve().parents[1] / "docs" / "architecture"
    docs_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = docs_dir / "active_tool_catalog.md"

    total_tools = sum(item["tool_count"] for item in plugin_summaries)
    lines = [
        "# Active Tool Catalog (Adaptive Loader v2)",
        "",
        f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- `{len(plugin_summaries)}` plugins registered",
        f"- `{total_tools}` tools currently loaded",
        f"- Active clusters: `{sorted(_active_clusters)}`",
        "",
        "| Plugin | Cluster | Tools |",
        "|---|---|---:|",
    ]
    for item in plugin_summaries:
        lines.append(f"| `{item['folder']}` | `{item['cluster']}` | {item['tool_count']} |")
    lines.append("")

    catalog_path.write_text("\n".join(lines), encoding="utf-8")
    return str(catalog_path)
