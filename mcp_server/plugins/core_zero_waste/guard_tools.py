from core.dependencies import safe_tool
import hashlib

# Ephemeral RAM Dictionary cho Attempt Hashing
ATTEMPT_MEMORY_STORE = {}

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def check_attempt_trap(task_id: str, proposed_logic: str) -> dict:
        """Checks AI iteration attempts to prevent infinite circular reasoning."""
        attempt_hash = hashlib.md5((task_id + proposed_logic).encode()).hexdigest()
        
        attempt_count = ATTEMPT_MEMORY_STORE.get(attempt_hash, 0)
        attempt_count += 1
        ATTEMPT_MEMORY_STORE[attempt_hash] = attempt_count
        
        if attempt_count == 1:
            return {
                "status": "WARN", 
                "hint": "Ghi nhận giải pháp số 1. Nếu run_sandbox fail, đừng sửa râu ria, phải đổi Strategy."
            }
        elif attempt_count == 2:
            return {
                "status": "SOFT_BLOCK", 
                "reason": "Cảnh bão: Mẫu thất bại cũ đang lặp lại (Same failure pattern)!",
                "suggestion": "HINT: Đừng cố fix Syntax. Hãy check lại Context_Guard ở Tầng Lớp (Class Level) xem có lỡ Override sai hàm không!"
            }
        else:
            return {
                "status": "HARD_BLOCK", 
                "reason": "Quyền Tự quyết của AI bị Tước Bỏ. Bạn đã mắc kẹt Loop 3 lần. Xin hãy Dừng code, trả lời User để tìm phương thức mới."
            }
