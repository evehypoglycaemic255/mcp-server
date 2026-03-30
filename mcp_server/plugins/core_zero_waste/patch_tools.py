import ast
import os

from core.config import settings
from core.dependencies import safe_tool


def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def apply_safe_patch(filepath: str, old_snippet: str, new_snippet: str, dry_run: bool = False) -> dict:
        """
        Apply a bounded patch inside the configured workspace.
        The tool refuses multi-match replacements and validates Python syntax before writing.
        """
        normalized_path = os.path.abspath(filepath)
        workspace_root = os.path.abspath(settings.PROJECT_ROOT)

        if not normalized_path.startswith(workspace_root):
            return {"status": "fail", "error": f"Refusing to patch outside workspace root: {workspace_root}"}
        if not os.path.exists(normalized_path):
            return {"status": "fail", "error": f"Patch aborted: file {normalized_path} does not exist."}

        with open(normalized_path, "r", encoding="utf-8") as f:
            content = f.read()

        occurrences = content.count(old_snippet)
        if occurrences == 0:
            return {"status": "fail", "error": "Patch aborted: old_snippet was not found exactly in the file."}
        if occurrences > 1:
            return {
                "status": "fail",
                "error": f"Patch aborted: old_snippet matched {occurrences} regions. Provide a unique snippet.",
            }

        new_content = content.replace(old_snippet, new_snippet, 1)
        if normalized_path.endswith(".py"):
            try:
                ast.parse(new_content)
            except SyntaxError as exc:
                return {"status": "fail", "error": f"Patch would introduce SyntaxError: {exc}"}

        result = {
            "filepath": normalized_path,
            "replacements": 1,
            "old_snippet_preview": old_snippet[:160],
            "new_snippet_preview": new_snippet[:160],
        }
        if dry_run:
            result["status"] = "preview"
            return result

        with open(normalized_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        result["status"] = "success"
        result["message"] = f"Patch applied safely to {normalized_path}"
        return result
