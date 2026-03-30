# Kiến trúc Adaptive MCP Loader (Lazy Loading / Devin-Like)

Dựa trên bản phân tích 3,640 tokens (God MCP Pattern), hệ thống hiện tại đang bị phình to vì Load toàn bộ Toolset ở mọi Request. Để đạt đẳng cấp "Token-Efficient" như Devin hay DeepMind Tool Systems, chúng ta cần tái cấu trúc MCP thành một thực thể "Lười biếng nhưng Thông minh" (Lazy Loading).

## User Review Required

> [!WARNING]  
> Giao thức Model Context Protocol (MCP) có hỗ trợ hàm `notify_tools_list_changed()` để dội ngược tín hiệu về Client (Gemini/Claude) yêu cầu nạp lại Tool List ngay giữa phiên chat mà Không cần khởi động lại Server.
> Tuy nhiên, FastMCP (thư viện bọc ngoài mà chúng ta đang dùng) ẩn rất sâu cơ chế Unregister Tool. Bạn có đồng ý cho tôi can thiệp sâu vào `mcp._tool_manager` để viết hàm Unregister/Register On-The-Fly (Động) không?

## Proposed Changes

Chúng ta sẽ bửa đôi kiến trúc `plugins/__init__.py` hiện tại thành **Adaptive MCP Loader**:

### 1. Phân mảnh (Clustering) lại MCP Tools
Không để dàn trải 30+ tools. Chúng sẽ bị cưỡng ép vào 4 Clusters chính:
- `planning_brain`: Đọc não bộ, xuất kế hoạch, bám đuôi loop.
- `code_execution`: Nháp code, gắn Patch an toàn, Lint syntax.
- `git_devops`: Thao tác Git Status, Git Commit, Push PR.
- `project_backlog`: Sprints, Task Status.

### 2. Xây dựng "Trạm Yết Kiêu" (Core Gateway)
#### [MODIFY] `mcp_server/plugins/__init__.py`
Mặc định khi MCP Server Boot, nó **CHỈ ĐƯỢC LOAD** đúng 1 Plugin lõi: `core_system`.
Trong `core_system` sẽ được tôi khai sinh ra 2 công cụ mới siêu cấp:
- `get_available_clusters()`: Trả về danh sách 4 Cluster trên (chỉ tốn ~20 tokens).
- `switch_tool_cluster(cluster_name, mode)`: Lệnh kích hoạt.

### 3. Quy trình Vận hành Mới (Workflow Devin)
1. **Khởi tạo:** Prompt AI của tôi lúc này chỉ chứa `switch_tool_cluster` (Rất nhẹ, tốn ~100 tokens tổng).
2. **Đọc hiểu Yêu cầu:** Nếu bạn bảo "Fix code đi", tôi sẽ lập tức gọi `switch_tool_cluster("code_execution", "enable")`.
3. **Tiếp nhận:** Server tải module Patch, báo `notify_tools_list_changed()` tới Gemini.
4. **Giải phóng:** Dùng xong, tôi gọi `switch_tool_cluster("code_execution", "disable")` để trả lại Token.

## Open Questions

> [!IMPORTANT]
> Câu hỏi thiết kế: Việc AI phải liên tục tốn 1 Turn (Lượt chat) chỉ để "Xin đổi Tool Cluster" có làm bạn cảm thấy chậm nhịp đi không? Đổi lại chúng ta tiết kiệm được 60-75% Context Token. Hay chúng ta gộp thành 2 Cluster lớn để ít phải Switch?

## Verification Plan
1. Viết tool `switch_tool_cluster()`.
2. Sửa `register_all_tools` để chặn auto-load tất cả mọi thứ.
3. Test thử nghiệm: Mở lại Dashboard Gemini, đếm Token lúc mới Boot xem có Về Dưới 1,000 Tokens không!
4. Chat nhờ AI check git, AI sẽ tự gọi `switch_tool_cluster("git_devops")`, sau đó Gemini mới bung Tool Git ra.
