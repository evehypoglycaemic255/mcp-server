import os
import glob
from core.dependencies import safe_tool
import logging

def get_latest_folders(base_dir, limit):
    folders = []
    if not os.path.exists(base_dir): return []
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path) and len(entry) > 10:  # Typically a UUID like 0df8cb4a-93cd-42d4
            mtime = os.path.getmtime(full_path)
            folders.append((full_path, mtime))
    folders.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in folders[:limit]]

def register_tools(mcp):
    
    @mcp.tool()
    @safe_tool
    def read_historical_brain(limit: int = 3, include_plans: bool = True) -> list:
        """Fetch past AI session walkthroughs/plans."""
        BRAIN_DIR = "/antigravity_brain"
        if not os.path.exists(BRAIN_DIR):
            return [{"error": f"Volume {BRAIN_DIR} không tồn tại. Yêu cầu bật Volume qua docker-compose!"}]
            
        target_folders = get_latest_folders(BRAIN_DIR, limit)
        results = []
        
        for folder in target_folders:
            session_id = os.path.basename(folder)
            session_data = {"session_id": session_id, "walkthrough": None, "plan": None}
            
            w_path = os.path.join(folder, "walkthrough.md")
            if os.path.exists(w_path):
                with open(w_path, "r", encoding="utf-8") as f:
                    session_data["walkthrough"] = f.read()

            if include_plans:
                p_path = os.path.join(folder, "implementation_plan.md")
                if os.path.exists(p_path):
                    with open(p_path, "r", encoding="utf-8") as f:
                        session_data["plan"] = f.read()
            
            # Chỉ trả về nếu Session này không trống rỗng
            if session_data["walkthrough"] or session_data["plan"]:
                results.append(session_data)
                
        return results
