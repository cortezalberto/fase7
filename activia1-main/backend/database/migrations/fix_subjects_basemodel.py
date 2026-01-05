"""
Migration: Fix subjects table to include BaseModel columns.

Cortez76: The SubjectDB model was updated to inherit from BaseModel (Cortez74),
but the database table was not migrated. This adds the missing columns:
- id (UUID primary key)
- created_at (DateTime)
- updated_at (DateTime)

Run with: python -m backend.database.migrations.fix_subjects_basemodel
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

from ..config import SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def check_table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists."""
    return table_name in inspector.get_table_names()


def run_migration():
    """Add BaseModel columns to subjects table."""
    db = SessionLocal()
    inspector = inspect(engine)

    try:
        # Check if subjects table exists
        if not check_table_exists(inspector, 'subjects'):
            logger.info("Table 'subjects' does not exist. Skipping migration.")
            return

        logger.info("Starting subjects table migration...")

        # Determine dialect
        dialect = engine.dialect.name
        is_postgres = dialect == 'postgresql'
        is_sqlite = dialect == 'sqlite'

        logger.info(f"Database dialect: {dialect}")

        # Check which columns need to be added
        needs_id = not check_column_exists(inspector, 'subjects', 'id')
        needs_created_at = not check_column_exists(inspector, 'subjects', 'created_at')
        needs_updated_at = not check_column_exists(inspector, 'subjects', 'updated_at')

        if not needs_id and not needs_created_at and not needs_updated_at:
            logger.info("All BaseModel columns already exist. Migration not needed.")
            return

        # For SQLite, we need a different approach since ALTER TABLE is limited
        if is_sqlite:
            logger.info("SQLite detected - using table recreation approach")

            # Get current data
            result = db.execute(text("SELECT code, name, description, language, total_units, is_active FROM subjects"))
            rows = result.fetchall()

            # Drop old table
            db.execute(text("DROP TABLE IF EXISTS subjects"))

            # Create new table with all columns
            db.execute(text("""
                CREATE TABLE subjects (
                    id VARCHAR(36) PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    language VARCHAR(20) NOT NULL,
                    total_units INTEGER DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """))

            # Recreate indexes
            db.execute(text("CREATE INDEX idx_subjects_code ON subjects(code)"))
            db.execute(text("CREATE INDEX idx_subjects_language ON subjects(language)"))
            db.execute(text("CREATE INDEX idx_subjects_active ON subjects(is_active)"))

            # Insert data with new columns
            now = datetime.now(timezone.utc).isoformat()
            for row in rows:
                new_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO subjects (id, code, name, description, language, total_units, is_active, created_at, updated_at)
                    VALUES (:id, :code, :name, :description, :language, :total_units, :is_active, :created_at, :updated_at)
                """), {
                    'id': new_id,
                    'code': row[0],
                    'name': row[1],
                    'description': row[2],
                    'language': row[3],
                    'total_units': row[4] or 0,
                    'is_active': row[5] if row[5] is not None else True,
                    'created_at': now,
                    'updated_at': now
                })

            logger.info(f"Migrated {len(rows)} subjects with new BaseModel columns")

        else:
            # PostgreSQL - use ALTER TABLE
            now = datetime.now(timezone.utc)

            if needs_id:
                logger.info("Adding 'id' column...")
                # Add id column with default UUID
                db.execute(text("""
                    ALTER TABLE subjects
                    ADD COLUMN id VARCHAR(36)
                """))

                # Generate UUIDs for existing rows
                result = db.execute(text("SELECT code FROM subjects"))
                for row in result.fetchall():
                    new_id = str(uuid.uuid4())
                    db.execute(text("""
                        UPDATE subjects SET id = :id WHERE code = :code
                    """), {'id': new_id, 'code': row[0]})

                # Make id NOT NULL and PRIMARY KEY
                db.execute(text("ALTER TABLE subjects ALTER COLUMN id SET NOT NULL"))

                # Drop existing primary key if exists and add new one
                try:
                    db.execute(text("ALTER TABLE subjects DROP CONSTRAINT IF EXISTS subjects_pkey"))
                except Exception as e:
                    # FIX Cortez84 CRIT-ERR-001: Log exception instead of silent pass
                    logger.warning("Could not drop subjects_pkey constraint (may not exist): %s", e)
                db.execute(text("ALTER TABLE subjects ADD PRIMARY KEY (id)"))

                logger.info("Column 'id' added successfully")

            if needs_created_at:
                logger.info("Adding 'created_at' column...")
                db.execute(text(f"""
                    ALTER TABLE subjects
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT '{now.isoformat()}'
                """))
                logger.info("Column 'created_at' added successfully")

            if needs_updated_at:
                logger.info("Adding 'updated_at' column...")
                db.execute(text(f"""
                    ALTER TABLE subjects
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT '{now.isoformat()}'
                """))
                logger.info("Column 'updated_at' added successfully")

        db.commit()
        logger.info("Migration completed successfully!")

    except (OperationalError, ProgrammingError) as e:
        db.rollback()
        logger.error(f"Database error during migration: {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during migration: {e}")
        raise
    finally:
        db.close()


def rollback_migration():
    """Remove BaseModel columns from subjects table (for rollback)."""
    db = SessionLocal()
    inspector = inspect(engine)

    try:
        if not check_table_exists(inspector, 'subjects'):
            logger.info("Table 'subjects' does not exist. Nothing to rollback.")
            return

        dialect = engine.dialect.name

        if dialect == 'sqlite':
            logger.warning("SQLite rollback not implemented - would lose data")
            return

        # PostgreSQL rollback
        if check_column_exists(inspector, 'subjects', 'updated_at'):
            db.execute(text("ALTER TABLE subjects DROP COLUMN updated_at"))
            logger.info("Dropped 'updated_at' column")

        if check_column_exists(inspector, 'subjects', 'created_at'):
            db.execute(text("ALTER TABLE subjects DROP COLUMN created_at"))
            logger.info("Dropped 'created_at' column")

        if check_column_exists(inspector, 'subjects', 'id'):
            # Need to recreate primary key on 'code' first
            db.execute(text("ALTER TABLE subjects DROP CONSTRAINT IF EXISTS subjects_pkey"))
            db.execute(text("ALTER TABLE subjects ADD PRIMARY KEY (code)"))
            db.execute(text("ALTER TABLE subjects DROP COLUMN id"))
            logger.info("Dropped 'id' column and restored 'code' as primary key")

        db.commit()
        logger.info("Rollback completed successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during rollback: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        logger.info("Running rollback...")
        rollback_migration()
    else:
        logger.info("Running migration...")
        run_migration()
