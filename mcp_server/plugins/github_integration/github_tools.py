import subprocess
import os
from core.dependencies import safe_tool
from core.config import settings

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def git_local_status() -> dict:
        """Returns modified or uncommitted files."""
        result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, cwd=settings.PROJECT_ROOT)
        if result.returncode != 0:
            return {"error": result.stderr or "git status failed", "workspace_root": settings.PROJECT_ROOT}
        return {"stdout": result.stdout, "workspace_root": settings.PROJECT_ROOT}

    @mcp.tool()
    @safe_tool
    def git_local_checkout(branch_name: str, create_new: bool = True) -> dict:
        """Checkout branch locally."""
        cmd = ["git", "checkout"]
        if create_new: 
            # Enforce standard prefix for Admin tracking
            if not branch_name.startswith(settings.GITHUB_PREFIX):
                branch_name = f"{settings.GITHUB_PREFIX}{branch_name}"
            cmd.append("-b")
        cmd.append(branch_name)
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.PROJECT_ROOT)
        if result.returncode != 0:
            return {"error": result.stderr or "git checkout failed", "workspace_root": settings.PROJECT_ROOT}
        return {"stdout": result.stdout, "stderr": result.stderr, "workspace_root": settings.PROJECT_ROOT}

    @mcp.tool()
    @safe_tool
    def git_local_commit(message: str) -> dict:
        """Commit safely against master index."""
        # Auto-Add all modified files
        add_result = subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=settings.PROJECT_ROOT)
        if add_result.returncode != 0:
            return {"error": add_result.stderr or "git add failed", "workspace_root": settings.PROJECT_ROOT}
        result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, cwd=settings.PROJECT_ROOT)
        if result.returncode != 0:
            return {"error": result.stderr or "git commit failed", "workspace_root": settings.PROJECT_ROOT}
        return {"stdout": result.stdout, "stderr": result.stderr, "workspace_root": settings.PROJECT_ROOT}

    @mcp.tool()
    @safe_tool
    def github_remote_create_pr(title: str, body: str, head_branch: str, base_branch: str = "main") -> dict:
        """Create Github PR from head to base branch."""
        if not settings.GITHUB_REMOTE_ENABLED:
            return {
                "status": "BLOCKED", 
                "error": "The firewall (Feature Toggle) has blocked your Github Public API access.",
                "hint": "Admin must enable `remote_api_enabled: true` in `config/mcp_config.json`."
            }
            
        if not settings.GITHUB_TOKEN:
            return {"status": "BLOCKED", "error": "Missing GITHUB_TOKEN secret in `.env`."}

        # Skeleton Code (Phase 2 Implement PyGithub Logic)
        return {
            "status": "SUCCESS_MOCK", 
            "message": f"Simulated Pull Request! If enabled, PyGithub would push [{head_branch} -> {base_branch}]!"
        }
