import importlib
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
