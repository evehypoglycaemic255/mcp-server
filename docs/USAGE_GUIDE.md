# MCP Commander - System Usage Guide & Agent Collaboration Rules

## 1. Purpose of This Document

This guide explains how to use MCP Commander in a multi-agent environment, where multiple AI agents collaborate on tasks, ensuring no duplication and enforcing strict rules to maintain system integrity and prevent conflicting edits.

## 2. Key Concepts

### 2.1 Task Assignment via AI Tags

Each backlog task card is assigned an `agent_tag` (e.g., `agent:copilot`, `agent:codex-v2`). This tag ensures:
- Only the assigned agent works on that task.
- Other agents recognize the task is "claimed" and skip it.
- If a task is unassigned (`agent:unassigned` or empty), any available agent can pick it up.

### 2.2 Sprint & Backlog Workflow

1. **Create Sprint**: Define goals, deadline, and active status.
2. **Create Backlog Items**: Add tasks with initial priority, effort estimate, and optional agent tag.
3. **Assign Agent**: Via dashboard "Assign AI Tag / Agent" button or `assign_backlog_agent_tag(task_id, ai_tag)` MCP tool.
4. **Execute Task**: Agent claims the task, updates status to "In Progress", implements code.
5. **Mark Complete**: Agent updates status to "Done", commits changes, logs results.

### 2.3 RBAC (Role-Based Access Control)

- **Admin** role: Can execute write operations (`create_sprint`, `update_sprint`, `upsert_project`, `update_backlog_item`, `assign_backlog_agent_tag`).
- **Readonly** role: Can only query tasks, view logs, inspect backlog.
- **Anonymous** (if AUTH_ENABLED=false): All tools available.

Access is controlled via API key header (`x-api-key`) at the `/mcp/sse` endpoint.

## 3. How AI Agents Collaborate

### 3.1 Agent Handshake Protocol

```
1. Agent checks MCP Commander for open tasks.
   GET /mcp/sse (authenticated)
   → retrieve backlog_items with status="To Do" OR status="Unassigned"

2. Agent filters tasks by agent_tag:
   - If agent_tag matches agent ID -> CLAIM the task
   - If agent_tag is empty or "agent:unassigned" -> agent CAN CLAIM
   - If agent_tag ≠ agent ID -> agent SKIPS (another agent owns it)

3. Agent calls assign_backlog_agent_tag(task_id, "agent:<my_id>")
   → system logs attempt in system_tool_logs (status=SUCCESS/FORBIDDEN)

4. Agent updates status → "In Progress"
   → Updates agent_tag → retained (locked)

5. Agent works (code patches, commits, etc.)

6. Agent updates status → "Done"
   → system logs completion, generates sync manifest if sprint is marked "Completed"
```

### 3.2 Conflict Prevention Rules

| Rule | Enforcement | Consequence |
|------|-------------|-------------|
| Task can only be assigned to ONE agent | `agent_tag` column unique state per task | Agent attempting reassign gets `FORBIDDEN` if already claimed |
| Only admin role can reassign | RBAC check on `assign_backlog_agent_tag` tool | Non-admin gets HTTP 401 or FORBIDDEN status |
| Task status must match agent work | Status validation in `update_backlog_item` | Mismatch logged in `system_tool_logs`, warning sent |
| No simultaneous patches to same file | **Optional**: file lock in `core/guard_tools.py` | Awaiting implementation (future sprint) |

### 3.3 Communication Between Agents

Agents communicate via:
1. **Shared Backlog**: View all tasks, status, and agent assignments.
2. **System Tool Logs**: Review tool calls, errors, and execution history.
3. **AI Sessions**: Stored in `ai_sessions` table—each agent logs tasks performed and pending logic.
4. **Sync Manifests**: When sprint completes, a `.last_sync.md` file is auto-generated in `docs/sprints_reports/` containing tracked documents and status.

Example: Agent A finishes task, marks "Done". Agent B sees status change and auto-triggers downstream tasks (if configured).

## 4. Enforcing Rules: Configuration & Policies

### 4.1 Setting Up Auth & RBAC

**In `.env` (mcp_server/):**
```env
MCP_AUTH_ENABLED=true
MCP_API_KEY=your-admin-key-here
MCP_API_KEY_ROLE=admin

MCP_API_READONLY_KEY=readonly-key-here
MCP_API_READONLY_ROLE=readonly

MCP_API_KEY_HEADER=x-api-key
```

