-- Bảng dự án
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name TEXT UNIQUE NOT NULL,
    description TEXT
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
    status TEXT DEFAULT 'To Do', -- [To Do, In Progress, Blocked, Done, Cancelled]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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