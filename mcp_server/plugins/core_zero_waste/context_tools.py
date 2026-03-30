import os
import json
from core.dependencies import safe_tool


def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def search_semantic_context(project_name: str, query: str, expand_level: int = 2, limit: int = 5) -> dict:
        """Search semantic code context for a project. Set expand_level for depth (1=Func, 2=Class, 3=Deps)."""
        from core.vector_db import search_memory
        from core.config import settings
        import psycopg2

        base_results = search_memory(project_name, query, n_results=limit, is_codebase=True)

        enhanced_context = []
        for res in base_results:
            node = {"function_logic": res["logic"], "metadata": res["metadata"]}
            file_ref = res["metadata"].get("file")
            parent_class = res["metadata"].get("parent_class")

            try:
                conn = psycopg2.connect(settings.DATABASE_URL)
                with conn.cursor() as cur:
                    if expand_level >= 2 and parent_class:
                        cur.execute(
                            "SELECT content FROM ai_memory_vectors WHERE collection_name = %s AND metadata::jsonb ->> 'type' = %s AND metadata::jsonb ->> 'name' = %s AND metadata::jsonb ->> 'file' = %s LIMIT 1",
                            (f"{project_name}-code", 'class_summary', parent_class, file_ref),
                        )
                        class_res = cur.fetchone()
                        if class_res:
                            node["class_summary"] = class_res[0]

                    if expand_level >= 3:
                        deps = res["metadata"].get("dependencies")
                        if deps:
                            node["dependencies_called"] = json.loads(deps)
                conn.close()
            except Exception:
                pass

            enhanced_context.append(node)

        return {
            "project_name": project_name,
            "query": query,
            "expand_level": expand_level,
            "results": enhanced_context,
            "token_saving_tip": "Only increase expand_level when extra context is needed.",
        }

    @mcp.tool()
    @safe_tool
    def review_architecture_map() -> dict:
        import core.ast_analyzer as ast_analyzer
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        ast_analyzer.analyze_ast(project_root)
        return {"status": "success", "file": "docs/architecture/code_wiring.md"}
