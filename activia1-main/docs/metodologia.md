# Metodología de Implementación: Sistema de Gestión de Contenido Académico

**Autor**: Claude Code (Programador Senior)
**Fecha**: 3 de enero de 2026
**Versión**: 1.1
**Objetivo**: Alimentar Materias, Unidades, Ejercicios y Apuntes de Teoría para Programación 1

---

## Flujo del Docente en el Dashboard

El sistema sigue un patrón **Maestro-Detalle multinivel** donde el docente gestiona el contenido académico de forma jerárquica:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DASHBOARD DOCENTE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PASO 1: Seleccionar/Crear Materia                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  📚 Programación 1  │  📚 Bases de Datos  │  + Nueva Materia         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ▼                                               │
│  PASO 2: Gestionar Unidades (MAESTRO)                                        │
│  ┌────────────────────────────────────────┐                                  │
│  │  Unidad 1: Variables y Tipos de Datos  │ ◄─── El docente crea unidades   │
│  │  Unidad 2: Estructuras de Control      │      con título, descripción,   │
│  │  Unidad 3: Funciones                   │      objetivos de aprendizaje   │
│  │  + Agregar Unidad                      │                                  │
│  └────────────────────────────────────────┘                                  │
│                              ▼                                               │
│  PASO 3: Agregar Contenido a Unidad (DETALLE)                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  📖 APUNTES TEÓRICOS          │  💻 EJERCICIOS                       │   │
│  │  ┌─────────────────────────┐  │  ┌─────────────────────────────────┐ │   │
│  │  │ + Nuevo Apunte          │  │  │ + Nuevo Ejercicio               │ │   │
│  │  │ ├─ Título               │  │  │ ├─ Enunciado                    │ │   │
│  │  │ ├─ Contenido Markdown   │  │  │ ├─ Código base                  │ │   │
│  │  │ ├─ 📎 Adjuntar PDFs     │  │  │ ├─ Tests automáticos            │ │   │
│  │  │ └─ Tiempo lectura       │  │  │ ├─ Hints progresivos            │ │   │
│  │  └─────────────────────────┘  │  │ └─ Rúbrica de evaluación        │ │   │
│  │                               │  └─────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo Detallado del Docente

1. **Selección de Materia**: El docente accede al Dashboard y selecciona una materia existente (ej: "Programación 1") o crea una nueva.

2. **Gestión de Unidades (Nivel Maestro)**:
   - Crea unidades temáticas con número secuencial
   - Define título, descripción y objetivos de aprendizaje
   - Establece tiempos estimados (teoría + práctica)
   - Puede reordenar, publicar o archivar unidades

3. **Contenido de Unidad (Nivel Detalle)**:
   Al seleccionar una unidad, el docente puede agregar dos tipos de contenido:

   **A. Apuntes Teóricos**:
   - Contenido en formato Markdown
   - Archivos PDF adjuntos (material complementario)
   - Recursos externos (videos, enlaces)
   - Tiempo estimado de lectura

   **B. Ejercicios Prácticos**:
   - Enunciado del problema
   - Código base/plantilla
   - Tests automáticos (entrada → salida esperada)
   - Hints progresivos (pistas graduales)
   - **Rúbrica de evaluación** con criterios y niveles

### Estructura de Rúbrica por Ejercicio

Cada ejercicio puede tener una rúbrica personalizada:

