# Sơ đồ Kiến trúc Code (Code Wiring)

> Sơ đồ này được cập nhật tự động bằng `ast_analyzer.py`. Nó bóc tách cấu trúc hàm/class trực tiếp từ mã nguồn mà không cần Regex.

## File: `dashboard\app.py`
- **Functions**: load_data
- **Dependencies**: pandas, streamlit, os, psycopg2

## File: `mcp_server\ast_analyzer.py`
- **Functions**: analyze_ast
- **Dependencies**: ast, os

## File: `mcp_server\init_mcp.py`
- **Functions**: init_project
- **Dependencies**: os, psycopg2

## File: `mcp_server\main.py`
- **Functions**: get_db_conn, safe_tool, manage_sprint, log_session_v2, get_project_context, store_project_memory, search_past_decisions, search_codebase, review_code_architecture, root, wrapper
- **Dependencies**: ast_analyzer, watcher, dotenv, starlette.routing, mcp.server.sse, sys, starlette.applications, vector_db, logging, uvicorn, fastapi, mcp.server.fastmcp, psycopg2, functools, time, psycopg2.extras, os

## File: `mcp_server\temp_init.py`
- **Functions**: run
- **Dependencies**: time, psycopg2

## File: `mcp_server\vector_db.py`
- **Classes**: ChromaBackend, PgVectorBackend
- **Functions**: get_embedding_model, embed_text, store_memory, search_memory, __init__, _get_collection, store_memory, search_memory, store_memory, search_memory
- **Dependencies**: sentence_transformers, logging, chromadb, json, psycopg2, os, uuid

## File: `mcp_server\watcher.py`
- **Classes**: ProjectWatchdogHandler
- **Functions**: start_watcher, __init__, on_modified, log_to_db
- **Dependencies**: watchdog.observers, logging, psycopg2, vector_db, time, os, watchdog.events, threading
