import os
from core.dependencies import safe_tool

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def store_project_memory(project_name: str, logic_note: str, source: str = "ai_agent"):
        from core.vector_db import store_memory
        success = store_memory(project_name, logic_note, {"source": source})
        return {"status": "stored"} if success else {"error": "Failed to store in VectorDB"}

    @mcp.tool()
    @safe_tool
    def search_past_decisions(project_name: str, query: str, limit: int = 3):
        from core.vector_db import search_memory
        results = search_memory(project_name, query, limit)
        return {"found": len(results), "memories": results}

    @mcp.tool()
    @safe_tool
    def search_codebase(project_name: str, query: str, limit: int = 5):
        from core.vector_db import search_memory
        results = search_memory(project_name, query, limit, is_codebase=True)
        return {"found": len(results), "code_snippets": results}

    @mcp.tool()
    @safe_tool
    def review_code_architecture():
        import core.ast_analyzer as ast_analyzer
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        ast_analyzer.analyze_ast(project_root)
        return {"status": "success", "message": "Đã ghi báo cáo map vào docs/architecture/code_wiring.md"}