```
┌─────────────────────────────────────────────────────────────────┐
│  RÚBRICA: Ejercicio "Calculadora de Área"                       │
├─────────────────────────────────────────────────────────────────┤
│  Criterio              │ Insuficiente │ Básico │ Bueno │ Excelente │
│  ─────────────────────────────────────────────────────────────────│
│  Sintaxis correcta     │     0        │   1    │   2   │     3     │
│  Lógica del algoritmo  │     0        │   2    │   3   │     4     │
│  Manejo de errores     │     0        │   1    │   2   │     3     │
│  ─────────────────────────────────────────────────────────────────│
│  Total máximo: 10 puntos                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Relación con Modelos Existentes

El sistema aprovecha los modelos ya existentes en el backend:

| Componente | Modelo Existente | Modelo Nuevo |
|------------|------------------|--------------|
| Materias | `SubjectDB` | - |
| Unidades | - | `UnidadDB` ✨ |
| Ejercicios | `ExerciseDB` | - |
| Hints | `HintDB` | - |
| Tests | `TestDB` | - |
| Rúbricas | `ExerciseRubricDB` + `RubricLevelDB` | - |
| Apuntes | - | `ApuntesDB` ✨ |
| Archivos PDF | - | `ArchivoAdjuntoDB` ✨ |

---

## Resumen Ejecutivo

Este documento presenta la metodología paso a paso para implementar un sistema completo de gestión de contenido académico en AI-Native MVP. El análisis revela que la infraestructura backend está aproximadamente 70-80% completa (ejercicios, hints, tests, intentos, materias), pero faltan componentes críticos para una experiencia de "curso digital" completa.

### Lo que existe:
- `SubjectDB` - Materias/asignaturas
- `ExerciseDB` - Ejercicios con hints, tests, y rúbricas
- `ExerciseRubricDB` + `RubricLevelDB` - Sistema de rúbricas por ejercicio
- `ActivityDB` - Actividades del profesor
- Endpoints de training V1 y V2

### Lo que falta:
- `UnidadDB` - Modelo explícito de unidades/lecciones
- `ApuntesDB` - Contenido teórico (apuntes)
- `ArchivoAdjuntoDB` - Archivos PDF adjuntos
- Endpoints CRUD para gestión de unidades, apuntes y archivos
- Frontend de administración de contenido académico con patrón Maestro-Detalle

---

## Fase 1: Modelos de Base de Datos (Backend)

### Paso 1.1: Crear modelo UnidadDB

**Archivo**: `backend/database/models/unidad.py`

```python
"""
Unidad Académica - Modelo para unidades/lecciones de una materia.

Este modelo permite organizar el contenido académico en unidades
con metadatos completos, objetivos de aprendizaje, y relaciones
con ejercicios y apuntes.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class UnidadDB(BaseModel):
    """
    Unidad académica dentro de una materia.

    Ejemplo: Programación 1 → Unidad 1: Variables y Tipos de Datos
    """
    __tablename__ = "unidades"
    __table_args__ = (
        Index("idx_unidad_materia", "materia_code"),
        Index("idx_unidad_numero", "materia_code", "numero"),
        CheckConstraint("numero > 0", name="ck_unidad_numero_positivo"),
    )

    # Identificación
    materia_code: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("subjects.code", ondelete="CASCADE"),
        nullable=False
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)

    # Contenido
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objetivos_aprendizaje: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list
    )

    # Tiempos estimados
    tiempo_teoria_min: Mapped[int] = mapped_column(Integer, default=60)
    tiempo_practica_min: Mapped[int] = mapped_column(Integer, default=120)

    # Estado y orden
    orden: Mapped[int] = mapped_column(Integer, default=1)
    esta_publicada: Mapped[bool] = mapped_column(Boolean, default=False)
    requiere_unidad_anterior: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relaciones
    materia = relationship("SubjectDB", back_populates="unidades")
    apuntes = relationship("ApuntesDB", back_populates="unidad", cascade="all, delete-orphan")
    # Los ejercicios se relacionan via ExerciseDB.unit que mapea al numero


class ApuntesDB(BaseModel):
    """
    Contenido teórico (apuntes) asociado a una unidad.

    Almacena el material de estudio en formato Markdown con
    soporte para recursos externos y metadatos de lectura.
    """
    __tablename__ = "apuntes"
    __table_args__ = (
        Index("idx_apuntes_unidad", "unidad_id"),
        Index("idx_apuntes_orden", "unidad_id", "orden"),
    )

    # Relación con unidad
    unidad_id: Mapped[str] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"),
        nullable=False
    )

    # Contenido
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    contenido_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    resumen: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Recursos adicionales
    recursos_externos: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list
    )  # [{url, titulo, tipo: "video"|"pdf"|"link"}]

    # Metadatos de lectura
    tiempo_lectura_min: Mapped[int] = mapped_column(Integer, default=15)
    nivel_dificultad: Mapped[str] = mapped_column(
        String(20),
        default="basico"
    )  # basico, intermedio, avanzado

    # Orden y estado
    orden: Mapped[int] = mapped_column(Integer, default=1)
    esta_publicado: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relaciones
    unidad = relationship("UnidadDB", back_populates="apuntes")
```

### Paso 1.2: Actualizar SubjectDB para relación con unidades

**Archivo**: `backend/database/models/subject.py` (modificación)

```python
# Añadir en SubjectDB:
unidades = relationship("UnidadDB", back_populates="materia", cascade="all, delete-orphan")
```

### Paso 1.3: Actualizar __init__.py de models

**Archivo**: `backend/database/models/__init__.py`

```python
# Añadir exports:
from .unidad import UnidadDB, ApuntesDB
```

### Paso 1.4: Crear migración

**Archivo**: `backend/database/migrations/add_unidades_apuntes.py`

```python
"""
Migración: Agregar tablas unidades y apuntes

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
        logger.error(f"Error en migración: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
```

---

## Fase 2: Repositorios (Backend)

### Paso 2.1: Crear UnidadRepository

**Archivo**: `backend/database/repositories/unidad_repository.py`

```python
"""
Repositorio para Unidades y Apuntes académicos.

Sigue las convenciones de BaseRepository (Cortez66):
- get_by_id(): Búsqueda por ID
- get_by_*(): Búsquedas por campos específicos
- create(), update(), delete(): Operaciones CRUD
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from .base import BaseRepository
from ..models.unidad import UnidadDB, ApuntesDB


class UnidadRepository(BaseRepository):
    """Repositorio para operaciones de Unidades académicas."""

    def __init__(self, db: Session):
        super().__init__(db)

    # ==================== Unidades ====================

    def create_unidad(
        self,
        materia_code: str,
        numero: int,
        titulo: str,
        descripcion: Optional[str] = None,
        objetivos_aprendizaje: Optional[List[str]] = None,
        tiempo_teoria_min: int = 60,
        tiempo_practica_min: int = 120,
        created_by: Optional[str] = None
    ) -> UnidadDB:
        """Crea una nueva unidad académica."""
        unidad = UnidadDB(
            materia_code=materia_code,
            numero=numero,
            titulo=titulo,
            descripcion=descripcion,
            objetivos_aprendizaje=objetivos_aprendizaje or [],
            tiempo_teoria_min=tiempo_teoria_min,
            tiempo_practica_min=tiempo_practica_min,
            orden=numero,
            created_by=created_by
        )
        self.db.add(unidad)
        self.db.flush()
        return unidad

    def get_unidad_by_id(
        self,
        unidad_id: str,
        load_apuntes: bool = False
    ) -> Optional[UnidadDB]:
        """Obtiene una unidad por su ID."""
        stmt = select(UnidadDB).where(
            UnidadDB.id == unidad_id,
            UnidadDB.deleted_at.is_(None)
        )
        if load_apuntes:
            stmt = stmt.options(selectinload(UnidadDB.apuntes))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_unidades_by_materia(
        self,
        materia_code: str,
        solo_publicadas: bool = False,
        load_apuntes: bool = False
    ) -> List[UnidadDB]:
        """Obtiene todas las unidades de una materia."""
        stmt = select(UnidadDB).where(
            UnidadDB.materia_code == materia_code,
            UnidadDB.deleted_at.is_(None)
        )
        if solo_publicadas:
            stmt = stmt.where(UnidadDB.esta_publicada == True)
        if load_apuntes:
            stmt = stmt.options(selectinload(UnidadDB.apuntes))
        stmt = stmt.order_by(UnidadDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_unidad_by_numero(
        self,
        materia_code: str,
        numero: int
    ) -> Optional[UnidadDB]:
        """Obtiene una unidad por materia y número."""
        stmt = select(UnidadDB).where(
            UnidadDB.materia_code == materia_code,
            UnidadDB.numero == numero,
            UnidadDB.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def update_unidad(
        self,
        unidad_id: str,
        **kwargs
    ) -> Optional[UnidadDB]:
        """Actualiza una unidad existente."""
        unidad = self.get_unidad_by_id(unidad_id)
        if unidad:
            for key, value in kwargs.items():
                if hasattr(unidad, key):
                    setattr(unidad, key, value)
            self.db.flush()
        return unidad

    def publicar_unidad(self, unidad_id: str) -> Optional[UnidadDB]:
        """Publica una unidad (la hace visible para estudiantes)."""
        return self.update_unidad(
            unidad_id,
            esta_publicada=True,
            published_at=datetime.now(timezone.utc)
        )

    def despublicar_unidad(self, unidad_id: str) -> Optional[UnidadDB]:
        """Despublica una unidad."""
        return self.update_unidad(
            unidad_id,
            esta_publicada=False,
            published_at=None
        )

    def delete_unidad(self, unidad_id: str) -> bool:
        """Soft delete de una unidad."""
        unidad = self.get_unidad_by_id(unidad_id)
        if unidad:
            unidad.deleted_at = datetime.now(timezone.utc)
            self.db.flush()
            return True
        return False

    # ==================== Apuntes ====================

    def create_apuntes(
        self,
        unidad_id: str,
        titulo: str,
        contenido_markdown: str,
        resumen: Optional[str] = None,
        recursos_externos: Optional[List[dict]] = None,
        tiempo_lectura_min: int = 15,
        nivel_dificultad: str = "basico",
        created_by: Optional[str] = None
    ) -> ApuntesDB:
        """Crea nuevos apuntes para una unidad."""
        # Determinar orden
        max_orden = self.db.execute(
            select(func.max(ApuntesDB.orden))
            .where(ApuntesDB.unidad_id == unidad_id)
        ).scalar_one_or_none() or 0

        apuntes = ApuntesDB(
            unidad_id=unidad_id,
            titulo=titulo,
            contenido_markdown=contenido_markdown,
            resumen=resumen,
            recursos_externos=recursos_externos or [],
            tiempo_lectura_min=tiempo_lectura_min,
            nivel_dificultad=nivel_dificultad,
            orden=max_orden + 1,
            created_by=created_by
        )
        self.db.add(apuntes)
        self.db.flush()
        return apuntes

    def get_apuntes_by_id(self, apuntes_id: str) -> Optional[ApuntesDB]:
        """Obtiene apuntes por su ID."""
        stmt = select(ApuntesDB).where(
            ApuntesDB.id == apuntes_id,
            ApuntesDB.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_apuntes_by_unidad(
        self,
        unidad_id: str,
        solo_publicados: bool = False
    ) -> List[ApuntesDB]:
        """Obtiene todos los apuntes de una unidad."""
        stmt = select(ApuntesDB).where(
            ApuntesDB.unidad_id == unidad_id,
            ApuntesDB.deleted_at.is_(None)
        )
        if solo_publicados:
            stmt = stmt.where(ApuntesDB.esta_publicado == True)
        stmt = stmt.order_by(ApuntesDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    def update_apuntes(
        self,
        apuntes_id: str,
        **kwargs
    ) -> Optional[ApuntesDB]:
        """Actualiza apuntes existentes."""
        apuntes = self.get_apuntes_by_id(apuntes_id)
        if apuntes:
            for key, value in kwargs.items():
                if hasattr(apuntes, key):
                    setattr(apuntes, key, value)
            self.db.flush()
        return apuntes

    def publicar_apuntes(self, apuntes_id: str) -> Optional[ApuntesDB]:
        """Publica apuntes."""
        return self.update_apuntes(
            apuntes_id,
            esta_publicado=True,
            published_at=datetime.now(timezone.utc)
        )

    def delete_apuntes(self, apuntes_id: str) -> bool:
        """Soft delete de apuntes."""
        apuntes = self.get_apuntes_by_id(apuntes_id)
        if apuntes:
            apuntes.deleted_at = datetime.now(timezone.utc)
            self.db.flush()
            return True
        return False

    def reordenar_apuntes(
        self,
        unidad_id: str,
        orden_ids: List[str]
    ) -> None:
        """Reordena los apuntes de una unidad."""
        for idx, apuntes_id in enumerate(orden_ids, start=1):
            self.update_apuntes(apuntes_id, orden=idx)
```

### Paso 2.2: Actualizar __init__.py de repositories

**Archivo**: `backend/database/repositories/__init__.py`

```python
# Añadir:
from .unidad_repository import UnidadRepository
```

---

## Fase 3: Schemas y Endpoints (Backend API)

### Paso 3.1: Crear schemas para Unidades y Apuntes

**Archivo**: `backend/api/schemas/unidad.py`

```python
"""
Schemas Pydantic para Unidades y Apuntes académicos.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Recursos ====================

class RecursoExterno(BaseModel):
    """Recurso externo (video, PDF, link)."""
    url: str
    titulo: str
    tipo: str = Field(default="link", pattern="^(video|pdf|link)$")


# ==================== Apuntes ====================

class ApuntesCreate(BaseModel):
    """Request para crear apuntes."""
    titulo: str = Field(..., min_length=3, max_length=300)
    contenido_markdown: str = Field(..., min_length=10)
    resumen: Optional[str] = None
    recursos_externos: List[RecursoExterno] = []
    tiempo_lectura_min: int = Field(default=15, ge=1, le=180)
    nivel_dificultad: str = Field(default="basico", pattern="^(basico|intermedio|avanzado)$")


class ApuntesUpdate(BaseModel):
    """Request para actualizar apuntes."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=300)
    contenido_markdown: Optional[str] = Field(None, min_length=10)
    resumen: Optional[str] = None
    recursos_externos: Optional[List[RecursoExterno]] = None
    tiempo_lectura_min: Optional[int] = Field(None, ge=1, le=180)
    nivel_dificultad: Optional[str] = Field(None, pattern="^(basico|intermedio|avanzado)$")


class ApuntesResponse(BaseModel):
    """Response de apuntes."""
    id: str
    unidad_id: str
    titulo: str
    contenido_markdown: str
    resumen: Optional[str]
    recursos_externos: List[RecursoExterno]
    tiempo_lectura_min: int
    nivel_dificultad: str
    orden: int
    esta_publicado: bool
    created_by: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Unidades ====================

class UnidadCreate(BaseModel):
    """Request para crear una unidad."""
    materia_code: str = Field(..., min_length=2, max_length=50)
    numero: int = Field(..., ge=1)
    titulo: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    objetivos_aprendizaje: List[str] = []
    tiempo_teoria_min: int = Field(default=60, ge=0)
    tiempo_practica_min: int = Field(default=120, ge=0)


class UnidadUpdate(BaseModel):
    """Request para actualizar una unidad."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = None
    objetivos_aprendizaje: Optional[List[str]] = None
    tiempo_teoria_min: Optional[int] = Field(None, ge=0)
    tiempo_practica_min: Optional[int] = Field(None, ge=0)
    requiere_unidad_anterior: Optional[bool] = None


class UnidadResponse(BaseModel):
    """Response de unidad (sin apuntes)."""
    id: str
    materia_code: str
    numero: int
    titulo: str
    descripcion: Optional[str]
    objetivos_aprendizaje: List[str]
    tiempo_teoria_min: int
    tiempo_practica_min: int
    orden: int
    esta_publicada: bool
    requiere_unidad_anterior: bool
    created_by: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnidadConApuntesResponse(UnidadResponse):
    """Response de unidad con sus apuntes."""
    apuntes: List[ApuntesResponse] = []


class UnidadConEjerciciosResponse(UnidadResponse):
    """Response de unidad con conteo de ejercicios."""
    total_ejercicios: int = 0
    ejercicios_publicados: int = 0


# ==================== Materia Completa ====================

class MateriaConUnidadesResponse(BaseModel):
    """Response de materia con todas sus unidades."""
    code: str
    name: str
    description: Optional[str]
    language: str
    total_units: int
    is_active: bool
    unidades: List[UnidadConEjerciciosResponse] = []

    class Config:
        from_attributes = True
```

### Paso 3.2: Crear router de contenido académico

**Archivo**: `backend/api/routers/academic_content.py`

```python
"""
Router para gestión de contenido académico.

Endpoints para CRUD de materias, unidades, apuntes y ejercicios.
Uso exclusivo de profesores (rol teacher requerido).
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, require_role
from ..schemas.unidad import (
    UnidadCreate, UnidadUpdate, UnidadResponse, UnidadConApuntesResponse,
    ApuntesCreate, ApuntesUpdate, ApuntesResponse,
    MateriaConUnidadesResponse
)
from ..exceptions import (
    NotFoundError, ValidationError, AuthorizationError
)
from ...database.repositories.unidad_repository import UnidadRepository
from ...database.repositories.profile_repository import SubjectRepository
from ...database.repositories.exercise_repository import ExerciseRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/academic", tags=["Academic Content"])


# ==================== Materias ====================

@router.get("/materias", response_model=List[MateriaConUnidadesResponse])
async def listar_materias(
    solo_activas: bool = Query(True, description="Solo materias activas"),
    incluir_unidades: bool = Query(True, description="Incluir unidades"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todas las materias con sus unidades.

    Accesible por profesores y estudiantes.
    """
    subject_repo = SubjectRepository(db)
    unidad_repo = UnidadRepository(db)
    exercise_repo = ExerciseRepository(db)

    materias = subject_repo.get_all()
    if solo_activas:
        materias = [m for m in materias if m.is_active]

    result = []
    for materia in materias:
        materia_data = MateriaConUnidadesResponse(
            code=materia.code,
            name=materia.name,
            description=materia.description,
            language=materia.language,
            total_units=materia.total_units,
            is_active=materia.is_active,
            unidades=[]
        )

        if incluir_unidades:
            # Para estudiantes, solo unidades publicadas
            es_profesor = current_user.get("role") == "teacher"
            unidades = unidad_repo.get_unidades_by_materia(
                materia.code,
                solo_publicadas=not es_profesor
            )

            for unidad in unidades:
                # Contar ejercicios
                ejercicios = exercise_repo.get_by_language_and_unit(
                    materia.language,
                    unidad.numero
                )

                materia_data.unidades.append({
                    **UnidadResponse.model_validate(unidad).model_dump(),
                    "total_ejercicios": len(ejercicios),
                    "ejercicios_publicados": len([e for e in ejercicios if e.is_active])
                })

        result.append(materia_data)

    return result


@router.get("/materias/{materia_code}", response_model=MateriaConUnidadesResponse)
async def obtener_materia(
    materia_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una materia con todas sus unidades."""
    subject_repo = SubjectRepository(db)
    materia = subject_repo.get_by_code(materia_code)

    if not materia:
        raise NotFoundError("materia", materia_code)

    # Construir respuesta similar a listar_materias
    # ... (implementación similar)
    return materia


# ==================== Unidades ====================

@router.post("/unidades", response_model=UnidadResponse)
async def crear_unidad(
    data: UnidadCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Crea una nueva unidad académica.

    Solo profesores pueden crear unidades.
    """
    unidad_repo = UnidadRepository(db)
    subject_repo = SubjectRepository(db)

    # Verificar que la materia existe
    materia = subject_repo.get_by_code(data.materia_code)
    if not materia:
        raise NotFoundError("materia", data.materia_code)

    # Verificar que no existe unidad con mismo número
    existente = unidad_repo.get_unidad_by_numero(data.materia_code, data.numero)
    if existente:
        raise ValidationError(
            f"Ya existe la unidad {data.numero} en {data.materia_code}"
        )

    try:
        unidad = unidad_repo.create_unidad(
            materia_code=data.materia_code,
            numero=data.numero,
            titulo=data.titulo,
            descripcion=data.descripcion,
            objetivos_aprendizaje=data.objetivos_aprendizaje,
            tiempo_teoria_min=data.tiempo_teoria_min,
            tiempo_practica_min=data.tiempo_practica_min,
            created_by=current_user.get("user_id")
        )
        db.commit()
        logger.info(
            "Unidad creada: %s (materia=%s, numero=%d)",
            unidad.id, data.materia_code, data.numero
        )
        return unidad
    except Exception as e:
        db.rollback()
        logger.error("Error creando unidad: %s", str(e))
        raise


@router.get("/unidades/{unidad_id}", response_model=UnidadConApuntesResponse)
async def obtener_unidad(
    unidad_id: str,
    incluir_apuntes: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una unidad con sus apuntes."""
    unidad_repo = UnidadRepository(db)
    unidad = unidad_repo.get_unidad_by_id(unidad_id, load_apuntes=incluir_apuntes)

    if not unidad:
        raise NotFoundError("unidad", unidad_id)

    # Verificar acceso si no está publicada
    if not unidad.esta_publicada and current_user.get("role") != "teacher":
        raise AuthorizationError("No tiene acceso a esta unidad")

    return unidad


@router.put("/unidades/{unidad_id}", response_model=UnidadResponse)
async def actualizar_unidad(
    unidad_id: str,
    data: UnidadUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Actualiza una unidad existente."""
    unidad_repo = UnidadRepository(db)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise ValidationError("No hay datos para actualizar")

    try:
        unidad = unidad_repo.update_unidad(unidad_id, **update_data)
        if not unidad:
            raise NotFoundError("unidad", unidad_id)
        db.commit()
        return unidad
    except Exception as e:
        db.rollback()
        raise


@router.post("/unidades/{unidad_id}/publicar", response_model=UnidadResponse)
async def publicar_unidad(
    unidad_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Publica una unidad para que sea visible por estudiantes."""
    unidad_repo = UnidadRepository(db)

    try:
        unidad = unidad_repo.publicar_unidad(unidad_id)
        if not unidad:
            raise NotFoundError("unidad", unidad_id)
        db.commit()
        logger.info("Unidad publicada: %s", unidad_id)
        return unidad
    except Exception as e:
        db.rollback()
        raise


@router.delete("/unidades/{unidad_id}")
async def eliminar_unidad(
    unidad_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Elimina una unidad (soft delete)."""
    unidad_repo = UnidadRepository(db)

    try:
        if not unidad_repo.delete_unidad(unidad_id):
            raise NotFoundError("unidad", unidad_id)
        db.commit()
        return {"message": "Unidad eliminada", "id": unidad_id}
    except Exception as e:
        db.rollback()
        raise


# ==================== Apuntes ====================

@router.post("/unidades/{unidad_id}/apuntes", response_model=ApuntesResponse)
async def crear_apuntes(
    unidad_id: str,
    data: ApuntesCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Crea apuntes para una unidad."""
    unidad_repo = UnidadRepository(db)

    # Verificar que la unidad existe
    unidad = unidad_repo.get_unidad_by_id(unidad_id)
    if not unidad:
        raise NotFoundError("unidad", unidad_id)

    try:
        apuntes = unidad_repo.create_apuntes(
            unidad_id=unidad_id,
            titulo=data.titulo,
            contenido_markdown=data.contenido_markdown,
            resumen=data.resumen,
            recursos_externos=[r.model_dump() for r in data.recursos_externos],
            tiempo_lectura_min=data.tiempo_lectura_min,
            nivel_dificultad=data.nivel_dificultad,
            created_by=current_user.get("user_id")
        )
        db.commit()
        logger.info("Apuntes creados: %s (unidad=%s)", apuntes.id, unidad_id)
        return apuntes
    except Exception as e:
        db.rollback()
        raise


@router.get("/apuntes/{apuntes_id}", response_model=ApuntesResponse)
async def obtener_apuntes(
    apuntes_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene apuntes por ID."""
    unidad_repo = UnidadRepository(db)
    apuntes = unidad_repo.get_apuntes_by_id(apuntes_id)

    if not apuntes:
        raise NotFoundError("apuntes", apuntes_id)

    # Verificar acceso
    if not apuntes.esta_publicado and current_user.get("role") != "teacher":
        raise AuthorizationError("No tiene acceso a estos apuntes")

    return apuntes


@router.put("/apuntes/{apuntes_id}", response_model=ApuntesResponse)
async def actualizar_apuntes(
    apuntes_id: str,
    data: ApuntesUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Actualiza apuntes existentes."""
    unidad_repo = UnidadRepository(db)

    update_data = data.model_dump(exclude_unset=True)
    if "recursos_externos" in update_data and update_data["recursos_externos"]:
        update_data["recursos_externos"] = [
            r.model_dump() if hasattr(r, 'model_dump') else r
            for r in update_data["recursos_externos"]
        ]

    try:
        apuntes = unidad_repo.update_apuntes(apuntes_id, **update_data)
        if not apuntes:
            raise NotFoundError("apuntes", apuntes_id)
        db.commit()
        return apuntes
    except Exception as e:
        db.rollback()
        raise


@router.post("/apuntes/{apuntes_id}/publicar", response_model=ApuntesResponse)
async def publicar_apuntes(
    apuntes_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Publica apuntes."""
    unidad_repo = UnidadRepository(db)

    try:
        apuntes = unidad_repo.publicar_apuntes(apuntes_id)
        if not apuntes:
            raise NotFoundError("apuntes", apuntes_id)
        db.commit()
        return apuntes
    except Exception as e:
        db.rollback()
        raise


@router.delete("/apuntes/{apuntes_id}")
async def eliminar_apuntes(
    apuntes_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """Elimina apuntes (soft delete)."""
    unidad_repo = UnidadRepository(db)

    try:
        if not unidad_repo.delete_apuntes(apuntes_id):
            raise NotFoundError("apuntes", apuntes_id)
        db.commit()
        return {"message": "Apuntes eliminados", "id": apuntes_id}
    except Exception as e:
        db.rollback()
        raise
```

### Paso 3.3: Registrar router en main.py

**Archivo**: `backend/api/main.py` (modificación)

```python
# Añadir import:
from .routers.academic_content import router as academic_router

# Añadir en include_router:
app.include_router(academic_router)
```

---

## Fase 4: Frontend - Tipos y Servicios

### Paso 4.1: Crear tipos para contenido académico

**Archivo**: `frontEnd/src/types/domain/academic.types.ts`

```typescript
/**
 * Tipos para gestión de contenido académico.
 *
 * Incluye materias, unidades, apuntes y sus relaciones.
 */

// ==================== Recursos ====================

export interface RecursoExterno {
  url: string;
  titulo: string;
  tipo: 'video' | 'pdf' | 'link';
}

// ==================== Apuntes ====================

export interface ApuntesCreate {
  titulo: string;
  contenido_markdown: string;
  resumen?: string;
  recursos_externos?: RecursoExterno[];
  tiempo_lectura_min?: number;
  nivel_dificultad?: 'basico' | 'intermedio' | 'avanzado';
}

export interface ApuntesUpdate {
  titulo?: string;
  contenido_markdown?: string;
  resumen?: string;
  recursos_externos?: RecursoExterno[];
  tiempo_lectura_min?: number;
  nivel_dificultad?: 'basico' | 'intermedio' | 'avanzado';
}

export interface ApuntesResponse {
  id: string;
  unidad_id: string;
  titulo: string;
  contenido_markdown: string;
  resumen: string | null;
  recursos_externos: RecursoExterno[];
  tiempo_lectura_min: number;
  nivel_dificultad: string;
  orden: number;
  esta_publicado: boolean;
  created_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

// ==================== Unidades ====================

export interface UnidadCreate {
  materia_code: string;
  numero: number;
  titulo: string;
  descripcion?: string;
  objetivos_aprendizaje?: string[];
  tiempo_teoria_min?: number;
  tiempo_practica_min?: number;
}

export interface UnidadUpdate {
  titulo?: string;
  descripcion?: string;
  objetivos_aprendizaje?: string[];
  tiempo_teoria_min?: number;
  tiempo_practica_min?: number;
  requiere_unidad_anterior?: boolean;
}

export interface UnidadResponse {
  id: string;
  materia_code: string;
  numero: int;
  titulo: string;
  descripcion: string | null;
  objetivos_aprendizaje: string[];
  tiempo_teoria_min: number;
  tiempo_practica_min: number;
  orden: number;
  esta_publicada: boolean;
  requiere_unidad_anterior: boolean;
  created_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UnidadConApuntes extends UnidadResponse {
  apuntes: ApuntesResponse[];
}

export interface UnidadConEjercicios extends UnidadResponse {
  total_ejercicios: number;
  ejercicios_publicados: number;
}

// ==================== Materias ====================

export interface MateriaResponse {
  code: string;
  name: string;
  description: string | null;
  language: string;
  total_units: number;
  is_active: boolean;
}

export interface MateriaConUnidades extends MateriaResponse {
  unidades: UnidadConEjercicios[];
}
```

### Paso 4.2: Crear servicio de contenido académico

**Archivo**: `frontEnd/src/services/api/academic.service.ts`

```typescript
/**
 * Servicio para gestión de contenido académico.
 *
 * CRUD de materias, unidades y apuntes.
 */

import { BaseApiService } from './base.service';
import type {
  MateriaConUnidades,
  UnidadCreate,
  UnidadUpdate,
  UnidadResponse,
  UnidadConApuntes,
  ApuntesCreate,
  ApuntesUpdate,
  ApuntesResponse,
} from '@/types/domain/academic.types';

class AcademicService extends BaseApiService {
  constructor() {
    super('/academic');
  }

  // ==================== Materias ====================

  async getMaterias(params?: {
    solo_activas?: boolean;
    incluir_unidades?: boolean;
  }): Promise<MateriaConUnidades[]> {
    const queryParams = new URLSearchParams();
    if (params?.solo_activas !== undefined) {
      queryParams.append('solo_activas', String(params.solo_activas));
    }
    if (params?.incluir_unidades !== undefined) {
      queryParams.append('incluir_unidades', String(params.incluir_unidades));
    }
    return this.get<MateriaConUnidades[]>(`/materias?${queryParams}`);
  }

  async getMateria(code: string): Promise<MateriaConUnidades> {
    return this.get<MateriaConUnidades>(`/materias/${code}`);
  }

  // ==================== Unidades ====================

  async createUnidad(data: UnidadCreate): Promise<UnidadResponse> {
    return this.post<UnidadResponse>('/unidades', data);
  }

  async getUnidad(
    id: string,
    incluirApuntes = true
  ): Promise<UnidadConApuntes> {
    return this.get<UnidadConApuntes>(
      `/unidades/${id}?incluir_apuntes=${incluirApuntes}`
    );
  }

  async updateUnidad(
    id: string,
    data: UnidadUpdate
  ): Promise<UnidadResponse> {
    return this.put<UnidadResponse>(`/unidades/${id}`, data);
  }

  async publicarUnidad(id: string): Promise<UnidadResponse> {
    return this.post<UnidadResponse>(`/unidades/${id}/publicar`);
  }

  async deleteUnidad(id: string): Promise<void> {
    return this.delete(`/unidades/${id}`);
  }

  // ==================== Apuntes ====================

  async createApuntes(
    unidadId: string,
    data: ApuntesCreate
  ): Promise<ApuntesResponse> {
    return this.post<ApuntesResponse>(`/unidades/${unidadId}/apuntes`, data);
  }

  async getApuntes(id: string): Promise<ApuntesResponse> {
    return this.get<ApuntesResponse>(`/apuntes/${id}`);
  }

  async updateApuntes(
    id: string,
    data: ApuntesUpdate
  ): Promise<ApuntesResponse> {
    return this.put<ApuntesResponse>(`/apuntes/${id}`, data);
  }

  async publicarApuntes(id: string): Promise<ApuntesResponse> {
    return this.post<ApuntesResponse>(`/apuntes/${id}/publicar`);
  }

  async deleteApuntes(id: string): Promise<void> {
    return this.delete(`/apuntes/${id}`);
  }
}

export const academicService = new AcademicService();
```

### Paso 4.3: Actualizar exports

**Archivo**: `frontEnd/src/types/index.ts`

```typescript
// Añadir:
export * from './domain/academic.types';
```

**Archivo**: `frontEnd/src/services/api/index.ts`

```typescript
// Añadir:
export { academicService } from './academic.service';
```

---

## Fase 5: Frontend - Página de Gestión de Contenido

### Paso 5.1: Crear página ContentManagementPage

**Archivo**: `frontEnd/src/pages/ContentManagementPage.tsx`

Esta página implementa el patrón **Maestro-Detalle** con tres niveles:
1. **Nivel 1 (Maestro)**: Lista de materias
2. **Nivel 2 (Detalle)**: Unidades de la materia seleccionada
3. **Nivel 3 (Sub-detalle)**: Apuntes y ejercicios de la unidad

```typescript
/**
 * ContentManagementPage - Gestión de contenido académico
 *
 * Permite a profesores gestionar:
 * - Materias y sus metadatos
 * - Unidades con objetivos de aprendizaje
 * - Apuntes teóricos en Markdown
 * - Ejercicios asociados a cada unidad
 *
 * Patrón: Maestro-Detalle de 3 niveles
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Book, FileText, Code, Plus, Edit, Trash2,
  ChevronRight, Eye, EyeOff, Clock, Target,
  Video, File, Link as LinkIcon, Save, X
} from 'lucide-react';
import { academicService } from '@/services/api';
import type {
  MateriaConUnidades,
  UnidadConEjercicios,
  UnidadCreate,
  ApuntesCreate,
  ApuntesResponse,
} from '@/types';

// ==================== Componentes Auxiliares ====================

interface UnidadFormProps {
  materiaCode: string;
  onSave: (data: UnidadCreate) => Promise<void>;
  onCancel: () => void;
  initialData?: Partial<UnidadCreate>;
}

function UnidadForm({ materiaCode, onSave, onCancel, initialData }: UnidadFormProps) {
  const [formData, setFormData] = useState<UnidadCreate>({
    materia_code: materiaCode,
    numero: initialData?.numero || 1,
    titulo: initialData?.titulo || '',
    descripcion: initialData?.descripcion || '',
    objetivos_aprendizaje: initialData?.objetivos_aprendizaje || [],
    tiempo_teoria_min: initialData?.tiempo_teoria_min || 60,
    tiempo_practica_min: initialData?.tiempo_practica_min || 120,
  });
  const [nuevoObjetivo, setNuevoObjetivo] = useState('');
  const [saving, setSaving] = useState(false);

  const handleAddObjetivo = () => {
    if (nuevoObjetivo.trim()) {
      setFormData({
        ...formData,
        objetivos_aprendizaje: [...formData.objetivos_aprendizaje!, nuevoObjetivo.trim()]
      });
      setNuevoObjetivo('');
    }
  };

  const handleRemoveObjetivo = (index: number) => {
    setFormData({
      ...formData,
      objetivos_aprendizaje: formData.objetivos_aprendizaje!.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(formData);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-white rounded-lg border">
      <h3 className="text-lg font-semibold">
        {initialData ? 'Editar Unidad' : 'Nueva Unidad'}
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Número de Unidad</label>
          <input
            type="number"
            min="1"
            value={formData.numero}
            onChange={(e) => setFormData({ ...formData, numero: parseInt(e.target.value) })}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Título</label>
          <input
            type="text"
            value={formData.titulo}
            onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
            className="w-full p-2 border rounded"
            placeholder="Ej: Variables y Tipos de Datos"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Descripción</label>
        <textarea
          value={formData.descripcion}
          onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
          className="w-full p-2 border rounded h-20"
          placeholder="Descripción de la unidad..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            <Clock className="inline w-4 h-4 mr-1" />
            Tiempo Teoría (min)
          </label>
          <input
            type="number"
            min="0"
            value={formData.tiempo_teoria_min}
            onChange={(e) => setFormData({ ...formData, tiempo_teoria_min: parseInt(e.target.value) })}
            className="w-full p-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            <Code className="inline w-4 h-4 mr-1" />
            Tiempo Práctica (min)
          </label>
          <input
            type="number"
            min="0"
            value={formData.tiempo_practica_min}
            onChange={(e) => setFormData({ ...formData, tiempo_practica_min: parseInt(e.target.value) })}
            className="w-full p-2 border rounded"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">
          <Target className="inline w-4 h-4 mr-1" />
          Objetivos de Aprendizaje
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={nuevoObjetivo}
            onChange={(e) => setNuevoObjetivo(e.target.value)}
            className="flex-1 p-2 border rounded"
            placeholder="Agregar objetivo..."
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddObjetivo())}
          />
          <button
            type="button"
            onClick={handleAddObjetivo}
            className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <ul className="space-y-1">
          {formData.objetivos_aprendizaje?.map((obj, idx) => (
            <li key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="flex-1 text-sm">{obj}</span>
              <button
                type="button"
                onClick={() => handleRemoveObjetivo(idx)}
                className="text-red-500 hover:text-red-700"
              >
                <X className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </form>
  );
}

// ==================== Componente Principal ====================

export default function ContentManagementPage() {
  // Estado
  const [materias, setMaterias] = useState<MateriaConUnidades[]>([]);
  const [selectedMateria, setSelectedMateria] = useState<string | null>(null);
  const [selectedUnidad, setSelectedUnidad] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Formularios
  const [showUnidadForm, setShowUnidadForm] = useState(false);
  const [showApuntesForm, setShowApuntesForm] = useState(false);

  // Cargar materias
  const loadMaterias = useCallback(async () => {
    try {
      setLoading(true);
      const data = await academicService.getMaterias({
        solo_activas: false,
        incluir_unidades: true
      });
      setMaterias(data);
    } catch (err) {
      setError('Error cargando materias');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMaterias();
  }, [loadMaterias]);

  // Handlers
  const handleCreateUnidad = async (data: UnidadCreate) => {
    await academicService.createUnidad(data);
    await loadMaterias();
    setShowUnidadForm(false);
  };

  const handlePublicarUnidad = async (unidadId: string) => {
    await academicService.publicarUnidad(unidadId);
    await loadMaterias();
  };

  const handleDeleteUnidad = async (unidadId: string) => {
    if (confirm('¿Eliminar esta unidad?')) {
      await academicService.deleteUnidad(unidadId);
      await loadMaterias();
    }
  };

  // Datos derivados
  const materiaActual = materias.find(m => m.code === selectedMateria);
  const unidades = materiaActual?.unidades || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Book className="w-7 h-7 text-blue-600" />
          Gestión de Contenido Académico
        </h1>
        <p className="text-gray-600 mt-1">
          Administra materias, unidades, apuntes y ejercicios
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Panel Izquierdo: Lista de Materias */}
        <div className="col-span-3 bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Materias
          </h2>
          <div className="space-y-2">
            {materias.map((materia) => (
              <button
                key={materia.code}
                onClick={() => {
                  setSelectedMateria(materia.code);
                  setSelectedUnidad(null);
                }}
                className={`w-full text-left p-3 rounded-lg transition ${
                  selectedMateria === materia.code
                    ? 'bg-blue-50 border-blue-200 border'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="font-medium">{materia.name}</div>
                <div className="text-sm text-gray-500">
                  {materia.unidades.length} unidades • {materia.language}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Panel Central: Unidades */}
        <div className="col-span-4 bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2">
              <ChevronRight className="w-5 h-5" />
              Unidades
            </h2>
            {selectedMateria && (
              <button
                onClick={() => setShowUnidadForm(true)}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded"
              >
                <Plus className="w-5 h-5" />
              </button>
            )}
          </div>

          {showUnidadForm && selectedMateria && (
            <UnidadForm
              materiaCode={selectedMateria}
              onSave={handleCreateUnidad}
              onCancel={() => setShowUnidadForm(false)}
            />
          )}

          {!selectedMateria ? (
            <p className="text-gray-500 text-center py-8">
              Selecciona una materia
            </p>
          ) : unidades.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No hay unidades. Crea la primera.
            </p>
          ) : (
            <div className="space-y-2">
              {unidades.map((unidad) => (
                <div
                  key={unidad.id}
                  onClick={() => setSelectedUnidad(unidad.id)}
                  className={`p-3 rounded-lg cursor-pointer transition ${
                    selectedUnidad === unidad.id
                      ? 'bg-blue-50 border-blue-200 border'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium">
                      Unidad {unidad.numero}: {unidad.titulo}
                    </div>
                    <div className="flex items-center gap-1">
                      {unidad.esta_publicada ? (
                        <Eye className="w-4 h-4 text-green-500" />
                      ) : (
                        <EyeOff className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {unidad.total_ejercicios} ejercicios •
                    {unidad.tiempo_teoria_min + unidad.tiempo_practica_min} min
                  </div>
                  <div className="flex gap-2 mt-2">
                    {!unidad.esta_publicada && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePublicarUnidad(unidad.id);
                        }}
                        className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded"
                      >
                        Publicar
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteUnidad(unidad.id);
                      }}
                      className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Panel Derecho: Contenido de Unidad */}
        <div className="col-span-5 bg-white rounded-lg border p-4">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Contenido
          </h2>

          {!selectedUnidad ? (
            <p className="text-gray-500 text-center py-8">
              Selecciona una unidad para ver su contenido
            </p>
          ) : (
            <div className="space-y-4">
              {/* Sección Apuntes */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Apuntes de Teoría</h3>
                  <button
                    onClick={() => setShowApuntesForm(true)}
                    className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
                <div className="text-sm text-gray-500">
                  Los apuntes aparecerán aquí una vez creados.
                </div>
              </div>

              {/* Sección Ejercicios */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Ejercicios</h3>
                  <button className="p-1 text-blue-600 hover:bg-blue-50 rounded">
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
                <div className="text-sm text-gray-500">
                  Los ejercicios de la unidad aparecerán aquí.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

### Paso 5.2: Agregar ruta en App.tsx

**Archivo**: `frontEnd/src/App.tsx` (modificación)

```typescript
// Añadir import:
const ContentManagementPage = lazy(() => import('./pages/ContentManagementPage'));

// Añadir ruta dentro de TeacherLayout:
<Route path="content" element={<ContentManagementPage />} />
```

### Paso 5.3: Agregar enlace en TeacherLayout

**Archivo**: `frontEnd/src/components/TeacherLayout.tsx` (modificación)

```typescript
// Añadir en la navegación del sidebar:
{
  icon: Book,
  label: 'Contenido',
  path: '/teacher/content'
}
```

### Paso 5.4: Componente de Gestión de Ejercicios

El docente puede crear ejercicios completos con tests, hints y rúbricas desde la interfaz.

**Archivo**: `frontEnd/src/components/teacher/ExerciseEditor.tsx`

```tsx
/**
 * ExerciseEditor - Editor de ejercicios con tests, hints y rúbricas.
 *
 * Permite al docente crear ejercicios completos para una unidad.
 */

import { useState } from 'react';
import { Plus, Trash2, GripVertical, Save, X } from 'lucide-react';

interface TestCase {
  id: string;
  input: string;
  expected_output: string;
  is_hidden: boolean;
}

interface Hint {
  id: string;
  order: number;
  content: string;
  penalty_percentage: number; // 0-100
}

interface RubricLevel {
  level: string; // "insuficiente", "basico", "bueno", "excelente"
  score: number;
  description: string;
}

interface RubricCriterion {
  id: string;
  name: string;
  description: string;
  weight: number; // Peso relativo del criterio
  levels: RubricLevel[];
}

interface ExerciseFormData {
  title: string;
  statement: string;
  base_code: string;
  language: string;
  difficulty: 'facil' | 'medio' | 'dificil';
  time_limit_minutes: number;
  tests: TestCase[];
  hints: Hint[];
  rubric: RubricCriterion[];
}

interface ExerciseEditorProps {
  unidadId: string;
  onSave: (exercise: ExerciseFormData) => Promise<void>;
  onCancel: () => void;
  initialData?: Partial<ExerciseFormData>;
}

export function ExerciseEditor({
  unidadId,
  onSave,
  onCancel,
  initialData
}: ExerciseEditorProps) {
  const [formData, setFormData] = useState<ExerciseFormData>({
    title: initialData?.title || '',
    statement: initialData?.statement || '',
    base_code: initialData?.base_code || '# Escribe tu código aquí\n',
    language: initialData?.language || 'python',
    difficulty: initialData?.difficulty || 'medio',
    time_limit_minutes: initialData?.time_limit_minutes || 30,
    tests: initialData?.tests || [],
    hints: initialData?.hints || [],
    rubric: initialData?.rubric || [],
  });

  const [activeTab, setActiveTab] = useState<'general' | 'tests' | 'hints' | 'rubric'>('general');
  const [saving, setSaving] = useState(false);

  // ==================== Tests ====================
  const addTest = () => {
    setFormData(prev => ({
      ...prev,
      tests: [...prev.tests, {
        id: `test_${Date.now()}`,
        input: '',
        expected_output: '',
        is_hidden: false
      }]
    }));
  };

  const removeTest = (id: string) => {
    setFormData(prev => ({
      ...prev,
      tests: prev.tests.filter(t => t.id !== id)
    }));
  };

  const updateTest = (id: string, field: keyof TestCase, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      tests: prev.tests.map(t => t.id === id ? { ...t, [field]: value } : t)
    }));
  };

  // ==================== Hints ====================
  const addHint = () => {
    setFormData(prev => ({
      ...prev,
      hints: [...prev.hints, {
        id: `hint_${Date.now()}`,
        order: prev.hints.length + 1,
        content: '',
        penalty_percentage: 10
      }]
    }));
  };

  const removeHint = (id: string) => {
    setFormData(prev => ({
      ...prev,
      hints: prev.hints
        .filter(h => h.id !== id)
        .map((h, idx) => ({ ...h, order: idx + 1 }))
    }));
  };

  // ==================== Rúbrica ====================
  const addRubricCriterion = () => {
    setFormData(prev => ({
      ...prev,
      rubric: [...prev.rubric, {
        id: `crit_${Date.now()}`,
        name: '',
        description: '',
        weight: 1,
        levels: [
          { level: 'insuficiente', score: 0, description: '' },
          { level: 'basico', score: 1, description: '' },
          { level: 'bueno', score: 2, description: '' },
          { level: 'excelente', score: 3, description: '' },
        ]
      }]
    }));
  };

  const removeRubricCriterion = (id: string) => {
    setFormData(prev => ({
      ...prev,
      rubric: prev.rubric.filter(c => c.id !== id)
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(formData);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <h2 className="font-semibold">
          {initialData ? 'Editar Ejercicio' : 'Nuevo Ejercicio'}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded"
          >
            <X className="w-4 h-4" />
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {(['general', 'tests', 'hints', 'rubric'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'general' && 'General'}
            {tab === 'tests' && `Tests (${formData.tests.length})`}
            {tab === 'hints' && `Hints (${formData.hints.length})`}
            {tab === 'rubric' && `Rúbrica (${formData.rubric.length})`}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Tab: General */}
        {activeTab === 'general' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Título</label>
              <input
                type="text"
                value={formData.title}
                onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Ej: Calculadora de Área"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Enunciado</label>
              <textarea
                value={formData.statement}
                onChange={e => setFormData(prev => ({ ...prev, statement: e.target.value }))}
                placeholder="Describe el problema que el estudiante debe resolver..."
                rows={6}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Dificultad</label>
                <select
                  value={formData.difficulty}
                  onChange={e => setFormData(prev => ({
                    ...prev,
                    difficulty: e.target.value as 'facil' | 'medio' | 'dificil'
                  }))}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="facil">Fácil</option>
                  <option value="medio">Medio</option>
                  <option value="dificil">Difícil</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tiempo límite (min)</label>
                <input
                  type="number"
                  value={formData.time_limit_minutes}
                  onChange={e => setFormData(prev => ({
                    ...prev,
                    time_limit_minutes: parseInt(e.target.value) || 30
                  }))}
                  min={5}
                  max={180}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Lenguaje</label>
                <select
                  value={formData.language}
                  onChange={e => setFormData(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="java">Java</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Código Base (plantilla)</label>
              <textarea
                value={formData.base_code}
                onChange={e => setFormData(prev => ({ ...prev, base_code: e.target.value }))}
                rows={8}
                className="w-full px-3 py-2 border rounded font-mono text-sm bg-gray-900 text-green-400"
              />
            </div>
          </div>
        )}

        {/* Tab: Tests */}
        {activeTab === 'tests' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                Define los casos de prueba que validarán el código del estudiante.
              </p>
              <button
                onClick={addTest}
                className="px-3 py-1.5 bg-green-600 text-white rounded text-sm flex items-center gap-1"
              >
                <Plus className="w-4 h-4" /> Agregar Test
              </button>
            </div>

            {formData.tests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No hay tests definidos. Agrega al menos un test.
              </div>
            ) : (
              <div className="space-y-3">
                {formData.tests.map((test, idx) => (
                  <div key={test.id} className="border rounded p-3 bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">Test #{idx + 1}</span>
                      <div className="flex items-center gap-2">
                        <label className="flex items-center gap-1 text-sm">
                          <input
                            type="checkbox"
                            checked={test.is_hidden}
                            onChange={e => updateTest(test.id, 'is_hidden', e.target.checked)}
                          />
                          Oculto
                        </label>
                        <button
                          onClick={() => removeTest(test.id)}
                          className="p-1 text-red-500 hover:bg-red-100 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-gray-500">Entrada</label>
                        <textarea
                          value={test.input}
                          onChange={e => updateTest(test.id, 'input', e.target.value)}
                          placeholder="5\n3"
                          rows={2}
                          className="w-full px-2 py-1 border rounded text-sm font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Salida Esperada</label>
                        <textarea
                          value={test.expected_output}
                          onChange={e => updateTest(test.id, 'expected_output', e.target.value)}
                          placeholder="8"
                          rows={2}
                          className="w-full px-2 py-1 border rounded text-sm font-mono"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab: Hints */}
        {activeTab === 'hints' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                Define pistas progresivas. Cada pista tiene una penalización en el puntaje.
              </p>
              <button
                onClick={addHint}
                className="px-3 py-1.5 bg-yellow-600 text-white rounded text-sm flex items-center gap-1"
              >
                <Plus className="w-4 h-4" /> Agregar Hint
              </button>
            </div>

            {formData.hints.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No hay hints definidos.
              </div>
            ) : (
              <div className="space-y-3">
                {formData.hints.map((hint) => (
                  <div key={hint.id} className="border rounded p-3 bg-yellow-50 flex gap-3">
                    <div className="flex items-center text-gray-400">
                      <GripVertical className="w-4 h-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium">Hint #{hint.order}</span>
                        <span className="text-xs bg-yellow-200 px-2 py-0.5 rounded">
                          -{hint.penalty_percentage}% penalización
                        </span>
                      </div>
                      <textarea
                        value={hint.content}
                        onChange={e => {
                          setFormData(prev => ({
                            ...prev,
                            hints: prev.hints.map(h =>
                              h.id === hint.id ? { ...h, content: e.target.value } : h
                            )
                          }));
                        }}
                        placeholder="Escribe la pista aquí..."
                        rows={2}
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <input
                        type="number"
                        value={hint.penalty_percentage}
                        onChange={e => {
                          setFormData(prev => ({
                            ...prev,
                            hints: prev.hints.map(h =>
                              h.id === hint.id ? { ...h, penalty_percentage: parseInt(e.target.value) || 0 } : h
                            )
                          }));
                        }}
                        min={0}
                        max={100}
                        className="w-16 px-2 py-1 border rounded text-sm text-center"
                      />
                      <button
                        onClick={() => removeHint(hint.id)}
                        className="p-1 text-red-500 hover:bg-red-100 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab: Rúbrica */}
        {activeTab === 'rubric' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                Define los criterios de evaluación y sus niveles de logro.
              </p>
              <button
                onClick={addRubricCriterion}
                className="px-3 py-1.5 bg-purple-600 text-white rounded text-sm flex items-center gap-1"
              >
                <Plus className="w-4 h-4" /> Agregar Criterio
              </button>
            </div>

            {formData.rubric.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No hay criterios de rúbrica definidos.
              </div>
            ) : (
              <div className="space-y-4">
                {formData.rubric.map((criterion) => (
                  <div key={criterion.id} className="border rounded p-4 bg-purple-50">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 grid grid-cols-2 gap-3">
                        <input
                          type="text"
                          value={criterion.name}
                          onChange={e => {
                            setFormData(prev => ({
                              ...prev,
                              rubric: prev.rubric.map(c =>
                                c.id === criterion.id ? { ...c, name: e.target.value } : c
                              )
                            }));
                          }}
                          placeholder="Nombre del criterio"
                          className="px-2 py-1 border rounded text-sm font-medium"
                        />
                        <input
                          type="text"
                          value={criterion.description}
                          onChange={e => {
                            setFormData(prev => ({
                              ...prev,
                              rubric: prev.rubric.map(c =>
                                c.id === criterion.id ? { ...c, description: e.target.value } : c
                              )
                            }));
                          }}
                          placeholder="Descripción del criterio"
                          className="px-2 py-1 border rounded text-sm"
                        />
                      </div>
                      <button
                        onClick={() => removeRubricCriterion(criterion.id)}
                        className="ml-2 p-1 text-red-500 hover:bg-red-100 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Niveles de la rúbrica */}
                    <div className="grid grid-cols-4 gap-2">
                      {criterion.levels.map((level, levelIdx) => (
                        <div
                          key={level.level}
                          className={`p-2 rounded border ${
                            level.level === 'excelente' ? 'bg-green-100 border-green-300' :
                            level.level === 'bueno' ? 'bg-blue-100 border-blue-300' :
                            level.level === 'basico' ? 'bg-yellow-100 border-yellow-300' :
                            'bg-red-100 border-red-300'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium capitalize">{level.level}</span>
                            <input
                              type="number"
                              value={level.score}
                              onChange={e => {
                                setFormData(prev => ({
                                  ...prev,
                                  rubric: prev.rubric.map(c =>
                                    c.id === criterion.id ? {
                                      ...c,
                                      levels: c.levels.map((l, i) =>
                                        i === levelIdx ? { ...l, score: parseInt(e.target.value) || 0 } : l
                                      )
                                    } : c
                                  )
                                }));
                              }}
                              className="w-12 px-1 py-0.5 border rounded text-xs text-center"
                              min={0}
                            />
                          </div>
                          <textarea
                            value={level.description}
                            onChange={e => {
                              setFormData(prev => ({
                                ...prev,
                                rubric: prev.rubric.map(c =>
                                  c.id === criterion.id ? {
                                    ...c,
                                    levels: c.levels.map((l, i) =>
                                      i === levelIdx ? { ...l, description: e.target.value } : l
                                    )
                                  } : c
                                )
                              }));
                            }}
                            placeholder="Descripción..."
                            rows={2}
                            className="w-full px-1 py-0.5 border rounded text-xs"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Resumen de puntos */}
            {formData.rubric.length > 0 && (
              <div className="bg-gray-100 rounded p-3 text-sm">
                <strong>Puntuación máxima:</strong>{' '}
                {formData.rubric.reduce((sum, c) =>
                  sum + Math.max(...c.levels.map(l => l.score)), 0
                )} puntos
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

### Paso 5.5: Tipos TypeScript para Ejercicios con Rúbricas

**Archivo**: `frontEnd/src/types/domain/exercise.types.ts` (añadir)

```typescript
// ==================== Ejercicios Completos ====================

export interface TestCase {
  id: string;
  input: string;
  expected_output: string;
  is_hidden: boolean;
}

export interface ExerciseHint {
  id: string;
  order: number;
  content: string;
  penalty_percentage: number;
}

export interface RubricLevel {
  level: 'insuficiente' | 'basico' | 'bueno' | 'excelente';
  score: number;
  description: string;
}

export interface RubricCriterion {
  id: string;
  name: string;
  description: string;
  weight: number;
  levels: RubricLevel[];
}

export interface ExerciseCreate {
  unidad_id: string;
  title: string;
  statement: string;
  base_code: string;
  language: string;
  difficulty: 'facil' | 'medio' | 'dificil';
  time_limit_minutes: number;
  tests: Omit<TestCase, 'id'>[];
  hints: Omit<ExerciseHint, 'id'>[];
  rubric: Omit<RubricCriterion, 'id'>[];
}

export interface ExerciseWithDetails {
  id: string;
  unidad_id: string;
  title: string;
  statement: string;
  base_code: string;
  language: string;
  difficulty: string;
  time_limit_minutes: number;
  order: number;
  is_published: boolean;
  tests: TestCase[];
  hints: ExerciseHint[];
  rubric: RubricCriterion[];
  created_at: string;
  updated_at: string;
}
```

### Paso 5.6: Servicio de Ejercicios

**Archivo**: `frontEnd/src/services/api/exercises.service.ts` (añadir métodos)

```typescript
/**
 * Métodos adicionales para gestión de ejercicios por docentes.
 */

import { apiClient } from './client';
import type {
  ExerciseCreate,
  ExerciseWithDetails,
} from '@/types/domain/exercise.types';

class ExercisesService {
  private basePath = '/exercises';

  /**
   * Crea un ejercicio completo con tests, hints y rúbrica.
   */
  async createExercise(data: ExerciseCreate): Promise<ExerciseWithDetails> {
    const response = await apiClient.post<ExerciseWithDetails>(
      `${this.basePath}/full`,
      data
    );
    return response.data;
  }

  /**
   * Obtiene un ejercicio con todos sus detalles.
   */
  async getExerciseWithDetails(id: string): Promise<ExerciseWithDetails> {
    const response = await apiClient.get<ExerciseWithDetails>(
      `${this.basePath}/${id}/full`
    );
    return response.data;
  }

  /**
   * Lista ejercicios de una unidad.
   */
  async getExercisesByUnidad(unidadId: string): Promise<ExerciseWithDetails[]> {
    const response = await apiClient.get<ExerciseWithDetails[]>(
      `${this.basePath}/unidad/${unidadId}`
    );
    return response.data;
  }

  /**
   * Actualiza un ejercicio completo.
   */
  async updateExercise(
    id: string,
    data: Partial<ExerciseCreate>
  ): Promise<ExerciseWithDetails> {
    const response = await apiClient.put<ExerciseWithDetails>(
      `${this.basePath}/${id}/full`,
      data
    );
    return response.data;
  }

  /**
   * Publica un ejercicio (lo hace visible para estudiantes).
   */
  async publishExercise(id: string): Promise<ExerciseWithDetails> {
    const response = await apiClient.post<ExerciseWithDetails>(
      `${this.basePath}/${id}/publish`
    );
    return response.data;
  }

  /**
   * Elimina un ejercicio (soft delete).
   */
  async deleteExercise(id: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }
}

export const exercisesService = new ExercisesService();
```

---

## Fase 6: Datos Iniciales para Programación 1

### Paso 6.1: Script de carga de datos

**Archivo**: `backend/scripts/seed_programacion1.py`

```python
"""
Script para cargar datos iniciales de Programación 1.

Ejecutar: python -m backend.scripts.seed_programacion1
"""

import logging
from backend.database.config import get_db
from backend.database.repositories.profile_repository import SubjectRepository
from backend.database.repositories.unidad_repository import UnidadRepository

logger = logging.getLogger(__name__)

PROGRAMACION1_DATA = {
    "code": "PROG1",
    "name": "Programación 1",
    "description": "Introducción a la programación con Python",
    "language": "python",
    "total_units": 8,
    "unidades": [
        {
            "numero": 1,
            "titulo": "Variables y Tipos de Datos",
            "descripcion": "Fundamentos de almacenamiento de información en Python",
            "objetivos_aprendizaje": [
                "Comprender el concepto de variable como contenedor de datos",
                "Identificar y usar los tipos de datos primitivos (int, float, str, bool)",
                "Aplicar operadores aritméticos y de asignación",
                "Realizar conversiones entre tipos de datos"
            ],
            "tiempo_teoria_min": 45,
            "tiempo_practica_min": 90
        },
        {
            "numero": 2,
            "titulo": "Estructuras de Control: Condicionales",
            "descripcion": "Toma de decisiones en programas",
            "objetivos_aprendizaje": [
                "Comprender el flujo de control condicional",
                "Implementar estructuras if, elif, else",
                "Usar operadores de comparación y lógicos",
                "Anidar condicionales de forma efectiva"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 3,
            "titulo": "Estructuras de Control: Bucles",
            "descripcion": "Repetición y automatización de tareas",
            "objetivos_aprendizaje": [
                "Comprender el concepto de iteración",
                "Implementar bucles for y while",
                "Usar range() y enumerate()",
                "Controlar el flujo con break y continue"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 4,
            "titulo": "Funciones",
            "descripcion": "Modularización y reutilización de código",
            "objetivos_aprendizaje": [
                "Definir y llamar funciones",
                "Comprender parámetros y valores de retorno",
                "Usar argumentos posicionales y con nombre",
                "Aplicar el concepto de scope (alcance)"
            ],
            "tiempo_teoria_min": 90,
            "tiempo_practica_min": 150
        },
        {
            "numero": 5,
            "titulo": "Listas y Tuplas",
            "descripcion": "Colecciones ordenadas de datos",
            "objetivos_aprendizaje": [
                "Crear y manipular listas",
                "Aplicar métodos de listas (append, remove, sort)",
                "Entender la diferencia entre listas y tuplas",
                "Usar slicing para acceder a subconjuntos"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 6,
            "titulo": "Diccionarios y Conjuntos",
            "descripcion": "Estructuras de datos clave-valor y conjuntos",
            "objetivos_aprendizaje": [
                "Crear y manipular diccionarios",
                "Iterar sobre claves, valores y items",
                "Comprender el concepto de conjunto (set)",
                "Aplicar operaciones de conjuntos"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        },
        {
            "numero": 7,
            "titulo": "Manejo de Strings",
            "descripcion": "Procesamiento de texto",
            "objetivos_aprendizaje": [
                "Aplicar métodos de string",
                "Usar f-strings para formateo",
                "Validar y transformar texto",
                "Trabajar con expresiones regulares básicas"
            ],
            "tiempo_teoria_min": 45,
            "tiempo_practica_min": 90
        },
        {
            "numero": 8,
            "titulo": "Archivos y Excepciones",
            "descripcion": "Entrada/salida y manejo de errores",
            "objetivos_aprendizaje": [
                "Leer y escribir archivos de texto",
                "Usar context managers (with)",
                "Implementar manejo de excepciones try/except",
                "Crear excepciones personalizadas"
            ],
            "tiempo_teoria_min": 60,
            "tiempo_practica_min": 120
        }
    ]
}


def seed_programacion1():
    """Carga los datos de Programación 1."""
    db = next(get_db())
    subject_repo = SubjectRepository(db)
    unidad_repo = UnidadRepository(db)

    try:
        # Crear o actualizar materia
        materia = subject_repo.get_by_code(PROGRAMACION1_DATA["code"])
        if not materia:
            materia = subject_repo.create(
                code=PROGRAMACION1_DATA["code"],
                name=PROGRAMACION1_DATA["name"],
                description=PROGRAMACION1_DATA["description"],
                language=PROGRAMACION1_DATA["language"],
                total_units=PROGRAMACION1_DATA["total_units"]
            )
            logger.info("Materia PROG1 creada")
        else:
            logger.info("Materia PROG1 ya existe")

        # Crear unidades
        for unidad_data in PROGRAMACION1_DATA["unidades"]:
            existente = unidad_repo.get_unidad_by_numero(
                PROGRAMACION1_DATA["code"],
                unidad_data["numero"]
            )
            if not existente:
                unidad_repo.create_unidad(
                    materia_code=PROGRAMACION1_DATA["code"],
                    numero=unidad_data["numero"],
                    titulo=unidad_data["titulo"],
                    descripcion=unidad_data["descripcion"],
                    objetivos_aprendizaje=unidad_data["objetivos_aprendizaje"],
                    tiempo_teoria_min=unidad_data["tiempo_teoria_min"],
                    tiempo_practica_min=unidad_data["tiempo_practica_min"],
                    created_by="system"
                )
                logger.info(f"Unidad {unidad_data['numero']} creada")
            else:
                logger.info(f"Unidad {unidad_data['numero']} ya existe")

        db.commit()
        logger.info("Seed completado exitosamente")

    except Exception as e:
        db.rollback()
        logger.error(f"Error en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_programacion1()
```

---

## Fase 7: Subida de Archivos PDF (Rectificación de Página)

Esta fase añade la capacidad de subir archivos PDF como material de apoyo para los apuntes. Requiere cambios en backend (almacenamiento, endpoints) y frontend (componente de upload, visualizador).

### Paso 7.1: Modelo para archivos adjuntos

**Archivo**: `backend/database/models/unidad.py` (añadir)

```python
class ArchivoAdjuntoDB(BaseModel):
    """
    Archivo adjunto (PDF, imagen) asociado a apuntes o unidad.

    Almacena metadata y referencia al archivo físico en disco/S3.
    """
    __tablename__ = "archivos_adjuntos"
    __table_args__ = (
        Index("idx_archivo_apuntes", "apuntes_id"),
        Index("idx_archivo_unidad", "unidad_id"),
        Index("idx_archivo_tipo", "tipo_archivo"),
    )

    # Relaciones (uno u otro, no ambos)
    apuntes_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("apuntes.id", ondelete="CASCADE"),
        nullable=True
    )
    unidad_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"),
        nullable=True
    )

    # Metadata del archivo
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_almacenado: Mapped[str] = mapped_column(String(255), nullable=False)  # UUID.ext
    tipo_archivo: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, png, jpg
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Ruta de almacenamiento
    ruta_relativa: Mapped[str] = mapped_column(String(500), nullable=False)
    # Ejemplo: "uploads/apuntes/2026/01/abc123.pdf"

    # Descripción opcional
    descripcion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Orden de visualización
    orden: Mapped[int] = mapped_column(Integer, default=1)

    # Checksum para verificación de integridad
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relaciones
    apuntes = relationship("ApuntesDB", back_populates="archivos_adjuntos")
    unidad = relationship("UnidadDB", back_populates="archivos_adjuntos")
```

### Paso 7.2: Actualizar modelos existentes

**Archivo**: `backend/database/models/unidad.py` (modificar ApuntesDB y UnidadDB)

```python
# En ApuntesDB, añadir relación:
archivos_adjuntos = relationship(
    "ArchivoAdjuntoDB",
    back_populates="apuntes",
    cascade="all, delete-orphan"
)

# En UnidadDB, añadir relación:
archivos_adjuntos = relationship(
    "ArchivoAdjuntoDB",
    back_populates="unidad",
    cascade="all, delete-orphan"
)
```

### Paso 7.3: Servicio de almacenamiento de archivos

**Archivo**: `backend/services/file_storage.py`

```python
"""
Servicio de almacenamiento de archivos.

Soporta almacenamiento local (desarrollo) y S3 (producción).
"""

import os
import hashlib
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod

from fastapi import UploadFile

logger = logging.getLogger(__name__)


# Configuración
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
}


class StorageProvider(ABC):
    """Interfaz abstracta para proveedores de almacenamiento."""

    @abstractmethod
    async def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        path_prefix: str = ""
    ) -> str:
        """Guarda archivo y retorna ruta relativa."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Elimina archivo por ruta."""
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Retorna URL de acceso al archivo."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Verifica si el archivo existe."""
        pass


class LocalStorageProvider(StorageProvider):
    """Almacenamiento local en disco (desarrollo)."""

    def __init__(self, base_dir: str = UPLOAD_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        path_prefix: str = ""
    ) -> str:
        # Crear estructura de directorios por fecha
        date_path = datetime.now().strftime("%Y/%m")
        full_prefix = f"{path_prefix}/{date_path}" if path_prefix else date_path

        dir_path = self.base_dir / full_prefix
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / filename

        # Escribir archivo
        content = file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        relative_path = f"{full_prefix}/{filename}"
        logger.info("Archivo guardado: %s", relative_path)
        return relative_path

    async def delete(self, path: str) -> bool:
        file_path = self.base_dir / path
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("Archivo eliminado: %s", path)
                return True
            return False
        except Exception as e:
            logger.error("Error eliminando archivo: %s", e)
            return False

    async def get_url(self, path: str) -> str:
        # En desarrollo, servimos archivos via endpoint
        return f"/api/v1/files/{path}"

    async def exists(self, path: str) -> bool:
        return (self.base_dir / path).exists()


class FileStorageService:
    """Servicio principal de almacenamiento de archivos."""

    def __init__(self, provider: Optional[StorageProvider] = None):
        self.provider = provider or LocalStorageProvider()

    async def upload_file(
        self,
        file: UploadFile,
        path_prefix: str = "apuntes"
    ) -> dict:
        """
        Sube un archivo y retorna metadata.

        Args:
            file: Archivo a subir (FastAPI UploadFile)
            path_prefix: Prefijo de ruta (ej: "apuntes", "ejercicios")

        Returns:
            dict con metadata del archivo guardado

        Raises:
            ValueError: Si el archivo no es válido
        """
        # Validar tipo MIME
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Tipo de archivo no permitido: {file.content_type}. "
                f"Permitidos: {list(ALLOWED_MIME_TYPES.keys())}"
            )

        # Leer contenido para validar tamaño
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"Archivo demasiado grande: {size_mb:.1f}MB. "
                f"Máximo: {MAX_FILE_SIZE_MB}MB"
            )

        # Generar nombre único
        extension = ALLOWED_MIME_TYPES[file.content_type]
        unique_filename = f"{uuid.uuid4()}.{extension}"

        # Calcular checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Guardar archivo
        from io import BytesIO
        file_buffer = BytesIO(content)
        relative_path = await self.provider.save(
            file_buffer,
            unique_filename,
            file.content_type,
            path_prefix
        )

        return {
            "nombre_original": file.filename,
            "nombre_almacenado": unique_filename,
            "tipo_archivo": extension,
            "mime_type": file.content_type,
            "tamano_bytes": len(content),
            "ruta_relativa": relative_path,
            "checksum_sha256": checksum,
        }

    async def delete_file(self, path: str) -> bool:
        """Elimina un archivo por ruta."""
        return await self.provider.delete(path)

    async def get_file_url(self, path: str) -> str:
        """Obtiene URL de acceso al archivo."""
        return await self.provider.get_url(path)


# Singleton
_storage_service: Optional[FileStorageService] = None


def get_file_storage() -> FileStorageService:
    """Obtiene instancia del servicio de almacenamiento."""
    global _storage_service
    if _storage_service is None:
        _storage_service = FileStorageService()
    return _storage_service
```

### Paso 7.4: Endpoints para subida de archivos

**Archivo**: `backend/api/routers/files.py`

```python
"""
Router para gestión de archivos adjuntos.

Endpoints para subir, descargar y eliminar archivos PDF y otros.
"""

import logging
from pathlib import Path
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.config import get_db
from backend.database.models.unidad import ArchivoAdjuntoDB
from backend.api.deps import get_current_user, require_role
from backend.services.file_storage import get_file_storage, UPLOAD_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Archivos"])


# ==================== Schemas ====================

class ArchivoUploadResponse(BaseModel):
    """Respuesta al subir un archivo."""
    id: str
    nombre_original: str
    tipo_archivo: str
    tamano_bytes: int
    ruta_relativa: str
    url: str


class ArchivoListResponse(BaseModel):
    """Archivo en lista."""
    id: str
    nombre_original: str
    tipo_archivo: str
    tamano_bytes: int
    descripcion: Optional[str]
    orden: int
    url: str


# ==================== Endpoints ====================

@router.post(
    "/upload/apuntes/{apuntes_id}",
    response_model=ArchivoUploadResponse,
    summary="Subir archivo a apuntes"
)
async def upload_file_to_apuntes(
    apuntes_id: UUID,
    file: UploadFile = File(...),
    descripcion: Optional[str] = Query(None, max_length=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Sube un archivo PDF o imagen a un apunte específico.

    Requiere rol de profesor.
    """
    storage = get_file_storage()

    try:
        # Subir archivo
        file_metadata = await storage.upload_file(file, path_prefix="apuntes")

        # Obtener orden máximo actual
        max_orden = db.query(ArchivoAdjuntoDB).filter(
            ArchivoAdjuntoDB.apuntes_id == str(apuntes_id),
            ArchivoAdjuntoDB.deleted_at.is_(None)
        ).count()

        # Crear registro en DB
        archivo_db = ArchivoAdjuntoDB(
            apuntes_id=str(apuntes_id),
            nombre_original=file_metadata["nombre_original"],
            nombre_almacenado=file_metadata["nombre_almacenado"],
            tipo_archivo=file_metadata["tipo_archivo"],
            mime_type=file_metadata["mime_type"],
            tamano_bytes=file_metadata["tamano_bytes"],
            ruta_relativa=file_metadata["ruta_relativa"],
            checksum_sha256=file_metadata["checksum_sha256"],
            descripcion=descripcion,
            orden=max_orden + 1
        )

        db.add(archivo_db)
        db.commit()
        db.refresh(archivo_db)

        url = await storage.get_file_url(file_metadata["ruta_relativa"])

        return ArchivoUploadResponse(
            id=archivo_db.id,
            nombre_original=archivo_db.nombre_original,
            tipo_archivo=archivo_db.tipo_archivo,
            tamano_bytes=archivo_db.tamano_bytes,
            ruta_relativa=archivo_db.ruta_relativa,
            url=url
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error subiendo archivo: %s", e)
        raise HTTPException(status_code=500, detail="Error al subir archivo")


@router.post(
    "/upload/unidad/{unidad_id}",
    response_model=ArchivoUploadResponse,
    summary="Subir archivo a unidad"
)
async def upload_file_to_unidad(
    unidad_id: UUID,
    file: UploadFile = File(...),
    descripcion: Optional[str] = Query(None, max_length=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Sube un archivo PDF o imagen directamente a una unidad.

    Útil para material complementario no asociado a apuntes específicos.
    """
    storage = get_file_storage()

    try:
        file_metadata = await storage.upload_file(file, path_prefix="unidades")

        max_orden = db.query(ArchivoAdjuntoDB).filter(
            ArchivoAdjuntoDB.unidad_id == str(unidad_id),
            ArchivoAdjuntoDB.deleted_at.is_(None)
        ).count()

        archivo_db = ArchivoAdjuntoDB(
            unidad_id=str(unidad_id),
            nombre_original=file_metadata["nombre_original"],
            nombre_almacenado=file_metadata["nombre_almacenado"],
            tipo_archivo=file_metadata["tipo_archivo"],
            mime_type=file_metadata["mime_type"],
            tamano_bytes=file_metadata["tamano_bytes"],
            ruta_relativa=file_metadata["ruta_relativa"],
            checksum_sha256=file_metadata["checksum_sha256"],
            descripcion=descripcion,
            orden=max_orden + 1
        )

        db.add(archivo_db)
        db.commit()
        db.refresh(archivo_db)

        url = await storage.get_file_storage().get_file_url(file_metadata["ruta_relativa"])

        return ArchivoUploadResponse(
            id=archivo_db.id,
            nombre_original=archivo_db.nombre_original,
            tipo_archivo=archivo_db.tipo_archivo,
            tamano_bytes=archivo_db.tamano_bytes,
            ruta_relativa=archivo_db.ruta_relativa,
            url=url
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error subiendo archivo: %s", e)
        raise HTTPException(status_code=500, detail="Error al subir archivo")


@router.get(
    "/apuntes/{apuntes_id}",
    response_model=List[ArchivoListResponse],
    summary="Listar archivos de apuntes"
)
async def list_files_by_apuntes(
    apuntes_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista todos los archivos adjuntos de un apunte."""
    storage = get_file_storage()

    archivos = db.query(ArchivoAdjuntoDB).filter(
        ArchivoAdjuntoDB.apuntes_id == str(apuntes_id),
        ArchivoAdjuntoDB.deleted_at.is_(None)
    ).order_by(ArchivoAdjuntoDB.orden).all()

    result = []
    for archivo in archivos:
        url = await storage.get_file_url(archivo.ruta_relativa)
        result.append(ArchivoListResponse(
            id=archivo.id,
            nombre_original=archivo.nombre_original,
            tipo_archivo=archivo.tipo_archivo,
            tamano_bytes=archivo.tamano_bytes,
            descripcion=archivo.descripcion,
            orden=archivo.orden,
            url=url
        ))

    return result


@router.get(
    "/{path:path}",
    summary="Descargar archivo"
)
async def download_file(
    path: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Descarga un archivo por su ruta.

    La ruta incluye prefijo y fecha: apuntes/2026/01/abc123.pdf
    """
    file_path = Path(UPLOAD_DIR) / path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Verificar que está dentro del directorio de uploads (seguridad)
    try:
        file_path.resolve().relative_to(Path(UPLOAD_DIR).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.delete(
    "/{archivo_id}",
    summary="Eliminar archivo"
)
async def delete_file(
    archivo_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("teacher"))
):
    """
    Elimina un archivo adjunto (soft delete).

    También elimina el archivo físico del almacenamiento.
    """
    archivo = db.query(ArchivoAdjuntoDB).filter(
        ArchivoAdjuntoDB.id == str(archivo_id),
        ArchivoAdjuntoDB.deleted_at.is_(None)
    ).first()

    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    storage = get_file_storage()

    # Eliminar archivo físico
    await storage.delete_file(archivo.ruta_relativa)

    # Soft delete en DB
    from datetime import datetime, timezone
    archivo.deleted_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Archivo eliminado", "id": str(archivo_id)}
```

### Paso 7.5: Registrar router de archivos

**Archivo**: `backend/api/main.py` (modificar)

```python
# Añadir import:
from backend.api.routers.files import router as files_router

# Añadir registro:
app.include_router(files_router)
```

### Paso 7.6: Migración para archivos adjuntos

**Archivo**: `backend/database/migrations/add_archivos_adjuntos.py`

```python
"""
Migración: Agregar tabla archivos_adjuntos

Ejecutar: python -m backend.database.migrations.add_archivos_adjuntos
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

-- Trigger para updated_at
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
        logger.error("Error en migración: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
```

### Paso 7.7: Tipos TypeScript para archivos

**Archivo**: `frontEnd/src/types/domain/academic.types.ts` (añadir)

```typescript
// ==================== Archivos Adjuntos ====================

export interface ArchivoAdjunto {
  id: string;
  nombre_original: string;
  tipo_archivo: 'pdf' | 'png' | 'jpg' | 'gif';
  tamano_bytes: number;
  descripcion: string | null;
  orden: number;
  url: string;
}

export interface ArchivoUploadResponse {
  id: string;
  nombre_original: string;
  tipo_archivo: string;
  tamano_bytes: number;
  ruta_relativa: string;
  url: string;
}

// Actualizar ApuntesResponse para incluir archivos
export interface ApuntesConArchivos extends ApuntesResponse {
  archivos: ArchivoAdjunto[];
}
```

### Paso 7.8: Servicio de archivos en frontend

**Archivo**: `frontEnd/src/services/api/files.service.ts`

```typescript
/**
 * Servicio para gestión de archivos adjuntos (PDFs, imágenes).
 */

import { apiClient } from './client';
import type {
  ArchivoAdjunto,
  ArchivoUploadResponse
} from '@/types/domain/academic.types';

class FilesService {
  private basePath = '/files';

  /**
   * Sube un archivo PDF a un apunte.
   */
  async uploadToApuntes(
    apuntesId: string,
    file: File,
    descripcion?: string
  ): Promise<ArchivoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    let url = `${this.basePath}/upload/apuntes/${apuntesId}`;
    if (descripcion) {
      url += `?descripcion=${encodeURIComponent(descripcion)}`;
    }

    const response = await apiClient.post<ArchivoUploadResponse>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Sube un archivo PDF a una unidad.
   */
  async uploadToUnidad(
    unidadId: string,
    file: File,
    descripcion?: string
  ): Promise<ArchivoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    let url = `${this.basePath}/upload/unidad/${unidadId}`;
    if (descripcion) {
      url += `?descripcion=${encodeURIComponent(descripcion)}`;
    }

    const response = await apiClient.post<ArchivoUploadResponse>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Lista archivos de un apunte.
   */
  async getByApuntes(apuntesId: string): Promise<ArchivoAdjunto[]> {
    const response = await apiClient.get<ArchivoAdjunto[]>(
      `${this.basePath}/apuntes/${apuntesId}`
    );
    return response.data;
  }

  /**
   * Elimina un archivo.
   */
  async delete(archivoId: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${archivoId}`);
  }

  /**
   * Obtiene URL de descarga de un archivo.
   */
  getDownloadUrl(rutaRelativa: string): string {
    return `/api/v1/files/${rutaRelativa}`;
  }

  /**
   * Formatea tamaño de archivo para mostrar.
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}

export const filesService = new FilesService();
```

### Paso 7.9: Componente de subida de archivos

**Archivo**: `frontEnd/src/components/FileUploader.tsx`

```tsx
/**
 * Componente para subir archivos PDF y otros formatos permitidos.
 *
 * Soporta drag & drop y selección tradicional.
 */

import { useState, useRef, useCallback } from 'react';
import { Upload, X, FileText, Image, Loader2, Check, AlertCircle } from 'lucide-react';
import { filesService } from '@/services/api/files.service';

interface FileUploaderProps {
  /** ID del apunte o unidad destino */
  targetId: string;
  /** Tipo de destino: 'apuntes' o 'unidad' */
  targetType: 'apuntes' | 'unidad';
  /** Callback al subir archivo exitosamente */
  onUploadSuccess?: (archivo: { id: string; nombre: string; url: string }) => void;
  /** Callback en error */
  onUploadError?: (error: string) => void;
  /** Tipos MIME permitidos */
  acceptedTypes?: string[];
  /** Tamaño máximo en MB */
  maxSizeMB?: number;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export function FileUploader({
  targetId,
  targetType,
  onUploadSuccess,
  onUploadError,
  acceptedTypes = ['application/pdf', 'image/png', 'image/jpeg'],
  maxSizeMB = 50,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return `Tipo no permitido: ${file.type}. Usa PDF o imágenes.`;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSizeMB) {
      return `Archivo muy grande: ${sizeMB.toFixed(1)}MB. Máximo: ${maxSizeMB}MB`;
    }

    return null;
  }, [acceptedTypes, maxSizeMB]);

  const uploadFile = useCallback(async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadingFiles(prev => [
        ...prev,
        { file, progress: 0, status: 'error', error: validationError }
      ]);
      onUploadError?.(validationError);
      return;
    }

    // Añadir a la lista de subida
    setUploadingFiles(prev => [
      ...prev,
      { file, progress: 0, status: 'uploading' }
    ]);

    try {
      const result = targetType === 'apuntes'
        ? await filesService.uploadToApuntes(targetId, file)
        : await filesService.uploadToUnidad(targetId, file);

      // Actualizar estado a éxito
      setUploadingFiles(prev =>
        prev.map(uf =>
          uf.file === file
            ? { ...uf, progress: 100, status: 'success' }
            : uf
        )
      );

      onUploadSuccess?.({
        id: result.id,
        nombre: result.nombre_original,
        url: result.url,
      });

      // Remover de la lista después de 2 segundos
      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(uf => uf.file !== file));
      }, 2000);

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error al subir archivo';

      setUploadingFiles(prev =>
        prev.map(uf =>
          uf.file === file
            ? { ...uf, status: 'error', error: errorMsg }
            : uf
        )
      );

      onUploadError?.(errorMsg);
    }
  }, [targetId, targetType, validateFile, onUploadSuccess, onUploadError]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    files.forEach(uploadFile);
  }, [uploadFile]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(uploadFile);

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [uploadFile]);

  const removeUploadingFile = useCallback((file: File) => {
    setUploadingFiles(prev => prev.filter(uf => uf.file !== file));
  }, []);

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') {
      return <FileText className="w-5 h-5 text-red-500" />;
    }
    return <Image className="w-5 h-5 text-blue-500" />;
  };

  return (
    <div className="space-y-4">
      {/* Zona de Drop */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
          transition-colors duration-200
          ${isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
        `}
      >
        <Upload className={`w-8 h-8 mx-auto mb-2 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
        <p className="text-sm text-gray-600">
          <span className="font-medium text-blue-600">Haz clic para seleccionar</span>
          {' '}o arrastra archivos aquí
        </p>
        <p className="text-xs text-gray-400 mt-1">
          PDF, PNG, JPG hasta {maxSizeMB}MB
        </p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedTypes.join(',')}
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Lista de archivos en subida */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((uf, index) => (
            <div
              key={`${uf.file.name}-${index}`}
              className={`
                flex items-center gap-3 p-3 rounded-lg border
                ${uf.status === 'error' ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}
              `}
            >
              {getFileIcon(uf.file)}

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{uf.file.name}</p>
                <p className="text-xs text-gray-500">
                  {filesService.formatFileSize(uf.file.size)}
                </p>
              </div>

              {uf.status === 'uploading' && (
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              )}

              {uf.status === 'success' && (
                <Check className="w-5 h-5 text-green-500" />
              )}

              {uf.status === 'error' && (
                <>
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  <button
                    onClick={() => removeUploadingFile(uf.file)}
                    className="p-1 hover:bg-red-100 rounded"
                  >
                    <X className="w-4 h-4 text-red-500" />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Paso 7.10: Visor de PDF embebido

**Archivo**: `frontEnd/src/components/PDFViewer.tsx`

```tsx
/**
 * Visor de PDF embebido usando iframe.
 *
 * Para una experiencia más rica, considerar react-pdf en el futuro.
 */

import { useState } from 'react';
import { Download, ExternalLink, X, Maximize2, Minimize2 } from 'lucide-react';

interface PDFViewerProps {
  /** URL del archivo PDF */
  url: string;
  /** Nombre del archivo para descargar */
  filename?: string;
  /** Callback para cerrar el visor */
  onClose?: () => void;
  /** Altura del visor */
  height?: string;
}

export function PDFViewer({
  url,
  filename = 'documento.pdf',
  onClose,
  height = '600px',
}: PDFViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  };

  const handleOpenExternal = () => {
    window.open(url, '_blank');
  };

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-black bg-opacity-90 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-900">
          <span className="text-white font-medium truncate">{filename}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Descargar"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={handleOpenExternal}
              className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Abrir en nueva pestaña"
            >
              <ExternalLink className="w-5 h-5" />
            </button>
            <button
              onClick={() => setIsFullscreen(false)}
              className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Salir de pantalla completa"
            >
              <Minimize2 className="w-5 h-5" />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
                title="Cerrar"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* PDF iframe */}
        <iframe
          src={`${url}#toolbar=1&navpanes=1&scrollbar=1`}
          className="flex-1 w-full bg-gray-800"
          title={filename}
        />
      </div>
    );
  }

  return (
    <div className="border rounded-lg overflow-hidden bg-white">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 border-b">
        <span className="text-sm font-medium truncate">{filename}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={handleDownload}
            className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded"
            title="Descargar"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsFullscreen(true)}
            className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded"
            title="Pantalla completa"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded"
              title="Cerrar"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* PDF iframe */}
      <iframe
        src={`${url}#toolbar=0&navpanes=0`}
        style={{ height }}
        className="w-full bg-gray-100"
        title={filename}
      />
    </div>
  );
}
```

### Paso 7.11: Integrar en ContentManagementPage

**Archivo**: `frontEnd/src/pages/ContentManagementPage.tsx` (modificar sección de apuntes)

```tsx
// Añadir imports:
import { FileUploader } from '@/components/FileUploader';
import { PDFViewer } from '@/components/PDFViewer';
import { filesService } from '@/services/api/files.service';

// Añadir estado:
const [archivosApuntes, setArchivosApuntes] = useState<ArchivoAdjunto[]>([]);
const [selectedPDF, setSelectedPDF] = useState<{ url: string; nombre: string } | null>(null);

// Añadir efecto para cargar archivos cuando se selecciona un apunte:
useEffect(() => {
  if (selectedApuntes?.id) {
    filesService.getByApuntes(selectedApuntes.id)
      .then(setArchivosApuntes)
      .catch(console.error);
  }
}, [selectedApuntes?.id]);

// En la sección de apuntes, añadir después del contenido markdown:

{/* Sección de Archivos PDF */}
<div className="mt-6 pt-6 border-t">
  <h4 className="font-medium mb-3 flex items-center gap-2">
    <FileText className="w-4 h-4" />
    Archivos Adjuntos
  </h4>

  {/* Lista de archivos existentes */}
  {archivosApuntes.length > 0 && (
    <div className="space-y-2 mb-4">
      {archivosApuntes.map((archivo) => (
        <div
          key={archivo.id}
          className="flex items-center gap-3 p-2 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer"
          onClick={() => archivo.tipo_archivo === 'pdf' && setSelectedPDF({
            url: archivo.url,
            nombre: archivo.nombre_original
          })}
        >
          <FileText className="w-5 h-5 text-red-500" />
          <div className="flex-1">
            <p className="text-sm font-medium">{archivo.nombre_original}</p>
            <p className="text-xs text-gray-500">
              {filesService.formatFileSize(archivo.tamano_bytes)}
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              filesService.delete(archivo.id).then(() => {
                setArchivosApuntes(prev => prev.filter(a => a.id !== archivo.id));
              });
            }}
            className="p-1 text-red-500 hover:bg-red-100 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )}

  {/* Uploader */}
  <FileUploader
    targetId={selectedApuntes.id}
    targetType="apuntes"
    onUploadSuccess={(archivo) => {
      setArchivosApuntes(prev => [...prev, {
        id: archivo.id,
        nombre_original: archivo.nombre,
        tipo_archivo: 'pdf',
        tamano_bytes: 0,
        descripcion: null,
        orden: prev.length + 1,
        url: archivo.url,
      }]);
    }}
  />
</div>

{/* Modal de PDF */}
{selectedPDF && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div className="bg-white rounded-lg w-full max-w-4xl mx-4">
      <PDFViewer
        url={selectedPDF.url}
        filename={selectedPDF.nombre}
        onClose={() => setSelectedPDF(null)}
        height="70vh"
      />
    </div>
  </div>
)}
```

### Paso 7.12: Variables de entorno

**Archivo**: `.env.example` (añadir)

```bash
# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=50
```

---

## Resumen de Archivos a Crear/Modificar

### Backend - Crear:
1. `backend/database/models/unidad.py` - Modelos UnidadDB, ApuntesDB y ArchivoAdjuntoDB
2. `backend/database/repositories/unidad_repository.py` - Repositorio
3. `backend/database/migrations/add_unidades_apuntes.py` - Migración unidades y apuntes
4. `backend/database/migrations/add_archivos_adjuntos.py` - Migración archivos (Fase 7)
5. `backend/api/schemas/unidad.py` - Schemas Pydantic
6. `backend/api/routers/academic_content.py` - Router API contenido académico
7. `backend/api/routers/files.py` - Router API archivos (Fase 7)
8. `backend/services/file_storage.py` - Servicio almacenamiento archivos (Fase 7)
9. `backend/scripts/seed_programacion1.py` - Datos iniciales

### Backend - Modificar:
1. `backend/database/models/__init__.py` - Exports (incluir ArchivoAdjuntoDB)
2. `backend/database/models/subject.py` - Relación con unidades
3. `backend/database/repositories/__init__.py` - Exports
4. `backend/api/main.py` - Registrar routers (academic_content y files)
5. `.env.example` - Variables UPLOAD_DIR, MAX_FILE_SIZE_MB

### Frontend - Crear:
1. `frontEnd/src/types/domain/academic.types.ts` - Tipos TypeScript (incluye ArchivoAdjunto)
2. `frontEnd/src/types/domain/exercise.types.ts` - Tipos para ejercicios con rúbricas (Paso 5.5)
3. `frontEnd/src/services/api/academic.service.ts` - Servicio API contenido
4. `frontEnd/src/services/api/files.service.ts` - Servicio API archivos (Fase 7)
5. `frontEnd/src/services/api/exercises.service.ts` - Servicio CRUD ejercicios (Paso 5.6)
6. `frontEnd/src/pages/ContentManagementPage.tsx` - Página principal Maestro-Detalle
7. `frontEnd/src/components/teacher/ExerciseEditor.tsx` - Editor de ejercicios con tabs (Paso 5.4)
8. `frontEnd/src/components/FileUploader.tsx` - Componente subida archivos (Fase 7)
9. `frontEnd/src/components/PDFViewer.tsx` - Visor PDF embebido (Fase 7)

### Frontend - Modificar:
1. `frontEnd/src/types/index.ts` - Exports
2. `frontEnd/src/services/api/index.ts` - Exports (incluir filesService, exercisesService)
3. `frontEnd/src/App.tsx` - Ruta
4. `frontEnd/src/components/TeacherLayout.tsx` - Navegación

---

## Orden de Ejecución

```bash
# ==================== FASE 1-6: Contenido Académico ====================

# 1. Crear archivos backend (modelos, repositorios)
# 2. Ejecutar migración de unidades y apuntes
python -m backend.database.migrations.add_unidades_apuntes

# 3. Crear schemas y router academic_content
# 4. Reiniciar backend
python -m backend

# 5. Cargar datos iniciales
python -m backend.scripts.seed_programacion1

# 6. Crear archivos frontend (tipos, servicio, página)
# 7. Reiniciar frontend
cd frontEnd && npm run dev

# 8. Verificar en http://localhost:3000/teacher/content

# ==================== FASE 7: Subida de Archivos PDF ====================

# 9. Crear servicio file_storage.py y router files.py
# 10. Ejecutar migración de archivos adjuntos (requiere que existan tablas unidades/apuntes)
python -m backend.database.migrations.add_archivos_adjuntos

# 11. Registrar router de files en main.py
# 12. Reiniciar backend
python -m backend

# 13. Crear componentes frontend (FileUploader, PDFViewer, files.service)
# 14. Integrar en ContentManagementPage
# 15. Reiniciar frontend
cd frontEnd && npm run dev

# 16. Verificar subida de PDFs en http://localhost:3000/teacher/content
#     - Seleccionar un apunte
#     - Arrastrar o seleccionar un PDF
#     - Verificar que aparece en la lista
#     - Click para abrir el visor embebido
```

---

## Próximos Pasos (Post-implementación)

1. **Editor Markdown**: Integrar editor WYSIWYG para apuntes (react-markdown-editor)
2. **RAG Integration**: Procesar PDFs subidos con el sistema RAG de Factiblerag1.md para embeddings
3. **Ejercicios CRUD**: Crear/editar ejercicios desde la interfaz
4. **Preview de contenido**: Vista previa como lo verá el estudiante
5. **Importación masiva**: Cargar ejercicios desde JSON/CSV
6. **Versionado**: Historial de cambios en apuntes
7. **S3 Storage**: Implementar `S3StorageProvider` para producción (usando MinIO o AWS S3)

---

**Fecha de creación**: 3 de enero de 2026
**Autor**: Claude Code (Programador Senior)
**Prerrequisitos**: Factiblerag1.md, CLAUDE.md actualizados
