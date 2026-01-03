"""
Migration: Add Moodle/LTI fields to activities table

Cortez65.1: Enables automatic activity matching when students launch from Moodle.

The teacher can configure an activity with Moodle course info:
- moodle_course_id: The context_id from Moodle (unique course identifier)
- moodle_course_name: The context_title (course name for display)
- moodle_course_label: The context_label (commission code like "PROG1-A")
- moodle_resource_name: The resource_link_title (activity name in Moodle)

When a student launches from Moodle, AI-Native can automatically find
the corresponding activity by matching these fields.

Run with:
    python -m backend.database.migrations.add_moodle_fields_to_activities
"""
import logging
from sqlalchemy import text
from ..session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add Moodle/LTI fields to activities table."""
    db = SessionLocal()
    try:
        # Define new columns to add
        new_columns = [
            ("moodle_course_id", "VARCHAR(255)", True),
            ("moodle_course_name", "VARCHAR(255)", True),
            ("moodle_course_label", "VARCHAR(100)", True),
            ("moodle_resource_name", "VARCHAR(255)", True),
        ]

        for col_name, col_type, nullable in new_columns:
            # Check if column already exists
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'activities'
                AND column_name = :col_name
            """)
            result = db.execute(check_query, {"col_name": col_name}).fetchone()

            if result:
                logger.info("Column '%s' already exists in activities table", col_name)
                continue

            # Add the column
            null_clause = "NULL" if nullable else "NOT NULL"
            alter_query = text(f"""
                ALTER TABLE activities
                ADD COLUMN {col_name} {col_type} {null_clause}
            """)
            db.execute(alter_query)
            logger.info("Added column '%s' to activities table", col_name)

        # Add indexes for efficient lookups
        indexes = [
            ("idx_activity_moodle_course", "moodle_course_id"),
            ("idx_activity_moodle_resource", "moodle_resource_name"),
        ]

        for idx_name, col_name in indexes:
            # Check if index exists
            check_idx = text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'activities' AND indexname = :idx_name
            """)
            result = db.execute(check_idx, {"idx_name": idx_name}).fetchone()

            if result:
                logger.info("Index '%s' already exists", idx_name)
                continue

            # Create index
            create_idx = text(f"""
                CREATE INDEX {idx_name} ON activities ({col_name})
            """)
            db.execute(create_idx)
            logger.info("Created index '%s'", idx_name)

        # Add composite index for matching
        composite_idx_name = "idx_activity_moodle_match"
        check_composite = text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'activities' AND indexname = :idx_name
        """)
        result = db.execute(check_composite, {"idx_name": composite_idx_name}).fetchone()

        if not result:
            create_composite = text("""
                CREATE INDEX idx_activity_moodle_match
                ON activities (moodle_course_id, moodle_resource_name)
            """)
            db.execute(create_composite)
            logger.info("Created composite index 'idx_activity_moodle_match'")

        db.commit()
        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error("Migration failed: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Running migration: add_moodle_fields_to_activities")
    run_migration()
    logger.info("Migration completed")
