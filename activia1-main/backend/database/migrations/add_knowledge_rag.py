"""
Migration: Add Knowledge Documents table for RAG

Cortez87: Implementacion de RAG para enriquecer respuestas de agentes.

Esta migracion:
1. Habilita la extension pgvector si no existe
2. Crea la tabla knowledge_documents con columna vector(384)
3. Crea indices para busqueda vectorial (IVFFlat)
4. Crea indices para filtros frecuentes

Usage:
    python -m backend.database.migrations.add_knowledge_rag

Note:
    - Requiere PostgreSQL con pgvector instalado
    - La imagen pgvector/pgvector:pg15 incluye la extension
    - Para desarrollo local sin pgvector, usa embedding_json (fallback JSON)
"""
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError

from backend.database.config import get_engine, get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_pgvector_available(engine) -> bool:
    """Check if pgvector extension is available."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
            ))
            return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Could not check pgvector availability: {e}")
        return False


def enable_pgvector_extension(engine) -> bool:
    """Enable pgvector extension if available."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector extension enabled successfully")
            return True
    except ProgrammingError as e:
        logger.warning(f"Could not enable pgvector (may not be installed): {e}")
        return False
    except Exception as e:
        logger.warning(f"Error enabling pgvector: {e}")
        return False


def create_knowledge_documents_table(engine, use_vector: bool = True):
    """
    Create the knowledge_documents table.

    Args:
        engine: SQLAlchemy engine
        use_vector: If True, create vector column for pgvector.
                   If False, only use JSONB for embeddings (SQLite compatible).
    """
    logger.info(f"Creating knowledge_documents table (use_vector={use_vector})")

    # Base table creation SQL
    base_sql = """
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        -- Identificacion unica
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        -- Contenido principal
        content TEXT NOT NULL,
        title VARCHAR(255),
        summary TEXT,

        -- Clasificacion pedagogica
        content_type VARCHAR(50) NOT NULL,
        unit VARCHAR(100),
        topic VARCHAR(100),
        difficulty VARCHAR(20),
        language VARCHAR(10) DEFAULT 'es',

        -- Embedding vectorial
        {vector_column}
        embedding_json JSONB,

        -- Trazabilidad y origen
        source_id VARCHAR(255),
        source_file VARCHAR(500),
        materia_code VARCHAR(50),

        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        deleted_at TIMESTAMP WITH TIME ZONE,

        -- Metadatos extensibles (extra_data to avoid SQLAlchemy reserved 'metadata')
        extra_data JSONB DEFAULT '{{}}'::jsonb
    );
    """

    # Vector column definition (only if pgvector available)
    vector_column = "embedding vector(384)," if use_vector else ""

    create_sql = base_sql.format(vector_column=vector_column)

    try:
        with engine.connect() as conn:
            conn.execute(text(create_sql))
            conn.commit()
            logger.info("Table knowledge_documents created successfully")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info("Table knowledge_documents already exists")
        else:
            raise


def create_indexes(engine, use_vector: bool = True):
    """Create indexes for the knowledge_documents table."""
    logger.info("Creating indexes for knowledge_documents")

    indexes = [
        # Standard indexes
        ("idx_knowledge_content_type", "CREATE INDEX IF NOT EXISTS idx_knowledge_content_type ON knowledge_documents(content_type)"),
        ("idx_knowledge_unit", "CREATE INDEX IF NOT EXISTS idx_knowledge_unit ON knowledge_documents(unit)"),
        ("idx_knowledge_materia", "CREATE INDEX IF NOT EXISTS idx_knowledge_materia ON knowledge_documents(materia_code)"),
        ("idx_knowledge_deleted", "CREATE INDEX IF NOT EXISTS idx_knowledge_deleted ON knowledge_documents(deleted_at)"),
        ("idx_knowledge_unit_type", "CREATE INDEX IF NOT EXISTS idx_knowledge_unit_type ON knowledge_documents(unit, content_type)"),
        ("idx_knowledge_materia_unit", "CREATE INDEX IF NOT EXISTS idx_knowledge_materia_unit ON knowledge_documents(materia_code, unit)"),
        ("idx_knowledge_active", "CREATE INDEX IF NOT EXISTS idx_knowledge_active ON knowledge_documents(deleted_at, content_type)"),
    ]

    # Vector index (IVFFlat) - only if pgvector available
    if use_vector:
        indexes.append((
            "idx_knowledge_embedding",
            """
            CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
            ON knowledge_documents
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
            """
        ))

    with engine.connect() as conn:
        for idx_name, idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                logger.info(f"Index {idx_name} created successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"Index {idx_name} already exists")
                else:
                    logger.warning(f"Could not create index {idx_name}: {e}")
        conn.commit()


def add_vector_column_if_missing(engine):
    """Add vector column if table exists but column is missing."""
    try:
        with engine.connect() as conn:
            # Check if vector column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'knowledge_documents'
                AND column_name = 'embedding'
            """))

            if result.fetchone() is None:
                logger.info("Adding embedding vector column to existing table")
                conn.execute(text(
                    "ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS embedding vector(384)"
                ))
                conn.commit()
                logger.info("Vector column added successfully")
            else:
                logger.info("Vector column already exists")
    except Exception as e:
        logger.warning(f"Could not add vector column: {e}")


def run_migration():
    """Run the complete migration."""
    logger.info("=" * 60)
    logger.info("Cortez87: Running RAG Knowledge Documents Migration")
    logger.info("=" * 60)

    engine = get_engine()

    # Step 1: Check if pgvector is available
    pgvector_available = check_pgvector_available(engine)
    logger.info(f"pgvector available: {pgvector_available}")

    # Step 2: Enable pgvector extension if available
    use_vector = False
    if pgvector_available:
        use_vector = enable_pgvector_extension(engine)

    # Step 3: Create table
    create_knowledge_documents_table(engine, use_vector=use_vector)

    # Step 4: Add vector column if table existed without it
    if use_vector:
        add_vector_column_if_missing(engine)

    # Step 5: Create indexes
    create_indexes(engine, use_vector=use_vector)

    logger.info("=" * 60)
    logger.info("Migration completed successfully!")
    if not use_vector:
        logger.warning(
            "NOTE: pgvector not available. Using JSONB fallback for embeddings. "
            "For production, use pgvector/pgvector:pg15 Docker image."
        )
    logger.info("=" * 60)


if __name__ == "__main__":
    run_migration()
