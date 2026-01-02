-- ============================================================================
-- AI-Native MVP - Sample Data (Optional)
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- Run this script only if you want sample data for testing
-- ============================================================================

-- Sample activity
INSERT INTO activities (id, activity_id, title, description, subject, difficulty, status, teacher_id, created_at)
VALUES (
    'act_001',
    'prog2_tp1_colas',
    'Trabajo Práctico 1: Colas Circulares',
    'Implementar una cola circular en C con operaciones básicas',
    'Programación II',
    'INTERMEDIO',
    'active',
    'teacher_001',
    CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Sample session
INSERT INTO sessions (id, student_id, activity_id, mode, start_time, status, created_at)
VALUES (
    'session_sample_001',
    'student_demo',
    'prog2_tp1_colas',
    'TUTOR',
    CURRENT_TIMESTAMP,
    'active',
    CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

SELECT 'Sample data created!' AS status;
