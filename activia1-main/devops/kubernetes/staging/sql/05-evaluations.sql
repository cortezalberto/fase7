-- ============================================================================
-- AI-Native MVP - Evaluations Table
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

CREATE TABLE IF NOT EXISTS evaluations (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    student_id VARCHAR(255) NOT NULL,
    activity_id VARCHAR(255) NOT NULL,
    overall_competency_level VARCHAR(50),
    overall_score FLOAT,
    dimensions JSONB,
    key_strengths JSONB,
    improvement_areas JSONB,
    recommendations JSONB,
    reasoning_analysis TEXT,
    git_analysis TEXT,
    ai_dependency_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_evaluations_session ON evaluations(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_student ON evaluations(student_id);
CREATE INDEX IF NOT EXISTS idx_student_activity_eval ON evaluations(student_id, activity_id);

SELECT 'Evaluations table created!' AS status;
