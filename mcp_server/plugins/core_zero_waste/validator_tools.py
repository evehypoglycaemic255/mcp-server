import ast
from core.dependencies import safe_tool

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def validate_syntax_lint(python_code: str) -> dict:
        """
        [VALIDATOR LAYER] Lọc NGAY KẺO TRỄ!
        Đánh giá Syntax AST Tree cục bộ trước khi AI Apply Patch làm nổ App thực.
        """
        try:
            ast.parse(python_code)
            return {"status": "pass", "message": "Khung Syntax hoạt động ổn (Valid AST)."}
        except SyntaxError as e:
            return {
                "status": "fail", 
                "error": f"Chết tại Syntax: {e.msg} ở Dòng {e.lineno}",
                "insight": "Dừng lại, đừng Apply Patch!"
            }
