"""
Migración: Agregar tablas unidades y apuntes

Cortez72: Implementación desde metodologia.md

Ejecutar: python -m backend.database.migrations.add_unidades_apuntes
"""

import logging
from sqlalchemy import text
from backend.database.config import get_db

logger = logging.getLogger(__name__)

MIGRATION_SQL = """
-- Tabla de unidades académicas
CREATE TABLE IF NOT EXISTS unidades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    materia_code VARCHAR(50) NOT NULL REFERENCES subjects(code) ON DELETE CASCADE,
    numero INTEGER NOT NULL CHECK (numero > 0),
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    objetivos_aprendizaje JSONB NOT NULL DEFAULT '[]',
    tiempo_teoria_min INTEGER DEFAULT 60,
    tiempo_practica_min INTEGER DEFAULT 120,
    orden INTEGER DEFAULT 1,
    esta_publicada BOOLEAN DEFAULT FALSE,
    requiere_unidad_anterior BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_unidad_materia ON unidades(materia_code);
CREATE INDEX IF NOT EXISTS idx_unidad_numero ON unidades(materia_code, numero);
CREATE UNIQUE INDEX IF NOT EXISTS uq_unidad_materia_numero
    ON unidades(materia_code, numero) WHERE deleted_at IS NULL;

-- Tabla de apuntes teóricos
CREATE TABLE IF NOT EXISTS apuntes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unidad_id UUID NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
    titulo VARCHAR(300) NOT NULL,
    contenido_markdown TEXT NOT NULL,
    resumen TEXT,
    recursos_externos JSONB NOT NULL DEFAULT '[]',
    tiempo_lectura_min INTEGER DEFAULT 15,
    nivel_dificultad VARCHAR(20) DEFAULT 'basico',
    orden INTEGER DEFAULT 1,
    esta_publicado BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_apuntes_unidad ON apuntes(unidad_id);
CREATE INDEX IF NOT EXISTS idx_apuntes_orden ON apuntes(unidad_id, orden);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_unidades_updated_at ON unidades;
CREATE TRIGGER update_unidades_updated_at
    BEFORE UPDATE ON unidades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_apuntes_updated_at ON apuntes;
CREATE TRIGGER update_apuntes_updated_at
    BEFORE UPDATE ON apuntes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""


def run_migration():
    """Ejecuta la migración."""
    db = next(get_db())
    try:
        db.execute(text(MIGRATION_SQL))
        db.commit()
        logger.info("Migración add_unidades_apuntes completada exitosamente")
    except Exception as e:
        db.rollback()
        logger.error("Error en migración: %s", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
