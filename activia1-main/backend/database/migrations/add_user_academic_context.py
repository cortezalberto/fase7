"""
Migration: Add academic context fields to users table

Cortez65.2: Enables student course/commission display without LTI integration.

For testing phase when Moodle is not yet integrated, students can have
their course and commission assigned manually or via admin API.

New fields:
- course_name: Current course name (e.g., "Programacion I")
- commission: Commission code (e.g., "K1021")

Run with:
    python -m backend.database.migrations.add_user_academic_context
"""
import logging
from sqlalchemy import text
from ..session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add academic context fields to users table."""
    db = SessionLocal()
    try:
        # Define new columns to add
        new_columns = [
            ("course_name", "VARCHAR(255)", True),
            ("commission", "VARCHAR(100)", True),
        ]

        for col_name, col_type, nullable in new_columns:
            # Check if column already exists
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users'
                AND column_name = :col_name
            """)
            result = db.execute(check_query, {"col_name": col_name}).fetchone()

            if result:
                logger.info("Column '%s' already exists in users table", col_name)
                continue

            # Add the column
            null_clause = "NULL" if nullable else "NOT NULL"
            alter_query = text(f"""
                ALTER TABLE users
                ADD COLUMN {col_name} {col_type} {null_clause}
            """)
            db.execute(alter_query)
            logger.info("Added column '%s' to users table", col_name)

        # Add index for commission lookups (useful for teacher queries)
        idx_name = "idx_user_commission"
        check_idx = text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'users' AND indexname = :idx_name
        """)
        result = db.execute(check_idx, {"idx_name": idx_name}).fetchone()

        if not result:
            create_idx = text(f"""
                CREATE INDEX {idx_name} ON users (commission)
            """)
            db.execute(create_idx)
            logger.info("Created index '%s'", idx_name)
        else:
            logger.info("Index '%s' already exists", idx_name)

        db.commit()
        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error("Migration failed: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Running migration: add_user_academic_context")
    run_migration()
    logger.info("Migration completed")
