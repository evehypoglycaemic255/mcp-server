# TOOL CATALOG FIRST POLICY

## Muc tieu
- Giam token waste khi AI agent can tim tool.
- Giam scan rong codebase chi de biet ten tool, plugin, va vung quan ly.
- Ep AI agent uu tien nguon catalog da duoc he thong auto-generate.

## Quy tac bat buoc
- Truoc khi tim tool trong codebase, AI agent phai uu tien doc `docs/architecture/active_tool_catalog.md`.
- Neu dang lam viec qua MCP server, AI agent phai uu tien goi `get_active_tool_catalog`.
- Chi duoc scan codebase de tim tool khi:
  - catalog khong ton tai,
  - catalog khong du thong tin cho task hien tai,
  - hoac co dau hieu catalog da stale so voi runtime.

## Quy tac scan khi bat buoc
- Neu phai scan, pham vi scan phai hep theo:
  - plugin dich,
  - file dich,
  - hoac tool dich.
- Khong quet rong toan bo `mcp_server/` hoac toan bo repo chi de tim danh sach tool.

## Thu tu uu tien discovery
1. `get_active_tool_catalog`
2. `docs/architecture/active_tool_catalog.md`
3. `docs/architecture/code_wiring.md`
4. `search_semantic_context` hoac `search_codebase`
5. scan hep theo plugin/file cu the

## Xu ly vi pham
- Neu agent scan rong codebase chi de tim tool trong khi catalog da du thong tin, hanh vi do duoc xem la vi pham zero-waste policy.
