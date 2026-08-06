# Supabase Schema for RIG Department Knowledge

Tables for pushing scraped knowledge data to Supabase.

## Tables

```sql
CREATE TABLE IF NOT EXISTS rig_knowledge_sources (
    id SERIAL PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    content TEXT,
    metadata JSONB,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    hash VARCHAR(64),
    bytes INTEGER
);

CREATE TABLE IF NOT EXISTS rig_knowledge_notes (
    id SERIAL PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    note_path TEXT NOT NULL,
    note_content TEXT,
    source_type VARCHAR(50),
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    hash VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS rig_department_goals (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL UNIQUE,
    daily_goal TEXT,
    weekly_goal TEXT,
    monthly_goal TEXT,
    arr_mechanism TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rig_department_teams (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    worker_id VARCHAR(100) NOT NULL,
    purpose TEXT,
    allowed_tools TEXT[],
    quality_bar TEXT,
    proof_required BOOLEAN DEFAULT TRUE,
    UNIQUE(agent_id, worker_id)
);

CREATE TABLE IF NOT EXISTS rig_ingestion_ledger (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    department VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    title TEXT,
    path TEXT,
    bytes INTEGER,
    hash VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_dept ON rig_knowledge_sources(department);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON rig_knowledge_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_notes_dept ON rig_knowledge_notes(department);
CREATE INDEX IF NOT EXISTS idx_ledger_dept ON rig_ingestion_ledger(department);
```

## Push Script

```bash
python3 ~/bin/rig_supabase_push.py --dry-run  # Generate SQL
python3 ~/bin/rig_supabase_push.py --project-url <url> --api-key <key>  # Execute
```
