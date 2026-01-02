-- ============================================================================
-- AI-Native MVP - Trace Sequences Table
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

CREATE TABLE IF NOT EXISTS trace_sequences (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    trace_ids JSONB NOT NULL,
    reasoning_path TEXT,
    strategy_changes JSONB,
    ai_dependency_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sequences_session ON trace_sequences(session_id);

SELECT 'Trace sequences table created!' AS status;
