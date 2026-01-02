-- ============================================================================
-- AI-Native MVP - Risks Table
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

CREATE TABLE IF NOT EXISTS risks (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255),
    student_id VARCHAR(255) NOT NULL,
    activity_id VARCHAR(255),
    risk_type VARCHAR(100) NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    dimension VARCHAR(50) NOT NULL,
    description TEXT,
    evidence JSONB,
    trace_ids JSONB,
    recommendations JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_risks_session ON risks(session_id);
CREATE INDEX IF NOT EXISTS idx_risks_student ON risks(student_id);
CREATE INDEX IF NOT EXISTS idx_risks_resolved ON risks(resolved);
CREATE INDEX IF NOT EXISTS idx_student_resolved ON risks(student_id, resolved);

SELECT 'Risks table created!' AS status;
