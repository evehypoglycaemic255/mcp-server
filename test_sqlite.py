import sqlite3
import os

vscode_path = r'C:\Users\minht\AppData\Roaming\Code\User\globalStorage\state.vscdb'
if not os.path.exists(vscode_path):
    print("WARNING: state.vscdb does not exist at", vscode_path)
else:
    conn = sqlite3.connect(vscode_path)
    print(f"Connected to {vscode_path}")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables:", tables)

    if 'ItemTable' in tables:
        cursor.execute("SELECT key, substr(value, 1, 150) FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%copilot%' OR key LIKE '%ai%' OR key LIKE '%codex%'")
        rows = cursor.fetchall()
        print("\n=== AI/Chat Keys ===")
        for key, val in rows:
            print(f"- {key}: {val}...")
    conn.close()

# Also check workspaceStorage for AI chat files
storage_path = r'C:\Users\minht\AppData\Roaming\Code\User\workspaceStorage'
if os.path.exists(storage_path):
    # Find any files related to AI memory
    count = 0
    for root, dirs, files in os.walk(storage_path):
        for f in files:
            if 'chat' in f.lower() or 'state.vscdb' in f.lower() or 'copilot' in f.lower() or 'codex' in f.lower():
                print(f"Found Workspace AI File: {os.path.join(root, f)}")
                count += 1
                if count > 15:
                    break
        if count > 15:
            break
