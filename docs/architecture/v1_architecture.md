# Kiến trúc hệ thống: MCP Commander

Tài liệu này mô tả kiến trúc tổng quan của MCP Commander ở trạng thái hiện hành.
Nó thay thế mô tả cũ còn drift với implementation trước remediation.

## Mục tiêu kiến trúc

- Cung cấp MCP server cho AI agent làm việc với project tracking, sprint, backlog và session logs.
- Duy trì persistent memory qua PostgreSQL và vector backend.
- Cho phép dashboard quan sát và quản trị project theo cách trực quan.
- Tách năng lực hệ thống theo plugin để dễ kiểm soát phạm vi tool.

## Thành phần chính

### 1. MCP Server
- Nền tảng: FastAPI + FastMCP.
- Chạy ở 2 mode:
  - local MCP runtime
  - SSE server qua `/mcp/sse`
- Có endpoint kiểm tra sức khỏe tại `/health`.

### 2. PostgreSQL
- Lưu project tracking và operational logs.
- Các bảng chính:
  - `projects`
  - `sprints`
  - `backlog_items`
  - `ai_sessions`
  - `system_tool_logs`
- Có schema bootstrap tại runtime qua `ensure_schema()`.

### 3. Streamlit Dashboard
- Dùng để xem và quản trị:
  - project
  - sprint
  - backlog
  - AI logs
  - system tool logs
  - plugin metadata
  - antigravity brain logs
- Tab `Sprint & Backlog Window` phục vụ theo dõi công việc đang triển khai.

### 4. Plugin Ecosystem

#### `core_system`
- Project management tools
- Sprint/backlog creation and update tools
- Codebase memory and architecture review tools

#### `core_zero_waste`
- Semantic context search
- Execution planning
- Session logging
- Patch workflow với guard và validation
- Ephemeral sandbox execution

#### `github_integration`
- Git local status
- Checkout branch
- Commit changes
- Mock PR creation

#### `antigravity_sync`
- Đọc dữ liệu brain logs từ mounted external volume

## Luồng triển khai

1. Dashboard hoặc MCP client gửi yêu cầu.
2. MCP server route yêu cầu tới plugin tương ứng.
3. Tool đi qua `safe_tool` để log và chuẩn hóa trạng thái lỗi.
4. Dữ liệu được ghi xuống PostgreSQL hoặc vector backend.
5. Dashboard đọc lại trạng thái để hiển thị tiến độ theo project.

## Luồng deployment

### Docker Compose
- `db`: PostgreSQL + pgvector, có healthcheck.
- `mcp-server`: mount source code và workspace root, có healthcheck `/health`.
- `dashboard`: streamlit app, có healthcheck `_stcore/health`.

## Giới hạn hiện tại

- Vector/embedding subsystem vẫn phụ thuộc dependency nặng và môi trường build phù hợp.
- Auth và access control chưa hoàn thiện.
- Một số hardening production vẫn nằm trong backlog remediation giai đoạn sau.
