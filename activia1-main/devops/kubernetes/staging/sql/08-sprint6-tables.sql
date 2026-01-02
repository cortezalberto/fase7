-- ============================================================================
-- AI-Native MVP - Sprint 6 Tables (Interview & Incident Simulations)
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

-- Interview Sessions (IT-IA)
CREATE TABLE IF NOT EXISTS interview_sessions (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    student_id VARCHAR(255) NOT NULL,
    interview_type VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(50) NOT NULL,
    questions_asked JSONB,
    responses JSONB,
    evaluation_score FLOAT,
    evaluation_breakdown JSONB,
    status VARCHAR(50) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interview_session ON interview_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_interview_student ON interview_sessions(student_id);

-- Incident Simulations (IR-IA)
CREATE TABLE IF NOT EXISTS incident_simulations (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    student_id VARCHAR(255) NOT NULL,
    incident_type VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    metrics JSONB,
    diagnosis_steps JSONB,
    resolution TEXT,
    resolution_score FLOAT,
    resolution_time_minutes INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_incident_session ON incident_simulations(session_id);
CREATE INDEX IF NOT EXISTS idx_incident_student ON incident_simulations(student_id);

SELECT 'Sprint 6 tables created!' AS status;
