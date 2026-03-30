-- Bảng dự án
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name TEXT UNIQUE NOT NULL,
    description TEXT,
    repo_path TEXT
);

-- Bảng Sprint
CREATE TABLE IF NOT EXISTS sprints (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    sprint_name TEXT NOT NULL,
    goals TEXT,
    status TEXT DEFAULT 'Active', -- Active, Completed
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP
);
-- Bảng Backlog (Chứa Task Agile)
CREATE TABLE IF NOT EXISTS backlog_items (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    sprint_id INTEGER REFERENCES sprints(id), -- NULL neu o trang thai backlog cho
    task_name TEXT NOT NULL,
    description TEXT,
    agent_tag TEXT DEFAULT '',
    claim_status TEXT DEFAULT 'Unclaimed',
    claimed_at TIMESTAMP,
    claim_version INTEGER DEFAULT 0,
    priority TEXT DEFAULT 'Medium',
    effort TEXT DEFAULT 'M',
    status TEXT DEFAULT 'To Do', -- [To Do, In Progress, Blocked, Done, Cancelled]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backlog_claim_events (
    id SERIAL PRIMARY KEY,
    backlog_item_id INTEGER REFERENCES backlog_items(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor_agent_tag TEXT DEFAULT '',
    previous_agent_tag TEXT DEFAULT '',
    new_agent_tag TEXT DEFAULT '',
    note TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Nhật ký/Task ai_sessions cũ
CREATE TABLE IF NOT EXISTS ai_sessions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    sprint_id INTEGER REFERENCES sprints(id),
    task_performed TEXT,
    implemented_logic TEXT,
    pending_tasks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Bảng Nhật ký Tool Mới (Dashboard Tab 4)
CREATE TABLE IF NOT EXISTS system_tool_logs (
    id SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL,
    parameters TEXT,
    status TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cài đặt Extension Vector và Bảng Vector
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ai_memory_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    collection_name TEXT,
    content TEXT,
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VIEW TỔNG HỢP THEO DÕI SPRINT (Cho Dashboard)
CREATE OR REPLACE VIEW v_sprint_monitoring AS
SELECT 
    p.project_name,
    s.sprint_name,
    s.status as sprint_status,
    s.goals,
    COUNT(asess.id) as total_tasks,
    MAX(asess.created_at) as last_activity
FROM projects p
JOIN sprints s ON p.id = s.project_id
LEFT JOIN ai_sessions asess ON s.id = asess.sprint_id
GROUP BY p.project_name, s.sprint_name, s.status, s.goals;

-- Insert dữ liệu mẫu
INSERT INTO projects (project_name, description) VALUES 
('DemoProject', 'Core AI Engine'),
('PTXS', 'Lottery Data Analysis'),
('Sentinel', 'AI Automation Agent');

ALTER TABLE projects ADD COLUMN IF NOT EXISTS repo_path TEXT;
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS agent_tag TEXT DEFAULT '';
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS claim_status TEXT DEFAULT 'Unclaimed';
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMP;
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS claim_version INTEGER DEFAULT 0;
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'Medium';
ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS effort TEXT DEFAULT 'M';
