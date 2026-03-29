D:\WORK\1.MCP_SERVER\
├── .windsurfrules (hoặc .cursorrules) # [Tuỳ chọn] File cấu hình gốc để "ép" AI phải đọc thư mục rules\ mỗi khi mở project
├── rules\                             # (DÀNH CHO AI ĐỌC - READ ONLY)
│   ├── development_rules.md           # Kỷ luật code, quy ước viết RAG/Python
│   └── architecture_guidelines.md     # Nguyên tắc khi thiết kế kiến trúc
├── docs\                              # (DÀNH CHO AI GHI & ĐỌC - READ/WRITE)
│   ├── architecture\                  
│   │   ├── v1_basic_memory.md         # Bản vẽ kiến trúc tĩnh
│   │   └── v2_rag_memory.md           # Chứa các bản update linh hoạt
│   └── sprints_reports\               
│       └── sprint_1_report.md         # File AI sẽ tự động sinh và viết tóm tắt ngay sau khi kết thúc 1 Sprint
├── mcp_server\                        # (THƯ MỤC CODE CHÍNH)
│   ├── main.py
│   └── ...
