# Sơ đồ Kiến trúc Code (Code Wiring)

> Sơ đồ này được cập nhật tự động bằng `ast_analyzer.py`. Nó bóc tách cấu trúc hàm/class trực tiếp từ mã nguồn mà không cần Regex.

## File: `init_mcp.py`
- *Parse Error: invalid non-printable character U+FEFF (init_mcp.py, line 1)*

## File: `main.py`
- **Functions**: root, health, metrics
- **Dependencies**: os, logging, mcp.server.sse, core.metrics, dotenv, uvicorn, fastapi, sys, plugins, starlette.applications, starlette.routing, core.config, prometheus_client, core.database, core.security, mcp.server.fastmcp, core.watcher

## File: `migrate.py`
- **Functions**: run_migration
- **Dependencies**: os, psycopg2

## File: `migrate_plugins.py`
- **Functions**: create_plugin, main
- **Dependencies**: os, shutil, sys

## File: `minify_docs.py`
- **Functions**: minify_docstrings, replacer
- **Dependencies**: os, re

## File: `temp_init.py`
- **Functions**: run
- **Dependencies**: core.config, psycopg2, time

## File: `core\ast_analyzer.py`
- **Classes**: DependencyVisitor
- **Functions**: extract_semantic_chunks, analyze_ast, __init__, visit_Call
- **Dependencies**: json, ast, os

## File: `core\config.py`
- *Parse Error: invalid non-printable character U+FEFF (config.py, line 1)*

## File: `core\database.py`
- **Functions**: get_db_conn
- **Dependencies**: os, logging, psycopg2, core.config, time, core.schema

## File: `core\dependencies.py`
- *Parse Error: invalid non-printable character U+FEFF (dependencies.py, line 1)*

## File: `core\metrics.py`
- **Classes**: _NoOpMetric
- **Functions**: labels, inc, observe
- **Dependencies**: prometheus_client

## File: `core\schema.py`
- **Functions**: ensure_schema
- **Dependencies**: os

## File: `core\security.py`
- **Functions**: validate_api_key, set_current_user_role, get_current_user_role, reset_current_user_role
- **Dependencies**: os, contextvars

## File: `core\vector_db.py`
- **Classes**: ChromaBackend, PgVectorBackend
- **Functions**: get_embedding_model, embed_text, store_memory, search_memory, __init__, _get_collection, store_memory, search_memory, store_memory, search_memory
- **Dependencies**: sentence_transformers, os, logging, chromadb, psycopg2, core.config, json, uuid

## File: `core\watcher.py`
- **Classes**: ProjectWatchdogHandler
- **Functions**: start_watcher, __init__, on_modified, log_to_db
- **Dependencies**: core.config, os, logging, core.vector_db, threading, core.ast_analyzer, watchdog.events, watchdog.observers.polling, psycopg2, time, core.database

## File: `plugins\__init__.py`
- **Functions**: _sync_plugin_metadata, _write_active_tool_catalog, sync_active_tool_catalog, register_all_tools
- **Dependencies**: os, logging, yaml, plugins, pkgutil, importlib, pathlib, datetime

## File: `plugins\antigravity_sync\antigravity_tools.py`
- **Functions**: get_latest_folders, register_tools, read_historical_brain
- **Dependencies**: os, logging, core.dependencies, glob

## File: `plugins\antigravity_sync\__init__.py`
- **Functions**: register_tools
- **Dependencies**: importlib, os, logging

## File: `plugins\core_system\codebase_tools.py`
- **Functions**: register_tools, store_project_memory, search_past_decisions, search_codebase, review_code_architecture, get_active_tool_catalog
- **Dependencies**: os, core.vector_db, core.ast_analyzer, pathlib, core.dependencies

## File: `plugins\core_system\project_tools.py`
- **Functions**: _project_slug, _docs_root, _sync_manifest_paths, _sync_manifest_targets, _write_sync_manifest, _resolve_agent_tag, _is_unclaimed, _insert_claim_event, _get_project, _resolve_sprint_id, _get_backlog_item_for_update, create_backlog_item_record, claim_backlog_item_record, release_backlog_item_record, update_backlog_item_record, assign_backlog_agent_tag_record, register_tools, upsert_project, create_sprint, update_sprint, create_backlog_item, update_backlog_item, assign_backlog_agent_tag, claim_backlog_item, release_backlog_item, list_project_assets, list_backlog_claim_events, get_project_sync_status
- **Dependencies**: os, psycopg2.extras, re, core.dependencies, core.database, datetime

## File: `plugins\core_system\__init__.py`
- **Functions**: register_tools
- **Dependencies**: importlib, os, logging

## File: `plugins\core_zero_waste\context_tools.py`
- **Functions**: register_tools, search_semantic_context, review_architecture_map
- **Dependencies**: os, core.vector_db, core.ast_analyzer, psycopg2, core.config, json, core.dependencies

## File: `plugins\core_zero_waste\guard_tools.py`
- **Functions**: register_tools, check_attempt_trap
- **Dependencies**: hashlib, core.dependencies

## File: `plugins\core_zero_waste\memory_tools.py`
- **Functions**: register_tools, log_session_v2, get_project_context
- **Dependencies**: psycopg2.extras, core.database, core.dependencies

## File: `plugins\core_zero_waste\patch_tools.py`
- **Functions**: register_tools, apply_safe_patch
- **Dependencies**: ast, os, core.dependencies, core.config

## File: `plugins\core_zero_waste\planning_tools.py`
- *Parse Error: invalid non-printable character U+FEFF (planning_tools.py, line 1)*

## File: `plugins\core_zero_waste\sandbox_tools.py`
- **Functions**: register_tools, run_code_ephemeral
- **Dependencies**: os, tempfile, subprocess, core.config, core.dependencies

## File: `plugins\core_zero_waste\validator_tools.py`
- **Functions**: register_tools, validate_syntax_lint
- **Dependencies**: ast, core.dependencies

## File: `plugins\core_zero_waste\__init__.py`
- **Functions**: register_tools
- **Dependencies**: importlib, os, logging

## File: `plugins\github_integration\github_tools.py`
- **Functions**: register_tools, git_local_status, git_local_checkout, git_local_commit, github_remote_create_pr
- **Dependencies**: os, core.dependencies, subprocess, core.config

## File: `plugins\github_integration\__init__.py`
- **Functions**: register_tools
- **Dependencies**: importlib, os, logging
