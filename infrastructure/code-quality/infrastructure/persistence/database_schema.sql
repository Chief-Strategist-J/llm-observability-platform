-- Database schema for SonarQube Code Quality System

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    key VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_analysis_at TIMESTAMP WITH TIME ZONE,
    quality_gate_status VARCHAR(50) NOT NULL DEFAULT 'none',
    languages TEXT DEFAULT '',
    CONSTRAINT projects_status_check CHECK (status IN ('active', 'inactive', 'archived')),
    CONSTRAINT projects_quality_gate_status_check CHECK (quality_gate_status IN ('passed', 'failed', 'warning', 'none'))
);

-- Analyses table
CREATE TABLE IF NOT EXISTS analyses (
    id VARCHAR(255) PRIMARY KEY,
    project_key VARCHAR(255) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    commit_hash VARCHAR(40) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT analyses_status_check CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT analyses_project_key_fkey FOREIGN KEY (project_key) REFERENCES projects(key) ON DELETE CASCADE
);

-- Analysis issues table
CREATE TABLE IF NOT EXISTS analysis_issues (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    line_number INTEGER NOT NULL,
    rule VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    CONSTRAINT analysis_issues_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
    CONSTRAINT analysis_issues_type_check CHECK (type IN ('bug', 'vulnerability', 'code_smell', 'security_hotspot')),
    CONSTRAINT analysis_issues_severity_check CHECK (severity IN ('blocker', 'critical', 'major', 'minor', 'info'))
);

-- Analysis metrics table
CREATE TABLE IF NOT EXISTS analysis_metrics (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    formatted_value VARCHAR(255) NOT NULL,
    CONSTRAINT analysis_metrics_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
    CONSTRAINT analysis_metrics_unique UNIQUE (analysis_id, name)
);

-- Quality gates table
CREATE TABLE IF NOT EXISTS quality_gates (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    project_key VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'none',
    conditions TEXT DEFAULT '',
    CONSTRAINT quality_gates_project_key_fkey FOREIGN KEY (project_key) REFERENCES projects(key) ON DELETE CASCADE,
    CONSTRAINT quality_gates_status_check CHECK (status IN ('passed', 'failed', 'warning', 'none'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_analyses_project_key ON analyses(project_key);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_project_branch ON analyses(project_key, branch);

CREATE INDEX IF NOT EXISTS idx_analysis_issues_analysis_id ON analysis_issues(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_issues_severity ON analysis_issues(severity);
CREATE INDEX IF NOT EXISTS idx_analysis_issues_type ON analysis_issues(type);

CREATE INDEX IF NOT EXISTS idx_analysis_metrics_analysis_id ON analysis_metrics(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_metrics_name ON analysis_metrics(name);

CREATE INDEX IF NOT EXISTS idx_quality_gates_project_key ON quality_gates(project_key);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_analysis_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION update_analysis_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_project_last_analysis 
    BEFORE UPDATE ON projects 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analysis_completed_at_trigger 
    BEFORE UPDATE ON analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_analysis_completed_at();

-- Insert default quality gate
INSERT INTO quality_gates (id, name, project_key, status, conditions)
VALUES ('default', 'Default Quality Gate', 'system', 'passed', 'coverage >= 80|duplicated_lines_density <= 3')
ON CONFLICT (id) DO NOTHING;
