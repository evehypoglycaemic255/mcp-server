import os
import re

plugins_dir = r"D:\WORK\1.MCP_SERVER\mcp_server\plugins"

def minify_docstrings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tìm kiếm các function có decorator @mcp.tool() và xóa docstrings dài của nó
    # Docstring regex: \s*\"\"\"[\s\S]*?\"\"\" (Nhưng chỉ khi nằm ngay dưới def)
    
    # Python text substitution that replaces the string literal right after the def statement.
    # It's safer to use AST or a specialized regex.
    # We will use regex to find: `def (\w+)\(.*?\)(?: -> .*?)?:\n\s*\"\"\"([\s\S]*?)\"\"\"`
    
    def replacer(match):
        func_name = match.group(1)
        original_doc = match.group(2)
        # Bỏ qua nếu docstring đã quá ngắn
        if len(original_doc.strip()) < 30:
            return match.group(0)
            
        short_doc = f"Executes {func_name}."
        if 'search' in func_name: short_doc = "Search capability."
        if 'git' in func_name: short_doc = "Git command."
        if 'backlog' in func_name: short_doc = "Manage backlog."
        if 'sprint' in func_name: short_doc = "Manage agile sprints."
        if 'patch' in func_name: short_doc = "Apply codebase patches."
        if 'brain' in func_name: short_doc = "Access AI memory."
        
        # We replace the exact docstring match
        new_str = match.group(0).replace('"""' + original_doc + '"""', f'"""{short_doc}"""')
        return new_str

    pattern = r'(def\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?:\s*\n\s*)\"\"\"([\s\S]*?)\"\"\"'
    new_content = re.sub(pattern, replacer, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Minified Docstrings in: {os.path.basename(file_path)}")

for root, _, files in os.walk(plugins_dir):
    for file in files:
        if file.endswith('.py'):
            minify_docstrings(os.path.join(root, file))
