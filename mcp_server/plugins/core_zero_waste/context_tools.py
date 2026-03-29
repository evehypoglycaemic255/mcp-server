import os
import json
from core.dependencies import safe_tool

def register_tools(mcp):
    
    @mcp.tool()
    @safe_tool
    def search_semantic_context(query: str, expand_level: int = 2, limit: int = 5) -> dict:
        """
        [CONTEXT GUARD] Dò tìm Codebase bằng Vector Semantic.
        - expand_level = 1: Trả về chính xác Function Chunk (Chỉ logic gốc).
        - expand_level = 2: Trả về Function + Summary của Class/Module chứa nó.
        - expand_level = 3: Trả về Function + Class + Cây Dependence (Những hàm nào gọi nó).
        """
        from core.vector_db import search_memory
        
        # Skeleton: Truy xuất hàm cơ bản từ Vector (Level 1)
        base_results = search_memory(query, query, n_results=limit, is_codebase=True)
        
        enhanced_context = []
        for res in base_results:
            node = {"function_logic": res["logic"], "metadata": res["metadata"]}
            file_ref = res["metadata"].get("file")
            parent_class = res["metadata"].get("parent_class")
            
            # Nếu AI cầu cứu thiếu Context, đào thêm Database bằng SQL Metadata (Level 2 & 3)
            try:
                from core.config import settings
                import psycopg2
                import json
                
                conn = psycopg2.connect(settings.DATABASE_URL)
                with conn.cursor() as cur:
                    if expand_level >= 2 and parent_class:
                        # Móc nội dung Class Summary
                        cur.execute("SELECT content FROM ai_memory_vectors WHERE metadata::jsonb ->> 'type' = %s AND metadata::jsonb ->> 'name' = %s AND metadata::jsonb ->> 'file' = %s LIMIT 1", ('class_summary', parent_class, file_ref))
                        class_res = cur.fetchone()
                        if class_res:
                            node["class_summary"] = class_res[0]
                            
                    if expand_level >= 3:
                        # Móc chi tiết Dependencies (Edges)
                        deps = res["metadata"].get("dependencies")
                        if deps:
                            node["dependencies_called"] = json.loads(deps)
                conn.close()
            except Exception as e:
                pass
                
            enhanced_context.append(node)
            
        return {
            "query": query,
            "expand_level": expand_level,
            "results": enhanced_context,
            "token_saving_tip": "Chỉ tăng expand_level khi thực sự thiếu context."
        }

    @mcp.tool()
    @safe_tool
    def review_architecture_map() -> dict:
        """Trả về toàn cảnh Graph Liên kết (Metaconcept) từ AST Analyzer"""
        import core.ast_analyzer as ast_analyzer
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        ast_analyzer.analyze_ast(project_root)
        return {"status": "success", "file": "docs/architecture/code_wiring.md"}
