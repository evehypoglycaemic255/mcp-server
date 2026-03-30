import importlib
import pkgutil
import logging
import os
import yaml

from datetime import datetime
from pathlib import Path


def _sync_plugin_metadata(yaml_path, cfg, tool_names):
    cfg["tool_count"] = len(tool_names)
    cfg["tools"] = tool_names
    cfg["last_tool_catalog_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(yaml_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(cfg, handle, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _write_active_tool_catalog(base_dir, plugin_summaries):
    docs_dir = Path(base_dir).resolve().parents[1] / "docs" / "architecture"
    docs_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = docs_dir / "active_tool_catalog.md"

    total_tools = sum(item["tool_count"] for item in plugin_summaries)
    lines = [
        "# Active Tool Catalog",
        "",
        f"Ngay cap nhat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Nguon chuan: auto-generated tu tool registry thuc te + plugin metadata",
        "",
        "## Muc dich",
        "",
        "Tai lieu nay la danh ba tra cuu nhanh cho AI agent va coder.",
        "He thong tu dong sinh lai file nay khi MCP server boot va hoan tat plugin auto-registration.",
        "",
        "## Tong quan",
        "",
        f"- `{len(plugin_summaries)}` plugin active",
        f"- `{total_tools}` tool active",
        "",
        "## Quick Map",
        "",
        "| Plugin | Muc dich | Managed In | So tool |",
        "|---|---|---|---:|",
    ]

    for item in plugin_summaries:
        managed_in = ", ".join(f"`{place}`" for place in item["managed_in"]) or "`MCP Server tools`"
        lines.append(
            f"| `{item['folder']}` | {item['description']} | {managed_in} | {item['tool_count']} |"
        )

    lines.extend(["", "## Theo Plugin", ""])

    for index, item in enumerate(plugin_summaries, start=1):
        lines.extend([f"### {index}. `{item['folder']}`", "", "Managed in:"])
        if item["managed_in"]:
            lines.extend([f"- `{place}`" for place in item["managed_in"]])
        else:
            lines.append("- `MCP Server tools`")
        lines.extend(
            [
                "",
                f"- Owner: `{item['owner'] or 'Unassigned'}`",
                f"- Version: `{item['version'] or 'N/A'}`",
                "",
                "| Tool | Muc dich nhanh |",
                "|---|---|",
            ]
        )
        for tool_name in item["tools"]:
            lines.append(f"| `{tool_name}` | Thuoc plugin `{item['folder']}` |")
        lines.append("")

    lines.extend(
        [
            "## Ghi chu",
            "",
            "- File nay duoc sinh tu dong. Khong can cap nhat tay khi them tool moi.",
            "- Neu plugin moi duoc dang ky thanh cong, lan boot tiep theo se tu dong cap nhat catalog.",
            "- Agent co the doc nhanh catalog nay thay vi quet lai toan bo codebase.",
            "",
        ]
    )

    catalog_path.write_text("\n".join(lines), encoding="utf-8")
    return str(catalog_path)


def sync_active_tool_catalog(mcp):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_summaries = []
    active_tools = {tool.name for tool in mcp._tool_manager.list_tools()}

    for plugin_folder in os.listdir(base_dir):
        p_dir = os.path.join(base_dir, plugin_folder)
        if not os.path.isdir(p_dir) or plugin_folder.startswith("__"):
            continue

        yaml_path = os.path.join(p_dir, "plugin.yaml")
        if not os.path.exists(yaml_path):
            continue

        try:
            with open(yaml_path, "r", encoding="utf-8") as handle:
                cfg = yaml.safe_load(handle) or {}
        except Exception as exc:
            logging.error(f"Error parsing YAML for {plugin_folder}: {exc}")
            continue

        if not cfg.get("enabled", True):
            continue

        tool_names = [tool_name for tool_name in cfg.get("tools", []) if tool_name in active_tools]
        _sync_plugin_metadata(yaml_path, cfg, tool_names)
        plugin_summaries.append(
            {
                "folder": plugin_folder,
                "name": cfg.get("name", plugin_folder),
                "description": cfg.get("description", "No description provided"),
                "owner": cfg.get("owner", ""),
                "version": cfg.get("version", ""),
                "managed_in": cfg.get("managed_in", []),
                "tool_count": len(tool_names),
                "tools": tool_names,
            }
        )

    return _write_active_tool_catalog(base_dir, plugin_summaries)

def register_all_tools(mcp):
    logging.info("Scanning for plugins with YAML configs...")
    import plugins as plugins_package
    
    count = 0
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_summaries = []
    
    for plugin_folder in os.listdir(base_dir):
        p_dir = os.path.join(base_dir, plugin_folder)
        if not os.path.isdir(p_dir) or plugin_folder.startswith("__"):
            continue
            
        yaml_path = os.path.join(p_dir, "plugin.yaml")
        if not os.path.exists(yaml_path):
            continue
            
        # Parse YAML to check if enabled
        try:
            with open(yaml_path, 'r', encoding='utf-8') as yf:
                cfg = yaml.safe_load(yf)
                if not cfg.get("enabled", True):
                    logging.info(f"🚫 Plugin {plugin_folder} is DISABLED via YAML.")
                    continue
        except Exception as e:
            logging.error(f"Error parsing YAML for {plugin_folder}: {e}")
            continue
            
        try:
            module = importlib.import_module(f"plugins.{plugin_folder}")
            if hasattr(module, "register_tools"):
                before_tools = {tool.name for tool in mcp._tool_manager.list_tools()}
                module.register_tools(mcp)
                after_tools = {tool.name for tool in mcp._tool_manager.list_tools()}
                added_tools = sorted(after_tools - before_tools)
                _sync_plugin_metadata(yaml_path, cfg or {}, added_tools)
                plugin_summaries.append({
                    "folder": plugin_folder,
                    "name": (cfg or {}).get("name", plugin_folder),
                    "description": (cfg or {}).get("description", "No description provided"),
                    "owner": (cfg or {}).get("owner", ""),
                    "version": (cfg or {}).get("version", ""),
                    "managed_in": (cfg or {}).get("managed_in", []),
                    "tool_count": len(added_tools),
                    "tools": added_tools,
                })
                logging.info(f"✅ Registered tool plugin: {plugin_folder}")
                count += 1
        except Exception as e:
            logging.error(f"❌ Failed to load tool plugin {plugin_folder}: {e}")
            
    logging.info(f"🎉 Auto-Discovery completed. Loaded {count} active tool plugins.")
