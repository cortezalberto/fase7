"""
Migration: Add traceability improvements (Cortez82)

This migration adds:
1. teacher_interventions table - for persisting alert acknowledgments
2. sessions.course_id column - for filtering by course
3. Trigger function for trace_count synchronization

Run with:
    python -m backend.database.migrations.add_traceability_improvements
"""
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


def run_migration():
    """Execute the migration."""
    import psycopg2
    from psycopg2 import sql

    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ai_native:dev_postgres_password_12345@localhost:5433/ai_native"
    )

    print(f"Connecting to database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    try:
        # ========================================================
        # 1. Create teacher_interventions table
        # ========================================================
        print("Creating teacher_interventions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_interventions (
                id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                teacher_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                student_id VARCHAR(100) NOT NULL,
                session_id VARCHAR(36) REFERENCES sessions(id) ON DELETE SET NULL,
                alert_id VARCHAR(100),
                intervention_type VARCHAR(50) NOT NULL DEFAULT 'alert_acknowledgment',
                notes TEXT,
                action_taken TEXT,
                status VARCHAR(30) DEFAULT 'acknowledged',
                resolution_notes TEXT,
                resolved_at TIMESTAMP WITH TIME ZONE,
                alert_context JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT ck_intervention_type_valid CHECK (
                    intervention_type IN (
                        'alert_acknowledgment', 'direct_message', 'grade_adjustment',
                        'remediation_plan', 'meeting_scheduled', 'resource_shared', 'follow_up'
                    )
                ),
                CONSTRAINT ck_intervention_status_valid CHECK (
                    status IN ('acknowledged', 'in_progress', 'resolved', 'escalated', 'closed')
                )
            );
        """)

        # Create indexes for teacher_interventions
        print("Creating indexes for teacher_interventions...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intervention_teacher_status
            ON teacher_interventions(teacher_id, status);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intervention_student
            ON teacher_interventions(student_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intervention_alert
            ON teacher_interventions(alert_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intervention_created
            ON teacher_interventions(created_at);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intervention_type_status
            ON teacher_interventions(intervention_type, status);
        """)

        # ========================================================
        # 2. Add course_id to sessions table
        # ========================================================
        print("Adding course_id to sessions table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'sessions' AND column_name = 'course_id'
                ) THEN
                    ALTER TABLE sessions ADD COLUMN course_id VARCHAR(100);
                END IF;
            END $$;
        """)

        # Create indexes for course_id
        print("Creating indexes for sessions.course_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_course
            ON sessions(course_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_course_status
            ON sessions(course_id, status);
        """)

        # ========================================================
        # 3. Add trace_count column to sessions if not exists
        # ========================================================
        print("Adding trace_count to sessions table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'sessions' AND column_name = 'trace_count'
                ) THEN
                    ALTER TABLE sessions ADD COLUMN trace_count INTEGER DEFAULT 0;
                END IF;
            END $$;
        """)

        # ========================================================
        # 4. Create trigger function for trace_count sync
        # ========================================================
        print("Creating trigger function for trace_count synchronization...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_session_trace_count()
            RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    UPDATE sessions
                    SET trace_count = COALESCE(trace_count, 0) + 1,
                        updated_at = NOW()
                    WHERE id = NEW.session_id;
                ELSIF TG_OP = 'DELETE' THEN
                    UPDATE sessions
                    SET trace_count = GREATEST(COALESCE(trace_count, 0) - 1, 0),
                        updated_at = NOW()
                    WHERE id = OLD.session_id;
                END IF;
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create the trigger
        print("Creating trigger on cognitive_traces...")
        cursor.execute("""
            DROP TRIGGER IF EXISTS trg_update_session_trace_count ON cognitive_traces;
        """)
        cursor.execute("""
            CREATE TRIGGER trg_update_session_trace_count
            AFTER INSERT OR DELETE ON cognitive_traces
            FOR EACH ROW
            EXECUTE FUNCTION update_session_trace_count();
        """)

        # ========================================================
        # 5. Sync existing trace counts
        # ========================================================
        print("Synchronizing existing trace counts...")
        cursor.execute("""
            UPDATE sessions s
            SET trace_count = (
                SELECT COUNT(*) FROM cognitive_traces ct
                WHERE ct.session_id = s.id
            )
            WHERE EXISTS (
                SELECT 1 FROM cognitive_traces ct WHERE ct.session_id = s.id
            );
        """)

        # Commit all changes
        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
