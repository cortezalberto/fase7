"""
Database Initialization Script - Auto-seed for Development

Este script se ejecuta automáticamente al iniciar la aplicación
y carga datos iniciales si la base de datos está vacía.

Ejecuta:
1. Creación de tablas (si no existen)
2. Seed de ejercicios (subjects, exercises, hints, tests, rubrics)

Uso:
    # Manual (desde dentro del container)
    python -m backend.scripts.init_db

    # Automático (llamado desde backend.api.main.py en lifespan)
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.config import engine, SessionLocal
from backend.database.base import Base
# FIX Cortez25: Use UserDB from database.models to avoid duplicate table definition
from backend.database.models import UserDB as User, ExerciseDB, SubjectDB

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def init_db():
    """Create all tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    # FIX Cortez76: Removed emoji to avoid cp1252 encoding error on Windows
    logger.info("Tables created successfully!")


def seed_exercises_if_empty():
    """
    Carga ejercicios desde JSON a PostgreSQL si la BD está vacía.

    Verifica si hay ejercicios en la BD:
    - Si hay ejercicios: Skip seed (ya fue inicializado)
    - Si NO hay ejercicios: Ejecutar seed completo
    """
    try:
        # Conectar a BD
        db = SessionLocal()

        try:
            # Verificar si ya hay datos
            exercise_count = db.query(ExerciseDB).count()
            subject_count = db.query(SubjectDB).count()

            if exercise_count > 0 or subject_count > 0:
                logger.info("=" * 80)
                # FIX Cortez54: Removed emoji to avoid cp1252 encoding error on Windows
                logger.info("DATABASE ALREADY SEEDED - Skipping initialization")
                logger.info("   Found: %d subjects, %d exercises", subject_count, exercise_count)
                logger.info("=" * 80)
                return True

            logger.info("=" * 80)
            # FIX Cortez54: Removed emoji to avoid cp1252 encoding error on Windows
            logger.info("DATABASE IS EMPTY - Starting seed process")
            logger.info("=" * 80)

        finally:
            db.close()

        # Base de datos vacía, ejecutar seed
        # FIX Cortez76: Removed emoji to avoid cp1252 encoding error on Windows
        logger.info("Running seed_exercises script...")

        from backend.scripts.seed_exercises import main as seed_exercises_main

        seed_exercises_main()

        logger.info("Seed completed successfully")

        # Verificar resultados
        db = SessionLocal()
        try:
            subject_count = db.query(SubjectDB).count()
            exercise_count = db.query(ExerciseDB).count()

            logger.info("=" * 80)
            logger.info("SEED RESULTS:")
            logger.info("   Subjects: %d", subject_count)
            logger.info("   Exercises: %d", exercise_count)
            logger.info("=" * 80)

        finally:
            db.close()

        return True

    except Exception as e:
        logger.error("Error during seed: %s", e, exc_info=True)
        return False


if __name__ == "__main__":
    # Crear tablas
    init_db()

    # Seed automático
    success = seed_exercises_if_empty()

    if not success:
        # FIX Cortez76: Removed emoji to avoid cp1252 encoding error on Windows
        logger.error("Database initialization FAILED")
        sys.exit(1)

    logger.info("Database initialization SUCCESSFUL")
    sys.exit(0)
