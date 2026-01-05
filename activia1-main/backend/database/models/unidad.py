"""
Unidad Académica - Modelo para unidades/lecciones de una materia.

Este modelo permite organizar el contenido académico en unidades
con metadatos completos, objetivos de aprendizaje, y relaciones
con ejercicios y apuntes.

Cortez72: Implementación desde metodologia.md
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel, JSONBCompatible


# FIX Cortez73 (MED-002): Inherit from both Base and BaseModel for proper SQLAlchemy registration
class UnidadDB(Base, BaseModel):
    """
    Unidad académica dentro de una materia.

    Ejemplo: Programación 1 → Unidad 1: Variables y Tipos de Datos

    Atributos:
        materia_code: Código de la materia (FK a subjects)
        numero: Número de la unidad dentro de la materia
        titulo: Título de la unidad
        descripcion: Descripción detallada
        objetivos_aprendizaje: Lista de objetivos en JSONB
        tiempo_teoria_min: Tiempo estimado de teoría en minutos
        tiempo_practica_min: Tiempo estimado de práctica en minutos
        orden: Orden de visualización
        esta_publicada: Si está visible para estudiantes
        requiere_unidad_anterior: Si necesita completar unidad previa
    """
    __tablename__ = "unidades"
    __table_args__ = (
        Index("idx_unidad_materia", "materia_code"),
        Index("idx_unidad_numero", "materia_code", "numero"),
        CheckConstraint("numero > 0", name="ck_unidad_numero_positivo"),
        # FIX Cortez73 (MED-003): Ensure unique unit number per subject
        UniqueConstraint("materia_code", "numero", name="uq_unidad_materia_numero"),
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
    # FIX Cortez79: Use JSONBCompatible for SQLite compatibility
    objetivos_aprendizaje: Mapped[List[str]] = mapped_column(
        JSONBCompatible,
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
    # FIX Cortez79: Add deleted_at for soft delete pattern
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Relaciones
    materia = relationship("SubjectDB", back_populates="unidades")
    apuntes = relationship(
        "ApuntesDB",
        back_populates="unidad",
        cascade="all, delete-orphan",
        order_by="ApuntesDB.orden"
    )
    archivos = relationship(
        "ArchivoAdjuntoDB",
        back_populates="unidad",
        cascade="all, delete-orphan",
        order_by="ArchivoAdjuntoDB.orden"
    )
    # Los ejercicios se relacionan via ExerciseDB.unit que mapea al numero


# FIX Cortez73 (MED-002): Inherit from both Base and BaseModel for proper SQLAlchemy registration
class ApuntesDB(Base, BaseModel):
    """
    Contenido teórico (apuntes) asociado a una unidad.

    Almacena el material de estudio en formato Markdown con
    soporte para recursos externos y metadatos de lectura.

    Atributos:
        unidad_id: UUID de la unidad padre
        titulo: Título del apunte
        contenido_markdown: Contenido en formato Markdown
        resumen: Resumen breve del contenido
        recursos_externos: Lista de recursos [{url, titulo, tipo}]
        tiempo_lectura_min: Tiempo estimado de lectura
        nivel_dificultad: basico, intermedio, avanzado
        orden: Orden de visualización
        esta_publicado: Si está visible para estudiantes
    """
    __tablename__ = "apuntes"
    __table_args__ = (
        Index("idx_apuntes_unidad", "unidad_id"),
        Index("idx_apuntes_orden", "unidad_id", "orden"),
        # FIX Cortez73 (MED-003): Ensure unique order per unit
        UniqueConstraint("unidad_id", "orden", name="uq_apuntes_unidad_orden"),
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
    # FIX Cortez79: Use JSONBCompatible for SQLite compatibility
    recursos_externos: Mapped[List[dict]] = mapped_column(
        JSONBCompatible,
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
    # FIX Cortez80: Add deleted_at for soft delete pattern
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Relaciones
    unidad = relationship("UnidadDB", back_populates="apuntes")
    archivos_adjuntos = relationship(
        "ArchivoAdjuntoDB",
        back_populates="apuntes",
        cascade="all, delete-orphan",
        order_by="ArchivoAdjuntoDB.orden"
    )


# FIX Cortez73 (MED-002): Inherit from both Base and BaseModel for proper SQLAlchemy registration
class ArchivoAdjuntoDB(Base, BaseModel):
    """
    Archivo adjunto (PDF, imagen) asociado a apuntes o unidad.

    Almacena metadata y referencia al archivo físico en disco/S3.

    Atributos:
        apuntes_id: UUID de los apuntes asociados (opcional)
        unidad_id: UUID de la unidad asociada (opcional)
        nombre_original: Nombre original del archivo subido
        nombre_almacenado: Nombre único en almacenamiento (UUID.ext)
        tipo_archivo: Extensión del archivo (pdf, png, jpg)
        mime_type: Tipo MIME del archivo
        tamano_bytes: Tamaño del archivo en bytes
        ruta_relativa: Ruta relativa en el almacenamiento
        descripcion: Descripción opcional del archivo
        orden: Orden de visualización
        checksum_sha256: Hash SHA256 para verificación de integridad
    """
    __tablename__ = "archivos_adjuntos"
    __table_args__ = (
        Index("idx_archivo_apuntes", "apuntes_id"),
        Index("idx_archivo_unidad", "unidad_id"),
        Index("idx_archivo_tipo", "tipo_archivo"),
        # FIX Cortez73: Ensure exactly one parent (apuntes XOR unidad)
        CheckConstraint(
            "(apuntes_id IS NOT NULL AND unidad_id IS NULL) OR "
            "(apuntes_id IS NULL AND unidad_id IS NOT NULL)",
            name="ck_archivo_has_exactly_one_parent"
        ),
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

    # FIX Cortez80: Add deleted_at for soft delete pattern
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Relaciones
    apuntes = relationship("ApuntesDB", back_populates="archivos_adjuntos")
    unidad = relationship("UnidadDB", back_populates="archivos")
