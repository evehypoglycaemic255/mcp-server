import os
from core.dependencies import safe_tool

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def apply_safe_patch(filepath: str, old_snippet: str, new_snippet: str) -> dict:
        """
        [PATCH ENGINE] Kỹ năng phẫu thuật tĩnh.
        Bắt AI chỉ được sử dụng công cụ "đổi vị trí chính xác" (Patching) thay vì Load rác Rewrite cả file.
        Chặn Fake Pass bằng kiểm duyệt SyntaxError trước đó.
        """
        if not os.path.exists(filepath):
            return {"status": "fail", "error": f"Phẫu thuật trượt: File {filepath} không tồn tại!"}
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_snippet not in content:
            return {
                "status": "fail", 
                "error": "Phẫu thuật trượt: Đoạn old_snippet bạn gửi không tồn tại y hệt dưới source thật. Hãy dùng Context Search lấy lại Snippet gôc!"
            }
            
        new_content = content.replace(old_snippet, new_snippet)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return {"status": "success", "message": f"Patch an toàn đã ghép lặn vào {filepath}. Zero-waste Token!"}
