-- ============================================================================
-- AI-Native MVP - Activities Table
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

CREATE TABLE IF NOT EXISTS activities (
    id VARCHAR(255) PRIMARY KEY,
    activity_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,
    subject VARCHAR(255),
    difficulty VARCHAR(50),
    estimated_duration_minutes INTEGER,
    teacher_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    pedagogical_policies JSONB,
    evaluation_criteria JSONB,
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_activity_teacher_status ON activities(teacher_id, status);
CREATE INDEX IF NOT EXISTS idx_activity_status_created ON activities(status, created_at);
CREATE INDEX IF NOT EXISTS idx_activity_subject_status ON activities(subject, status);

SELECT 'Activities table created!' AS status;
