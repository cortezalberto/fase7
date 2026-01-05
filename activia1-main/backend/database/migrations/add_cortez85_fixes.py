"""
Migration: Add Cortez85 database fixes.

This migration adds:
1. Missing indexes on exercises.deleted_at for soft delete queries
2. Composite index on exercises (is_active, deleted_at) for common query pattern

Run with:
    python -m backend.database.migrations.add_cortez85_fixes
"""
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Execute the migration."""
    import psycopg2

    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ai_native:dev_postgres_password_12345@localhost:5433/ai_native"
    )

    logger.info("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    try:
        # ========================================================
        # 1. Add index on exercises.deleted_at
        # ========================================================
        logger.info("Creating index idx_exercises_deleted on exercises.deleted_at...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_exercises_deleted
            ON exercises(deleted_at);
        """)

        # ========================================================
        # 2. Add composite index on (is_active, deleted_at)
        # ========================================================
        logger.info("Creating composite index idx_exercises_active_deleted...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_exercises_active_deleted
            ON exercises(is_active, deleted_at);
        """)

        # ========================================================
        # 3. Verify deleted_at columns exist in unidades, apuntes, archivos_adjuntos
        # ========================================================
        tables_to_check = ['unidades', 'apuntes', 'archivos_adjuntos']

        for table in tables_to_check:
            logger.info(f"Checking deleted_at column in {table}...")
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name = 'deleted_at'
            """, (table,))

            if cursor.fetchone() is None:
                logger.info(f"Adding deleted_at column to {table}...")
                cursor.execute(f"""
                    ALTER TABLE {table}
                    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
                """)
                # Create index for soft delete queries
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table}_deleted
                    ON {table}(deleted_at);
                """)
            else:
                logger.info(f"Column deleted_at already exists in {table}")

        # Commit all changes
        conn.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def rollback_migration():
    """Rollback the migration (remove indexes)."""
    import psycopg2

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ai_native:dev_postgres_password_12345@localhost:5433/ai_native"
    )

    logger.info("Connecting to database for rollback...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    try:
        logger.info("Dropping idx_exercises_deleted...")
        cursor.execute("DROP INDEX IF EXISTS idx_exercises_deleted;")

        logger.info("Dropping idx_exercises_active_deleted...")
        cursor.execute("DROP INDEX IF EXISTS idx_exercises_active_deleted;")

        conn.commit()
        logger.info("Rollback completed successfully!")

    except Exception as e:
        conn.rollback()
        logger.error(f"Rollback failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        logger.info("Running rollback...")
        rollback_migration()
    else:
        logger.info("Running migration...")
        run_migration()