**In `config/mcp_config.json`:**
```json
{
  "rbac": {
    "admin_tools": [
      "create_sprint",
      "update_sprint",
      "upsert_project",
      "update_backlog_item",
      "assign_backlog_agent_tag"
    ]
  }
}
```

### 4.2 Preventing Unauthorized Changes

1. **Tool-Level Guards** (`core/dependencies.py`):
   - `safe_tool` decorator checks RBAC before execution.
   - Status = "FORBIDDEN" if non-admin tries admin-only operation.
   - Logged to `system_tool_logs` with user role.

2. **API Key Validation** (`core/security.py`):
   - SSE endpoint `/mcp/sse` validates `x-api-key` header.
   - Returns HTTP 401 if key missing or invalid.
   - Sets context variable `current_user_role` for downstream checks.

3. **Dashboard Permission** (optional future feature):
   - Streamlit can display read-only UI for `readonly` role.
   - Write operations grayed out or hidden.

### 4.3 Audit Trail & Monitoring

All tool calls are logged in `system_tool_logs`:
- `tool_name`: function name
- `parameters`: sanitized input (passwords, tokens redacted)
- `status`: SUCCESS | ERROR | FORBIDDEN
- `message`: results or error reason
- `created_at`: timestamp

Query example:
```sql
SELECT tool_name, status, message, created_at
FROM system_tool_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

## 5. Using the Dashboard (Streamlit)

### 5.1 Sprint & Backlog Window

1. **Filter by Agent**: Dropdown "Filter Agent" shows all assigned agents.
2. **Table View**: Shows task ID, name, agent tag, priority, effort, status, sprint.
3. **Kanban View**: 5 columns (To Do, In Progress, Blocked, Done, Cancelled). Each card shows:
   - Task name
   - Agent tag (e.g., "Agent: agent:copilot")
   - Priority & Effort
   - Sprint allocation

### 5.2 Assigning Tasks

1. Select a task from the backlog table or Kanban.
2. Expand "Assign AI Tag / Agent" expander.
3. Enter agent tag (e.g., `agent:copilot`, `agent:codex-v2`).
4. Click "Assign Agent".
5. Confirmation: `✅ Assigned AI Tag '<tag>' to task <id>.`

### 5.3 Editing Tasks

1. Expand "Edit Selected Task".
2. Update Task Name, Description, Sprint, Priority, Effort, Status, Agent.
3. Click "Save Task Changes".
4. DB updates automatically with `updated_at` timestamp.

## 6. MCP Tool Reference for Agents

### Project Management

```python
# Create/update project
upsert_project(
    project_name: str,
    description: str = "",
    repo_path: str = ""
)

# Create sprint
create_sprint(
    project_name: str,
    sprint_name: str,
    goals: str = "",
    status: str = "Active",  # Active, Paused, Completed, Cancelled
    end_date: str = ""       # YYYY-MM-DD
)

# Update sprint
update_sprint(
    project_name: str,
    sprint_name: str,
    goals: str = "",
    status: str = "",
    end_date: str = ""
)
```

### Backlog & Task Management

```python
# Create backlog item
create_backlog_item(
    project_name: str,
    task_name: str,
    description: str = "",
    sprint_name: str = "",
    status: str = "To Do",
    priority: str = "Medium",  # Critical, High, Medium, Low
    effort: str = "M",         # S, M, L
    agent_tag: str = ""        # e.g., "agent:copilot"
)

# Update backlog item
update_backlog_item(
    project_name: str,
    task_name: str,
    description: str = "",
    sprint_name: str = "",
    status: str = "",
    priority: str = "",
    effort: str = "",
    agent_tag: str = ""
)

# Assign task to agent
assign_backlog_agent_tag(task_id: int, ai_tag: str)

# List project assets
list_project_assets(project_name: str)
```

### Memory & Context

```python
# Search semantic memory (from core_zero_waste)
search_memory(
    query: str,
    n_results: int = 5,
    is_codebase: bool = True
)

