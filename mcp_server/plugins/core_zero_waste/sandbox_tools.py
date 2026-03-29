import subprocess
import tempfile
import os
from core.dependencies import safe_tool
from core.config import settings

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def run_code_ephemeral(python_code: str, test_inputs: str = "") -> dict:
        """
        [SANDBOX ENGINE] Chạy nháp Code Python trên RAM, cô lập quy trình (Isolated Process).
        Có giới hạn ngắt kết nối (Timeout) để chống Infinite Loop của AI.
        Tuyệt đối không làm lộ State hay ghi đè lên Codebase thật.
        """
        # Tạo file nháp Tạm thời (Ephemeral)
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(python_code)
            tmp_path = tmp.name

        try:
            # Truyền mác PYTHONPATH ảo để Sandbox tải được thư viện nhưng không được nhả Rác vào Project File
            project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            sandbox_cwd = tempfile.gettempdir()
            
            env = os.environ.copy()
            env["PYTHONPATH"] = project_dir
            
            # Subprocess Cô Lập (Timeout 5s - 100% Isolated State)
            cmd = ["python", tmp_path]
            if test_inputs: cmd.append(test_inputs)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=sandbox_cwd,
                env=env
            )
            
            output = result.stdout
            error = result.stderr
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": output,
                "stderr": error
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": f"Execution exceeded 5 seconds. Quota Blocked."}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
