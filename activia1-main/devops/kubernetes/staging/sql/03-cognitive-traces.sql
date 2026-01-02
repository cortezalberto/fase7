-- ============================================================================
-- AI-Native MVP - Cognitive Traces Table
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

CREATE TABLE IF NOT EXISTS cognitive_traces (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    student_id VARCHAR(255) NOT NULL,
    activity_id VARCHAR(255) NOT NULL,
    trace_level VARCHAR(50) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    cognitive_state VARCHAR(100),
    cognitive_intent VARCHAR(100),
    content TEXT,
    ai_involvement FLOAT,
    response_content TEXT,
    trace_metadata JSONB,
    blocked BOOLEAN DEFAULT FALSE,
    block_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_traces_session ON cognitive_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_student ON cognitive_traces(student_id);
CREATE INDEX IF NOT EXISTS idx_traces_activity ON cognitive_traces(activity_id);
CREATE INDEX IF NOT EXISTS idx_session_type ON cognitive_traces(session_id, interaction_type);

SELECT 'Cognitive traces table created!' AS status;