# Store memory
store_memory(
    project_name: str,
    content: str,
    metadata: dict = {},
    is_codebase: bool = True
)
```

## 7. Best Practices for Multi-Agent Workflows

### 7.1 Pre-Execution Checklist (for each agent)

- [ ] Verify authentication token / API key is valid.
- [ ] Check current user role (admin or readonly) – can I modify tasks?
- [ ] Query open backlog items with status="To Do".
- [ ] Scan for tasks with my `agent_tag` already assigned.
- [ ] Filter by language/skillset (e.g., only Python tasks).
- [ ] Review sprint goals and priority ranking.
- [ ] Claim ONE task at a time (avoid overcommit).

### 7.2 During Task Execution

- [ ] Call `assign_backlog_agent_tag(task_id, "agent:<my_id>")` to lock it.
- [ ] Update status to "In Progress" + log start time.
- [ ] Store intermediate memory: `store_memory(project, code_snippet, {"checkpoint": "phase_2"})`.
- [ ] If blocker detected: update status to "Blocked", leave comment in description.
- [ ] Ask for help: mention blockers in `system_tool_logs` message or reach out via AI session notes.

### 7.3 Post-Execution Handover

- [ ] Verify code quality, tests pass, no lint errors.
- [ ] Update status to "Done" (or "Blocked" if incomplete).
- [ ] Call `update_backlog_item(..., status="Done")`.
- [ ] Commit code with PR/merge request reference.
- [ ] If sprint is "Completed", system auto-generates sync manifest.
- [ ] Log learnings in `ai_sessions` for future reference.

### 7.4 Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| HTTP 401 at `/mcp/sse` | Invalid/missing API key | Check `.env`, regenerate key if needed |
| `FORBIDDEN in system_tool_logs` | Non-admin trying `update_sprint` | Escalate to admin or request role promotion |
| Task already claimed | `agent_tag` != your ID | Politely skip or request reassignment from admin |
| DB connection failed | PostgreSQL down or URL misconfigured | Check `docker ps`, verify `DATABASE_URL` in `.env` |

## 8. Metrics & Observability

### 8.1 Prometheus Metrics Endpoint

Access via: `GET http://localhost:8000/metrics`

Exposed metrics:
- `mcp_tool_calls_total{tool_name, status}`: Cumulative tool call count
- `mcp_tool_latency_seconds{tool_name}`: Tool execution time histogram

### 8.2 Health Check

Access via: `GET http://localhost:8000/health`

Response:
```json
{
  "status": "healthy",
  "db": "ok",
  "role": "admin"
}
```

Optional header for secret-protected health:
```
GET /health
x-healthcheck-token: <MCP_HEALTHCHECK_SECRET>
```

### 8.3 Logging

- **Structured logs**: JSON format with `timestamp`, `tool`, `status`, `duration_ms`.
- **Location**: `mcp_server/logs/` (if enabled) + Docker container stdout/stderr.

## 9. Troubleshooting

### "Agent already assigned to task"

**Problem**: Two agents try to claim the same task simultaneously.

**Solution**:
1. Admin checks `system_tool_logs` for conflicting `assign_backlog_agent_tag` calls.
2. Admin manually reassigns via dashboard "Assign AI Tag / Agent".
3. Losing agent picks next available task.

### "Permission denied: role cannot execute <tool>"

**Problem**: Non-admin tries admin-only tool like `update_sprint`.

**Solution**:
1. Check `.env` API_KEY and role assignment.
2. Request admin to run operation or grant `admin` role to your API key.
3. Alternatively, use `readonly` key for query-only operations.

### "No backlog items match filters"

**Problem**: All tasks are assigned or completed.

**Solution**:
1. Create new sprint or backlog items.
2. Check with admin to reassign "Done" tasks back to "To Do" if needed.
3. Review sprint goals—may need to define new work.

### "Sync manifest not generated after sprint completion"

**Problem**: Sprint marked "Completed" but no `.last_sync.md` created.

**Solution**:
1. Verify `docs/sprints_reports/` directory exists (or subdirs).
2. Check permissions: `mcp_server/plugins/core_system/` should be writable.
3. Manually trigger via `update_sprint(project_name, sprint_name, status="Completed")`.
4. Check app logs for `_write_sync_manifest` errors.

## 10. Future Enhancements

- [ ] File-level locking to prevent simultaneous patch conflicts.
- [ ] Automatic task reassignment if agent becomes inactive.
- [ ] Agent capability matrix (skills vs task requirements).
- [ ] Workflow pipelines (task A triggers task B).
- [ ] AI-driven priority ranking based on dependencies.
- [ ] Dashboard role-based UI rendering (admin vs readonly).

## 11. References

- Project root: [readme.md](../readme.md)
- Architecture: [v2_architecture.md](architecture/v2_architecture.md)
- Config: [mcp_config.json](../mcp_server/config/mcp_config.json)
- Security: [core/security.py](../mcp_server/core/security.py)
- RBAC: [core/config.py](../mcp_server/core/config.py)
- Audit: [docs/sprints_reports/sprint1_mcp_commander_remediation_tasks.md](sprints_reports/sprint1_mcp_commander_remediation_tasks.md)
