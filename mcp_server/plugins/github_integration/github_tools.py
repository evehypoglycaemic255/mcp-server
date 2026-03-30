import subprocess
import os
from core.dependencies import safe_tool
from core.config import settings

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def git_local_status() -> dict:
        """
        [PHASE 1 - GIT LOCAL] Return a list of files currently tracked as modified or uncommitted.
        Helps the AI define its actual workspace diff before patching.
        """
        result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, cwd=settings.PROJECT_ROOT)
        if result.returncode != 0:
            return {"error": result.stderr or "git status failed", "workspace_root": settings.PROJECT_ROOT}
        return {"stdout": result.stdout, "workspace_root": settings.PROJECT_ROOT}

    @mcp.tool()
    @safe_tool
    def git_local_checkout(branch_name: str, create_new: bool = True) -> dict:
        """
        [PHASE 1 - GIT LOCAL] Allows AI to switch away from main branch and open a Sandbox Branch (e.g. ai-feature/fix-bug).
        Completely isolates the risk of breaking Core Architecture.
        """
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
        """
        [PHASE 1 - GIT LOCAL] "Save Game Point" (Checkpoint) for safety.
        Any Local Patch that passes Validator should be committed locally to allow rewinds.
        """
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
        """
        [PHASE 2 - GITHUB REMOTE] Generate a Pull Request (Awaiting Reviewers) to push to cloud server.
        Blocked by Toggle Config unless Admin trusts and enables Remote capability.
        """
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
