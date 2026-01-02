-- ============================================================================
-- AI-Native MVP - Student Profiles Table
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

CREATE TABLE IF NOT EXISTS student_profiles (
    id VARCHAR(255) PRIMARY KEY,
    student_id VARCHAR(255) UNIQUE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    average_ai_dependency FLOAT DEFAULT 0.0,
    total_risks INTEGER DEFAULT 0,
    critical_risks INTEGER DEFAULT 0,
    risk_trends JSONB,
    competency_evolution JSONB,
    last_activity_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_profiles_student ON student_profiles(student_id);

SELECT 'Student profiles table created!' AS status;
