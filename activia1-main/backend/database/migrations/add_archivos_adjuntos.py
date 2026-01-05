"""
Migración: Agregar tabla archivos_adjuntos

Cortez72: Implementación desde metodologia.md

Ejecutar: python -m backend.database.migrations.add_archivos_adjuntos

NOTA: Ejecutar DESPUÉS de add_unidades_apuntes.py ya que depende de esas tablas.
"""

import logging
from sqlalchemy import text
from backend.database.config import get_db

logger = logging.getLogger(__name__)

MIGRATION_SQL = """
-- Tabla de archivos adjuntos
CREATE TABLE IF NOT EXISTS archivos_adjuntos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apuntes_id UUID REFERENCES apuntes(id) ON DELETE CASCADE,
    unidad_id UUID REFERENCES unidades(id) ON DELETE CASCADE,
    nombre_original VARCHAR(255) NOT NULL,
    nombre_almacenado VARCHAR(255) NOT NULL,
    tipo_archivo VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamano_bytes INTEGER NOT NULL,
    ruta_relativa VARCHAR(500) NOT NULL,
    descripcion VARCHAR(500),
    orden INTEGER DEFAULT 1,
    checksum_sha256 VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    -- Constraint: debe pertenecer a apuntes O unidad, no ambos ni ninguno
    CONSTRAINT ck_archivo_pertenencia CHECK (
        (apuntes_id IS NOT NULL AND unidad_id IS NULL) OR
        (apuntes_id IS NULL AND unidad_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_archivo_apuntes ON archivos_adjuntos(apuntes_id);
CREATE INDEX IF NOT EXISTS idx_archivo_unidad ON archivos_adjuntos(unidad_id);
CREATE INDEX IF NOT EXISTS idx_archivo_tipo ON archivos_adjuntos(tipo_archivo);

-- Trigger para updated_at (función ya existe de migración anterior)
DROP TRIGGER IF EXISTS update_archivos_adjuntos_updated_at ON archivos_adjuntos;
CREATE TRIGGER update_archivos_adjuntos_updated_at
    BEFORE UPDATE ON archivos_adjuntos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""


def run_migration():
    """Ejecuta la migración."""
    db = next(get_db())
    try:
        db.execute(text(MIGRATION_SQL))
        db.commit()
        logger.info("Migración add_archivos_adjuntos completada")
    except Exception as e:
        db.rollback()
        logger.error("Error en migración: %s", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
