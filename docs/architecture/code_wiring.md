# Code Wiring

Tài liệu này mô tả wiring ở mức hiện hành của MCP Commander sau đợt remediation ngày 2026-03-30.
Nó thay thế bản auto-generated cũ đã stale và lệch với kiến trúc plugin hiện tại.

## Dashboard

### `dashboard/app.py`
- Entrypoint tối giản cho Streamlit.
- Gọi `render_app()` từ `dashboard_v2.py`.

### `dashboard/dashboard_v2.py`
- Dashboard chính cho:
  - Projects
  - Sprint & Backlog Window
  - Overview Dashboard
  - AI Log Signals
  - System Tool Logs
  - Plugins Ecosystem
  - Antigravity Brain Logs
- Đọc trực tiếp PostgreSQL qua query có tham số.
- Đọc metadata plugin từ `mcp_server/plugins/*/plugin.yaml`.

## MCP Server Core

### `mcp_server/main.py`
- Khởi tạo `FastMCP` và auto-register toàn bộ plugin đang `enabled`.
- Expose các endpoint:
  - `/`
  - `/health`
  - `/mcp/sse`
- Khởi động workspace watcher khi chạy ở chế độ server.

### `mcp_server/core/config.py`
- Nạp `.env` và `config/mcp_config.json`.
- Chuẩn hóa các runtime defaults:
  - `DEFAULT_PROJECT_NAME`
  - `DEFAULT_SPRINT_NAME`
  - `WORKSPACE_ROOT`
  - `WATCHDOG_ROOTS`

### `mcp_server/core/database.py`
- Mở kết nối PostgreSQL.
- Gọi `ensure_schema()` để tự đồng bộ schema tối thiểu khi runtime khởi động.

### `mcp_server/core/schema.py`
- Định nghĩa và bootstrap các bảng:
  - `projects`
  - `sprints`
  - `backlog_items`
  - `ai_sessions`
  - `system_tool_logs`
- Tự đảm bảo có default project và active sprint mặc định.

### `mcp_server/core/dependencies.py`
- Middleware `safe_tool`.
- Ghi `system_tool_logs` cho mọi tool đi qua decorator.
- Redact payload nhạy cảm và đánh dấu `ERROR` đúng khi tool trả về payload lỗi.

### `mcp_server/core/watcher.py`
- Theo dõi thay đổi file trong các root được cấu hình.
- Vectorize code chunks vào memory backend.
- Ghi log thay đổi file vào `ai_sessions` nếu có sprint active.

### `mcp_server/init_mcp.py`
- Bootstrap default project/sprint bằng runtime config thay vì hardcode DB URL.

## Plugin Matrix

### `mcp_server/plugins/core_system`
- `project_tools.py`
  - `upsert_project`
  - `create_sprint`
  - `update_sprint`
  - `create_backlog_item`
  - `update_backlog_item`
  - `list_project_assets`
- `codebase_tools.py`
  - `store_project_memory`
  - `search_past_decisions`
  - `search_codebase`
  - `review_code_architecture`

### `mcp_server/plugins/core_zero_waste`
- `context_tools.py`
  - semantic context search theo `project_name`
- `planning_tools.py`
  - execution planning gắn với sprint active
- `memory_tools.py`
  - session logging
  - project context lookup
- `patch_tools.py`
  - bounded patch workflow với syntax validation và `dry_run`
- `guard_tools.py`
  - attempt trap / anti-loop guard
- `sandbox_tools.py`
  - ephemeral Python execution
- `validator_tools.py`
  - syntax validation

### `mcp_server/plugins/github_integration`
- Git local status / checkout / commit
- Mock GitHub PR tool
- Phụ thuộc workspace Git hợp lệ và binary `git`

### `mcp_server/plugins/antigravity_sync`
- Đọc historical brain sessions từ mounted volume bên ngoài
- Hiển thị tại dashboard tab Antigravity Brain Logs

## Deployment Wiring

### `docker-compose.yml`
- `db`: PostgreSQL + pgvector, có healthcheck `pg_isready`
- `mcp-server`: chạy `python main.py --sse`, có `/health`, mount workspace root
- `dashboard`: Streamlit UI, có healthcheck `_stcore/health`

## Ghi chú

- Tài liệu này là bản curated để phản ánh implementation hiện hành.
- Nếu cần auto-generate lại từ AST, nên phát sinh sang file khác để tránh overwrite mô tả vận hành thực tế.
- Last synchronized via MCP patch tool on 2026-03-30.
