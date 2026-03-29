import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")

def create_plugin(name, desc, files_to_move):
    p_dir = os.path.join(PLUGINS_DIR, name)
    os.makedirs(p_dir, exist_ok=True)
    
    # Tạo YAML
    yaml_path = os.path.join(p_dir, "plugin.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(f"name: {name}\n")
        f.write(f"description: {desc}\n")
        f.write("version: 1.0.0\n")
        f.write("enabled: true\n")
        
    # Tạo README
    md_path = os.path.join(p_dir, "README.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Plugin: {name}\n\n{desc}\n")
        
    # Tạo __init__ proxy
    init_path = os.path.join(p_dir, "__init__.py")
    module_names = []
    
    # Move Python Files
    for filename in files_to_move:
        src = os.path.join(TOOLS_DIR, filename)
        dst = os.path.join(p_dir, filename)
        if os.path.exists(src):
            shutil.move(src, dst)
            module_names.append(filename.replace('.py', ''))
            
    # Ghi nội dung Register Proxy
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write("def register_tools(mcp):\n")
        for mod in module_names:
            f.write(f"    from . import {mod}\n")
            f.write(f"    if hasattr({mod}, 'register_tools'):\n")
            f.write(f"        {mod}.register_tools(mcp)\n")

def main():
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR)
        
    # 1. Zero Waste
    create_plugin(
        "core_zero_waste", 
        "Hệ thống lõi Zero-Waste chống rò rỉ Context và ngăn lặp vòng lặp ảo của Agent.",
        ["sandbox_tools.py", "context_tools.py", "guard_tools.py", "patch_tools.py", "planning_tools.py"]
    )
    
    # 2. Github
    create_plugin(
        "github_integration",
        "Luồng làm việc với Git Local, tạo nhánh test, sinh Pull Request Remote.",
        ["github_tools.py"]
    )
    
    # 3. Codebase
    create_plugin(
        "core_system",
        "Bộ quét mã nguồn, chạy Review kiến trúc, và đọc tệp cơ bản.",
        ["codebase_tools.py", "system_tools.py", "api_tools.py"] # Just in case
    )
    
    # 4. Master Plugin Loader
    loader_path = os.path.join(PLUGINS_DIR, "__init__.py")
    with open(loader_path, 'w', encoding='utf-8') as f:
        f.write('''import importlib
import pkgutil
import logging
import os
import yaml

def register_all_tools(mcp):
    logging.info("Scanning for plugins with YAML configs...")
    import plugins as plugins_package
    
    count = 0
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
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
                module.register_tools(mcp)
                logging.info(f"✅ Registered tool plugin: {plugin_folder}")
                count += 1
        except Exception as e:
            logging.error(f"❌ Failed to load tool plugin {plugin_folder}: {e}")
            
    logging.info(f"🎉 Auto-Discovery completed. Loaded {count} active tool plugins.")
''')

    # Xóa folder tools cũ cực kỳ an toàn
    for f in os.listdir(TOOLS_DIR):
        fpath = os.path.join(TOOLS_DIR, f)
        if os.path.isfile(fpath): os.remove(fpath)
    os.rmdir(TOOLS_DIR)
    print("Migration Hoàn Tất: Đã tái cấu trúc 100% Tools thành Plugins.")

if __name__ == "__main__":
    main()
