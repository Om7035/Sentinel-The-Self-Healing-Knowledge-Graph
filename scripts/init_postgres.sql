-- Sentinel PostgreSQL Initialization

CREATE TABLE IF NOT EXISTS job_status (
    job_id VARCHAR(255) PRIMARY KEY,
    url TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    result JSONB,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_job_status_url ON job_status(url);
