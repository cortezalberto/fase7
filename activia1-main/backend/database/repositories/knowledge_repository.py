"""
Knowledge Repository - Operaciones de base de datos para documentos RAG.

Cortez87: Implementacion de RAG para enriquecer respuestas de agentes.

Este repositorio gestiona el ciclo de vida completo de los documentos
de conocimiento: creacion, lectura, actualizacion, eliminacion logica,
y especialmente busqueda por similitud vectorial.

La busqueda vectorial utiliza pgvector para encontrar documentos
semanticamente relacionados con una consulta.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func, text
from sqlalchemy.orm import Session

from ..models.knowledge import KnowledgeDocumentDB
from .base import BaseRepository

logger = logging.getLogger(__name__)


class KnowledgeRepository(BaseRepository):
    """
    Repositorio para documentos de conocimiento con busqueda vectorial.

    Combina operaciones CRUD tradicionales con busqueda semantica
    por embeddings, permitiendo recuperar documentos relevantes
    basandose tanto en similitud de significado como en filtros
    estructurados (unidad, tipo, dificultad).

    La busqueda vectorial utiliza distancia coseno, donde valores
    cercanos a 1 indican alta similitud y cercanos a 0 indican
    baja similitud.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.model = KnowledgeDocumentDB

    def create(
        self,
        content: str,
        content_type: str,
        embedding: Optional[List[float]] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        unit: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        materia_code: Optional[str] = None,
        source_id: Optional[str] = None,
        source_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeDocumentDB:
        """
        Crea un nuevo documento de conocimiento.

        Args:
            content: Texto del documento
            content_type: Tipo (teoria, ejemplo, faq, consigna, ejercicio)
            embedding: Vector de 384 dimensiones (opcional)
            title: Titulo descriptivo
            summary: Resumen del contenido
            unit: Unidad tematica
            topic: Tema especifico
            difficulty: Nivel (basico, intermedio, avanzado)
            materia_code: Codigo de materia
            source_id: ID del documento original
            source_file: Ruta del archivo fuente
            metadata: Datos adicionales

        Returns:
            Instancia del documento creado
        """
        doc = KnowledgeDocumentDB(
            content=content,
            content_type=content_type,
            title=title,
            summary=summary,
            unit=unit,
            topic=topic,
            difficulty=difficulty,
            materia_code=materia_code,
            source_id=source_id,
            source_file=source_file,
            extra_data=metadata or {},
            embedding_json=embedding,  # Store in JSON field as fallback
        )

        try:
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)

            # If pgvector is available, also store in vector column
            if embedding:
                self._store_vector_embedding(doc.id, embedding)

            logger.debug(f"Created knowledge document: {doc.id}")
            return doc

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create knowledge document: {e}")
            raise

    def _store_vector_embedding(self, doc_id: UUID, embedding: List[float]) -> None:
        """
        Store embedding in pgvector column using raw SQL.

        This is separate from ORM to handle the vector type which
        requires special handling.
        """
        try:
            # Format embedding as PostgreSQL vector literal
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            self.db.execute(text(
                "UPDATE knowledge_documents "
                "SET embedding = :embedding::vector "
                "WHERE id = :doc_id"
            ), {"embedding": embedding_str, "doc_id": str(doc_id)})
            self.db.commit()

        except Exception as e:
            # pgvector may not be available (e.g., SQLite in tests)
            logger.debug(f"Could not store vector embedding (pgvector unavailable?): {e}")

    def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocumentDB]:
        """Get document by ID."""
        stmt = select(KnowledgeDocumentDB).where(
            KnowledgeDocumentDB.id == doc_id,
            KnowledgeDocumentDB.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(
        self,
        content_type: Optional[str] = None,
        unit: Optional[str] = None,
        materia_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeDocumentDB]:
        """
        Get all documents with optional filters.

        Args:
            content_type: Filter by type
            unit: Filter by unit
            materia_code: Filter by materia
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of matching documents
        """
        conditions = [KnowledgeDocumentDB.deleted_at.is_(None)]

        if content_type:
            conditions.append(KnowledgeDocumentDB.content_type == content_type)
        if unit:
            conditions.append(KnowledgeDocumentDB.unit == unit)
        if materia_code:
            conditions.append(KnowledgeDocumentDB.materia_code == materia_code)

        stmt = (
            select(KnowledgeDocumentDB)
            .where(and_(*conditions))
            .order_by(KnowledgeDocumentDB.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.execute(stmt).scalars().all())

    def search_similar(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos semanticamente similares a una consulta.

        Utiliza busqueda vectorial con distancia coseno para encontrar
        documentos cuyo significado sea similar al de la consulta.

        Args:
            query_embedding: Vector de 384 dimensiones de la consulta
            filters: Filtros opcionales:
                - unit: Unidad tematica
                - content_type: Tipo de contenido
                - difficulty: Nivel de dificultad
                - materia_code: Codigo de materia
            limit: Maximo numero de resultados
            min_similarity: Umbral minimo de similitud (0-1)

        Returns:
            Lista de documentos con su score de similitud, ordenados
            de mayor a menor relevancia
        """
        filters = filters or {}

        # First try pgvector search
        try:
            return self._search_with_pgvector(
                query_embedding, filters, limit, min_similarity
            )
        except Exception as e:
            logger.debug(f"pgvector search failed, using JSON fallback: {e}")

        # Fallback to JSON-based search (slower but works with SQLite)
        return self._search_with_json_fallback(
            query_embedding, filters, limit, min_similarity
        )

    def _search_with_pgvector(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """
        Search using pgvector's native vector operations.

        Uses cosine distance for similarity calculation.
        """
        # Build WHERE conditions
        where_clauses = ["deleted_at IS NULL"]
        params = {"limit": limit}

        if filters.get("unit"):
            where_clauses.append("unit = :unit")
            params["unit"] = filters["unit"]
        if filters.get("content_type"):
            where_clauses.append("content_type = :content_type")
            params["content_type"] = filters["content_type"]
        if filters.get("difficulty"):
            where_clauses.append("difficulty = :difficulty")
            params["difficulty"] = filters["difficulty"]
        if filters.get("materia_code"):
            where_clauses.append("materia_code = :materia_code")
            params["materia_code"] = filters["materia_code"]

        where_clause = " AND ".join(where_clauses)

        # Format embedding for PostgreSQL
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        params["query_embedding"] = embedding_str

        # Query using cosine distance
        # cosine_distance returns 0 for identical, 2 for opposite
        # We convert to similarity: 1 - (distance / 2)
        sql = text(f"""
            SELECT
                id, content, title, summary, content_type,
                unit, topic, difficulty, materia_code, extra_data,
                1 - (embedding <=> :query_embedding::vector) / 2 as similarity
            FROM knowledge_documents
            WHERE {where_clause}
                AND embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = self.db.execute(sql, params)
        rows = result.fetchall()

        documents = []
        for row in rows:
            similarity = float(row.similarity) if row.similarity else 0
            if similarity >= min_similarity:
                documents.append({
                    "id": str(row.id),
                    "content": row.content,
                    "title": row.title,
                    "summary": row.summary,
                    "content_type": row.content_type,
                    "unit": row.unit,
                    "topic": row.topic,
                    "difficulty": row.difficulty,
                    "materia_code": row.materia_code,
                    "similarity": similarity,
                    "metadata": row.extra_data or {}
                })

        return documents

    def _search_with_json_fallback(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """
        Fallback search using JSON-stored embeddings.

        Calculates cosine similarity in Python. Slower but works
        without pgvector (e.g., SQLite in tests).
        """
        # Get all documents matching filters
        conditions = [KnowledgeDocumentDB.deleted_at.is_(None)]

        if filters.get("unit"):
            conditions.append(KnowledgeDocumentDB.unit == filters["unit"])
        if filters.get("content_type"):
            conditions.append(KnowledgeDocumentDB.content_type == filters["content_type"])
        if filters.get("difficulty"):
            conditions.append(KnowledgeDocumentDB.difficulty == filters["difficulty"])
        if filters.get("materia_code"):
            conditions.append(KnowledgeDocumentDB.materia_code == filters["materia_code"])

        stmt = (
            select(KnowledgeDocumentDB)
            .where(and_(*conditions))
        )
        docs = list(self.db.execute(stmt).scalars().all())

        # Calculate similarity for each document
        results = []
        for doc in docs:
            if not doc.embedding_json:
                continue

            similarity = self._cosine_similarity(query_embedding, doc.embedding_json)
            if similarity >= min_similarity:
                results.append({
                    "id": str(doc.id),
                    "content": doc.content,
                    "title": doc.title,
                    "summary": doc.summary,
                    "content_type": doc.content_type,
                    "unit": doc.unit,
                    "topic": doc.topic,
                    "difficulty": doc.difficulty,
                    "materia_code": doc.materia_code,
                    "similarity": similarity,
                    "metadata": doc.extra_data or {}
                })

        # Sort by similarity descending and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def bulk_create(self, documents: List[Dict[str, Any]]) -> int:
        """
        Crea multiples documentos en una sola transaccion.

        Optimizado para la carga inicial de corpus academicos.

        Args:
            documents: Lista de diccionarios con:
                - content, content_type (required)
                - embedding, title, summary, unit, etc. (optional)

        Returns:
            Cantidad de documentos insertados
        """
        db_docs = []
        for doc_data in documents:
            embedding = doc_data.pop("embedding", None)
            doc = KnowledgeDocumentDB(
                embedding_json=embedding,
                **doc_data
            )
            db_docs.append(doc)

        try:
            self.db.add_all(db_docs)
            self.db.commit()

            # Store vector embeddings if available
            for i, doc in enumerate(db_docs):
                if documents[i].get("embedding"):
                    self._store_vector_embedding(doc.id, documents[i]["embedding"])

            logger.info(f"Bulk created {len(db_docs)} knowledge documents")
            return len(db_docs)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk create failed: {e}")
            raise

    def update(
        self,
        doc_id: str,
        **kwargs
    ) -> Optional[KnowledgeDocumentDB]:
        """Update document fields."""
        doc = self.get_by_id(doc_id)
        if not doc:
            return None

        embedding = kwargs.pop("embedding", None)

        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        doc.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()
            self.db.refresh(doc)

            if embedding:
                doc.embedding_json = embedding
                self._store_vector_embedding(doc.id, embedding)
                self.db.commit()

            return doc

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise

    def soft_delete(self, doc_id: str) -> bool:
        """Mark document as deleted without removing."""
        doc = self.get_by_id(doc_id)
        if not doc:
            return False

        doc.deleted_at = datetime.now(timezone.utc)

        try:
            self.db.commit()
            logger.debug(f"Soft deleted document: {doc_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to soft delete document {doc_id}: {e}")
            raise

    def count(
        self,
        content_type: Optional[str] = None,
        unit: Optional[str] = None,
        materia_code: Optional[str] = None
    ) -> int:
        """Count documents with optional filters."""
        conditions = [KnowledgeDocumentDB.deleted_at.is_(None)]

        if content_type:
            conditions.append(KnowledgeDocumentDB.content_type == content_type)
        if unit:
            conditions.append(KnowledgeDocumentDB.unit == unit)
        if materia_code:
            conditions.append(KnowledgeDocumentDB.materia_code == materia_code)

        stmt = select(func.count()).select_from(KnowledgeDocumentDB).where(and_(*conditions))
        return self.db.execute(stmt).scalar() or 0


__all__ = ["KnowledgeRepository"]
