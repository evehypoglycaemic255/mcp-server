# Active Tool Catalog

Ngay cap nhat: 2026-03-30 16:41:44
Nguon chuan: auto-generated tu tool registry thuc te + plugin metadata

## Muc dich

Tai lieu nay la danh ba tra cuu nhanh cho AI agent va coder.
He thong tu dong sinh lai file nay khi MCP server boot va hoan tat plugin auto-registration.

## Tong quan

- `4` plugin active
- `30` tool active

## Quick Map

| Plugin | Muc dich | Managed In | So tool |
|---|---|---|---:|
| `antigravity_sync` | Kết nối lịch sử session Antigravity để đọc plan và walkthrough từ bộ nhớ ngoài. | `Antigravity Brain Logs`, `Plugins Ecosystem` | 1 |
| `core_system` | Bộ công cụ hệ thống cho quản lý project, sprint, backlog, memory query, và review kiến trúc code. | `Projects tab`, `Sprint & Backlog Window`, `MCP Server tools` | 16 |
| `core_zero_waste` | Hệ thống lõi Zero-Waste cho context guard, validator, sandbox, session logging, và patch workflow. | `Sprint & Backlog Window`, `AI Log Signals`, `MCP Server tools` | 9 |
| `github_integration` | Luồng làm việc Git local và GitHub integration cho branch, commit, và PR orchestration. | `Plugins Ecosystem`, `MCP Server tools` | 4 |

## Theo Plugin

### 1. `antigravity_sync`

Managed in:
- `Antigravity Brain Logs`
- `Plugins Ecosystem`

- Owner: `Knowledge / UX`
- Version: `1.0.0`

| Tool | Muc dich nhanh |
|---|---|
| `read_historical_brain` | Thuoc plugin `antigravity_sync` |

### 2. `core_system`

Managed in:
- `Projects tab`
- `Sprint & Backlog Window`
- `MCP Server tools`

- Owner: `Backend`
- Version: `1.0.0`

| Tool | Muc dich nhanh |
|---|---|
| `assign_backlog_agent_tag` | Thuoc plugin `core_system` |
| `claim_backlog_item` | Thuoc plugin `core_system` |
| `create_backlog_item` | Thuoc plugin `core_system` |
| `create_sprint` | Thuoc plugin `core_system` |
| `get_active_tool_catalog` | Thuoc plugin `core_system` |
| `get_project_sync_status` | Thuoc plugin `core_system` |
| `list_backlog_claim_events` | Thuoc plugin `core_system` |
| `list_project_assets` | Thuoc plugin `core_system` |
| `release_backlog_item` | Thuoc plugin `core_system` |
| `review_code_architecture` | Thuoc plugin `core_system` |
| `search_codebase` | Thuoc plugin `core_system` |
| `search_past_decisions` | Thuoc plugin `core_system` |
| `store_project_memory` | Thuoc plugin `core_system` |
| `update_backlog_item` | Thuoc plugin `core_system` |
| `update_sprint` | Thuoc plugin `core_system` |
| `upsert_project` | Thuoc plugin `core_system` |

### 3. `core_zero_waste`

Managed in:
- `Sprint & Backlog Window`
- `AI Log Signals`
- `MCP Server tools`

- Owner: `Backend`
- Version: `1.0.0`

| Tool | Muc dich nhanh |
|---|---|
| `apply_safe_patch` | Thuoc plugin `core_zero_waste` |
| `check_attempt_trap` | Thuoc plugin `core_zero_waste` |
| `create_execution_plan` | Thuoc plugin `core_zero_waste` |
| `get_project_context` | Thuoc plugin `core_zero_waste` |
| `log_session_v2` | Thuoc plugin `core_zero_waste` |
| `review_architecture_map` | Thuoc plugin `core_zero_waste` |
| `run_code_ephemeral` | Thuoc plugin `core_zero_waste` |
| `search_semantic_context` | Thuoc plugin `core_zero_waste` |
| `validate_syntax_lint` | Thuoc plugin `core_zero_waste` |

### 4. `github_integration`

Managed in:
- `Plugins Ecosystem`
- `MCP Server tools`

- Owner: `Backend + Infra`
- Version: `1.0.0`

| Tool | Muc dich nhanh |
|---|---|
| `git_local_checkout` | Thuoc plugin `github_integration` |
| `git_local_commit` | Thuoc plugin `github_integration` |
| `git_local_status` | Thuoc plugin `github_integration` |
| `github_remote_create_pr` | Thuoc plugin `github_integration` |

## Ghi chu

- File nay duoc sinh tu dong. Khong can cap nhat tay khi them tool moi.
- Neu plugin moi duoc dang ky thanh cong, lan boot tiep theo se tu dong cap nhat catalog.
- Agent co the doc nhanh catalog nay thay vi quet lai toan bo codebase.
