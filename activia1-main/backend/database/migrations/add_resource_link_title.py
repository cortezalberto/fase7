"""
Migration: Add resource_link_title to lti_sessions table

Cortez65.1: Adds the activity name field from Moodle LTI launches.

This allows storing the name of the Moodle activity (e.g., "Ejercicio 1: Variables")
that triggered the LTI launch, in addition to the resource_link_id.

Run with:
    python -m backend.database.migrations.add_resource_link_title
"""
import logging
from sqlalchemy import text
from ..session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add resource_link_title column to lti_sessions table."""
    db = SessionLocal()
    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'lti_sessions'
            AND column_name = 'resource_link_title'
        """)
        result = db.execute(check_query).fetchone()

        if result:
            logger.info("Column 'resource_link_title' already exists in lti_sessions table")
            return

        # Add the column
        alter_query = text("""
            ALTER TABLE lti_sessions
            ADD COLUMN resource_link_title VARCHAR(255) NULL
        """)
        db.execute(alter_query)
        db.commit()

        logger.info("Successfully added 'resource_link_title' column to lti_sessions table")

    except Exception as e:
        logger.error("Migration failed: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Running migration: add_resource_link_title")
    run_migration()
    logger.info("Migration completed successfully")
