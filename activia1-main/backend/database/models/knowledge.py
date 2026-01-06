"""
Knowledge Document Model - Documentos para RAG educativo.

Cortez87: Implementacion de RAG para enriquecer respuestas de agentes.
Cortez88: Fixed inheritance from BaseModel and UUID type for SQLite compatibility.

Este modelo representa un fragmento de contenido academico que puede ser
recuperado semanticamente para enriquecer las respuestas de los agentes
del sistema (T-IA-Cog, S-IA-X).

La busqueda vectorial utiliza pgvector con embeddings de 384 dimensiones
generados por nomic-embed-text via Ollama.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy import Column, String, Text, DateTime, Integer, Index

from .base import Base, BaseModel, JSONBCompatible, utc_now


class KnowledgeDocumentDB(Base, BaseModel):
    """
    Documento de conocimiento para RAG educativo.

    Almacena contenido academico (teoria, ejemplos, FAQs, consignas)
    junto con su representacion vectorial para busqueda semantica.

    Hereda de BaseModel para obtener:
        - id: UUID como String(36) compatible con SQLite
        - created_at, updated_at: Timestamps automaticos

    Atributos adicionales:
        content: Texto completo del documento.
        title: Titulo descriptivo (opcional).
        summary: Resumen para contextos donde el contenido es extenso.
        content_type: Clasificacion del tipo (teoria, ejemplo, faq, consigna, ejercicio).
        unit: Unidad tematica a la que pertenece.
        topic: Tema especifico dentro de la unidad.
        difficulty: Nivel de dificultad (basico, intermedio, avanzado).
        language: Idioma del contenido (default: es).
        embedding: Vector de 384 dimensiones para busqueda semantica.
        source_id: ID del documento fuente original.
        source_file: Ruta del archivo desde donde se importo.
        materia_code: Codigo de la materia asociada.
        extra_data: Informacion adicional en formato JSON.

    Note:
        El embedding se almacena como JSON array en lugar de tipo vector nativo
        para compatibilidad con SQLite en tests. La busqueda vectorial real
        se realiza mediante SQL raw con pgvector en PostgreSQL.
    """
    __tablename__ = "knowledge_documents"

    # ID heredado de BaseModel (String(36) para compatibilidad SQLite)

    # Contenido principal
    content = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)

    # Clasificacion pedagogica
    content_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tipo: teoria, ejemplo, faq, consigna, ejercicio"
    )
    unit = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Unidad tematica (ej: algoritmos_ordenamiento)"
    )
    topic = Column(
        String(100),
        nullable=True,
        comment="Tema especifico (ej: quicksort)"
    )
    difficulty = Column(
        String(20),
        nullable=True,
        comment="Nivel: basico, intermedio, avanzado"
    )
    language = Column(String(10), default="es")

    # Embedding vectorial - Almacenado como JSON para compatibilidad
    # La columna real vector(384) se crea en la migracion con pgvector
    # Este campo JSON es fallback para SQLite en tests
    embedding_json = Column(
        JSONBCompatible,
        nullable=True,
        comment="Embedding 384-dim como JSON array (fallback para SQLite)"
    )

    # Trazabilidad y origen
    source_id = Column(String(255), nullable=True, comment="ID del documento original")
    source_file = Column(String(500), nullable=True, comment="Ruta del archivo fuente")
    materia_code = Column(String(50), nullable=True, index=True)

    # Cortez88: created_at y updated_at se heredan de BaseModel
    # Solo definimos deleted_at para soft delete
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp"
    )

    # Metadatos extensibles (named extra_data to avoid SQLAlchemy reserved 'metadata')
    extra_data = Column(JSONBCompatible, default=dict)

    # Cortez88: Indices compuestos para queries frecuentes
    # Incluye indices para timestamps que se usan en ordenamiento
    __table_args__ = (
        Index('idx_knowledge_unit_type', 'unit', 'content_type'),
        Index('idx_knowledge_materia_unit', 'materia_code', 'unit'),
        Index('idx_knowledge_active', 'deleted_at', 'content_type'),
        Index('idx_knowledge_created', 'created_at'),
        Index('idx_knowledge_updated', 'updated_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeDocumentDB(id={self.id}, "
            f"title='{self.title[:30] if self.title else 'N/A'}...', "
            f"type={self.content_type})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el documento a diccionario para serialización."""
        return {
            "id": str(self.id),
            "content": self.content,
            "title": self.title,
            "summary": self.summary,
            "content_type": self.content_type,
            "unit": self.unit,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "language": self.language,
            "source_id": self.source_id,
            "source_file": self.source_file,
            "materia_code": self.materia_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.extra_data or {},
        }
