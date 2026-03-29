from core.dependencies import safe_tool
import uuid

def register_tools(mcp):

    @mcp.tool()
    @safe_tool
    def create_execution_plan(task_intent: str, target_files: list, strategy_type: str) -> dict:
        """
        [PLANNER LAYER] AI BẮT BUỘC phải gọi tool này trước khi Edit Code.
        Góp phần định hình Metaconcept, chống gọi tool mù (Trial-Error).
        - strategy_type: 'refactor', 'bugfix', 'feature_addition'.
        """
        plan_id = str(uuid.uuid4())[:8]
        
        # Ghi Log Kế hoạch vào Database để Giám sát và Tracking Hành Vi
        try:
            from core.config import settings
            import psycopg2
            conn = psycopg2.connect(settings.DATABASE_URL)
            with conn.cursor() as cur:
                # Mặc định cắm vào project_id 1 cho Demo
                cur.execute(
                    "INSERT INTO ai_session_logs (project_id, session_task, logic_process, pending_issues) VALUES (1, %s, %s, %s)",
                    (f"Plan [{plan_id}]: {task_intent}", f"Targets: {target_files} | Strategy: {strategy_type}", "Đang chờ Sandbox Exec")
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print("DB Log Plan Error:", e)

        return {
            "status": "APPROVED",
            "plan_id": plan_id,
            "directive": f"Cam kết chiến lược {strategy_type} đã được khóa. Ràng buộc: {target_files}. Vui lòng test Sandbox.",
            "enforced_targets": target_files
        }
