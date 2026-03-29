import ast
import os
import json

class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)

def extract_semantic_chunks(code: str, filename: str) -> list:
    """
    [PHASE 1 - AST CHUNKING]
    Xẻ thịt mã nguồn thành 3 level: Function (Level 1), Class Summary (Level 2), Edge (Level 3).
    """
    chunks = []
    try:
        tree = ast.parse(code, filename=filename)
    except Exception as e:
        print(f"Lỗi AST Parser tại {filename}: {e}")
        return chunks

    # Level 2: Class/Module Summary
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    for c in classes:
        methods = [m.name for m in c.body if isinstance(m, ast.FunctionDef)]
        summary_content = f"class {c.name}:\n  methods: {', '.join(methods)}"
        chunks.append({
            "content": summary_content,
            "metadata": {
                "type": "class_summary",
                "name": c.name,
                "file": filename
            }
        })

    # Level 1 & 3: Function Logic + Dependency Callers
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Hàm cha (Nếu nằm trong Class)
            parent_class = None
            for c in classes:
                if node in c.body:
                    parent_class = c.name
                    break
            
            # Lấy nguyên văn Code Hàm (Python 3.8+)
            func_code = ast.get_source_segment(code, node)
            if not func_code: continue

            # Lấy Level 3: Dependency Móc nối
            dep_visitor = DependencyVisitor()
            dep_visitor.visit(node)
            edges = list(set(dep_visitor.calls))

            chunks.append({
                "content": func_code,
                "metadata": {
                    "type": "function",
                    "name": node.name,
                    "parent_class": parent_class,
                    "dependencies": json.dumps(edges),
                    "file": filename
                }
            })
            
    # Nếu file không có hàm nào, tạo 1 Module Chunk dự phòng
    if not chunks:
        chunks.append({
            "content": code[:1000],
            "metadata": {"type": "module_fallback", "file": filename}
        })

    return chunks

# Tích hợp Code Wiring (Bản cũ)
def analyze_ast(project_dir):
    wiring = []
    wiring.append("# Sơ đồ Kiến trúc Code (Code Wiring)\n")
    wiring.append("> Sơ đồ này được cập nhật tự động bằng `ast_analyzer.py`. Nó bóc tách cấu trúc hàm/class trực tiếp từ mã nguồn mà không cần Regex.\n")
    
    for root, dirs, files in os.walk(project_dir):
        if any(ignore in root for ignore in ['venv', '__pycache__', '.git', 'chroma']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_dir)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=rel_path)
                    
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
                    from_imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
                    
                    wiring.append(f"## File: `{rel_path}`")
                    if classes: wiring.append(f"- **Classes**: {', '.join(classes)}")
                    if functions: wiring.append(f"- **Functions**: {', '.join(functions)}")
                    all_imports = imports + from_imports
                    if all_imports: wiring.append(f"- **Dependencies**: {', '.join(set(all_imports))}")
                    wiring.append("")
                except Exception as e:
                    wiring.append(f"## File: `{rel_path}`\n- *Parse Error: {e}*\n")
                    
    target_dir = os.path.join(project_dir, 'docs', 'architecture')
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, 'code_wiring.md')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(wiring))

if __name__ == "__main__":
    analyze_ast(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
