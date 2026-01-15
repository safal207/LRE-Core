-- LRE Core Persistence Schema v1.0
-- Single-table design for maximum simplicity and query performance

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,     -- ISO 8601 format
    direction TEXT NOT NULL,     -- 'INBOUND' or 'OUTBOUND'
    payload TEXT,                -- JSON string
    meta TEXT,                   -- JSON string (optional)
    created_at REAL NOT NULL,    -- Unix timestamp for fast queries

    -- Validation constraints
    CHECK (direction IN ('INBOUND', 'OUTBOUND')),
    CHECK (length(trace_id) > 0),
    CHECK (length(type) > 0)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_trace_id ON events(trace_id);
CREATE INDEX IF NOT EXISTS idx_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_created_at ON events(created_at DESC);

-- Agent presence tracking (JSON extract from payload)
CREATE INDEX IF NOT EXISTS idx_agent_id ON events(
    json_extract(payload, '$.agent_id')
) WHERE json_extract(payload, '$.agent_id') IS NOT NULL;

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_trace_type ON events(trace_id, type);

-- View for recent agent activity (optional helper)
CREATE VIEW IF NOT EXISTS recent_agent_pings AS
SELECT
    json_extract(payload, '$.agent_id') as agent_id,
    MAX(created_at) as last_ping,
    COUNT(*) as ping_count
FROM events
WHERE type = 'system_ping'
  AND json_extract(payload, '$.agent_id') IS NOT NULL
GROUP BY json_extract(payload, '$.agent_id');