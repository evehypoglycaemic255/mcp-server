import os
import importlib
import logging

def register_tools(mcp):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(current_dir):
        if file.endswith(".py") and not file.startswith("__"):
            mod_name = file[:-3]
            try:
                mod = importlib.import_module(f"{__package__}.{mod_name}")
                if hasattr(mod, "register_tools"):
                    mod.register_tools(mcp)
            except Exception as e:
                logging.error(f"Failed to load {mod_name} inside {__package__}: {e}")
