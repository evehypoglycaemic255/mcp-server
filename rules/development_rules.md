# KỶ LUẬT PHÁT TRIỂN & ZERO-WASTE PIPELINE (PROMPT CHO AI)

## 1. Nguyên lý Nền tảng (Core Principles)
- **Zero-Waste Token (Tiết kiệm Tối đa):** CẤM load toàn bộ file vào ngữ cảnh nếu không thực sự cần. Hãy sử dụng Radar `search_semantic_context`.
- **Reasoning over Trial-Error (Suy luận thay vì Thử-Sai mù quáng):** Mọi tác vụ sửa/thêm code BẮT BUỘC chạy qua: Lập kế hoạch (Plan) -> Mở rộng Bố cục (Context) -> Thử nghiệm (Sandbox) -> Chèn mã cục bộ (Patch).
- **Không tự bịa đặt bối cảnh:** Hệ thống ĐÃ CÓ SẴN file sơ đồ kiến trúc tại `docs/architecture/code_wiring.md` (được sinh tự động từ AST). Bạn BẮT BUỘC phải đọc file này để lấy Metaconcept toàn cục thay vì đoán mò. Cấm gọi `review_architecture_map` để quét lại từ đầu nếu file kia vẫn đang hữu dụng (tốn Token).

## 2. Quy trình Mệnh lệnh "Zero-Waste" BẮT BUỘC (Agent Execution Pipeline)
Bất kỳ khi nào thực hiện gỡ Lỗi (Bugfix) hoặc Thêm tính năng (Feature), AI Agent (như bạn) PHẢI tuân thủ nghiêm ngặt 5 cột mốc:

* **Bước 1 - Lập Kế hoạch Xác Tín (Intent & Plan):** 
  - Gọi ngay tool `create_execution_plan` khai báo Mật danh Task, Tệp đích và Chiến lược để lấy thẻ `plan_id`.
* **Bước 2 - Lấy Context Cục Bộ Rẽ Nhánh:** 
  - Gọi `search_semantic_context(query, expand_level=1)` để lấy chính xác Logic Function bị lỗi. 
  - CHỈ KHI KHÔNG ĐỦ THÔNG TIN, mới được đẩy `expand_level=2` (lấy Class) hoặc `3` (lấy Cây Dependencies). Nghiêm cấm xả rác hàng ngàn dòng code vào Context Screen.
* **Bước 3 - Môi trường Giả lập & Thẩm định (Sandbox):**
  - Trái tim của Zero-Waste! Viết Test Case cho logic, nạp vào `run_code_ephemeral`. Code của bạn phải Output ra kết quả `success` trên RAM trước khi chạm vào File hệ thống.
  - Phải vượt qua Cổng kiểm định Cú pháp thông qua `validate_syntax_lint`.
* **Bước 4 - Can thiệp Giải Phẫu (Safe Patching):**
  - NGIÊM CẤM TẠO LẠI TOÀN BỘ FILE (Overwrite entire file). Bắt buộc phải xác định dòng `old_snippet` để thay thế chuẩn xác qua công cụ `apply_safe_patch`.
* **Bước 5 - Trạm Gác Vòng Lặp (Attempt Loop Lock):**
  - Chạy `check_attempt_trap(hash)`. Nếu bạn nhận Cảnh báo `WARN` hoặc chặn `SOFT_BLOCK`, NGAY LẬP TỨC NGỪNG SỬA CÚ PHÁP LẶP LẠI (Syntax Trial). Hãy thay đổi toàn bộ Chiến thuật, quay lại Bước 2 hoặc báo cáo Admin xin Support.

## 3. Quy chuẩn Code (Code Standards)
- Khi thêm, sửa code phải có comment mã sprint và nhiệm vụ của đoạn code. Python phải có Type Hinting rõ ràng.
- Bước cuối cùng của mọi chặng luôn là tự hỏi "Tôi có nên lưu lại Task Session này vào Database không" và chủ động gọi `log_session_v2`.
## 0. Tool Catalog First
- Truoc khi tim tool trong codebase, bat buoc doc `rules/tool_catalog_rules.md`.
- Uu tien `docs/architecture/active_tool_catalog.md` hoac `get_active_tool_catalog`.
