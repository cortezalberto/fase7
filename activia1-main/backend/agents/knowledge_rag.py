"""
Knowledge RAG Agent - Agente de Recuperacion Aumentada por Generacion.

Cortez87: Implementacion de RAG para enriquecer respuestas de agentes.

Este agente actua como intermediario entre las consultas de los estudiantes
y los agentes generativos del sistema (T-IA-Cog, S-IA-X). Su funcion es
enriquecer el contexto disponible para esos agentes recuperando informacion
relevante de la base de conocimiento.

El agente NO genera respuestas directamente. Solo recupera y organiza
contexto para que otros agentes lo utilicen en su generacion.

Flujo de operacion:
1. Recibir consulta del estudiante
2. Generar embedding de la consulta
3. Buscar documentos similares en pgvector
4. Evaluar si el contexto recuperado es suficientemente relevante
5. Construir texto de contexto formateado para el agente destino
"""
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from ..core.embeddings import EmbeddingProvider, get_embedding_provider
from ..core.constants import (
    RAG_CONFIDENCE_HIGH,
    RAG_CONFIDENCE_MEDIUM,
    RAG_CONFIDENCE_LOW,
    RAG_DEFAULT_MAX_DOCUMENTS,
    RAG_DEFAULT_MIN_CONFIDENCE,
    RAG_CONTENT_TRUNCATE_LENGTH,
)

# Avoid circular import - repository is injected at runtime
if TYPE_CHECKING:
    from ..database.repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)


class RAGConfidence(str, Enum):
    """
    Niveles de confianza del resultado RAG.

    La confianza indica que tan relevantes son los documentos
    recuperados para la consulta del estudiante.
    """
    HIGH = "high"       # >= 0.8: Documentos altamente relevantes
    MEDIUM = "medium"   # 0.6-0.8: Documentos relacionados
    LOW = "low"         # 0.4-0.6: Documentos tangencialmente relacionados
    NONE = "none"       # < 0.4: Sin contexto util


@dataclass
class RAGResult:
    """
    Resultado completo de una consulta RAG.

    Encapsula tanto los documentos recuperados como metadatos
    sobre la calidad de la recuperacion, permitiendo a los
    consumidores (como AIGateway) tomar decisiones informadas
    sobre si usar o descartar el contexto.
    """
    documents: List[Dict[str, Any]] = field(default_factory=list)
    confidence: RAGConfidence = RAGConfidence.NONE
    is_sufficient: bool = False
    context_text: str = ""
    query_embedding: List[float] = field(default_factory=list)

    @property
    def avg_similarity(self) -> float:
        """Calcula la similitud promedio de los documentos recuperados."""
        if not self.documents:
            return 0.0
        return sum(d.get("similarity", 0) for d in self.documents) / len(self.documents)

    @property
    def max_similarity(self) -> float:
        """Calcula la similitud maxima de los documentos recuperados."""
        if not self.documents:
            return 0.0
        return max(d.get("similarity", 0) for d in self.documents)

    @property
    def document_count(self) -> int:
        """Numero de documentos recuperados."""
        return len(self.documents)


class KnowledgeRAGAgent:
    """
    Agente de Recuperacion de Conocimiento Aumentada por Generacion.

    Este agente actua como intermediario entre las consultas de los
    estudiantes y los agentes generativos del sistema. Su funcion es
    enriquecer el contexto disponible para esos agentes recuperando
    informacion relevante de la base de conocimiento.

    El agente NO genera respuestas directamente. Solo recupera y
    organiza contexto para que otros agentes (especialmente T-IA-Cog)
    lo utilicen en su generacion.

    Umbrales de confianza:
    - HIGH (>= 0.8): Documentos muy relevantes, usar siempre
    - MEDIUM (0.6-0.8): Documentos utiles, usar si hay al menos 2
    - LOW (0.4-0.6): Documentos tangenciales, probablemente omitir
    - NONE (< 0.4): Sin contexto util, continuar sin enriquecer

    Attributes:
        embeddings: Proveedor de embeddings (OllamaEmbeddingProvider)
        knowledge_repo: Repositorio de documentos de conocimiento
        config: Configuracion del agente
        max_documents: Maximo documentos a incluir en contexto
        min_confidence: Umbral minimo de similitud
        context_template: Plantilla para formatear contexto
    """

    # Umbrales de confianza - MED-004 FIX: Use centralized constants
    CONFIDENCE_HIGH = RAG_CONFIDENCE_HIGH
    CONFIDENCE_MEDIUM = RAG_CONFIDENCE_MEDIUM
    CONFIDENCE_LOW = RAG_CONFIDENCE_LOW

    # Plantilla por defecto para el contexto
    DEFAULT_CONTEXT_TEMPLATE = """[CONTEXTO PEDAGOGICO RECUPERADO]
{documents}

[NOTA: Usa este contexto para enriquecer tu respuesta, pero sigue las reglas
pedagogicas del tutor. No copies el contenido directamente, usalo para guiar
al estudiante con informacion precisa y actualizada.]
"""

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        knowledge_repo: Optional["KnowledgeRepository"] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el agente RAG.

        Args:
            embedding_provider: Proveedor de embeddings (opcional, se crea automaticamente)
            knowledge_repo: Repositorio de conocimiento (opcional, debe inyectarse en produccion)
            config: Configuracion adicional
        """
        self.config = config or {}

        # Embedding provider - crear si no se inyecta
        if embedding_provider is not None:
            self.embeddings = embedding_provider
        else:
            self.embeddings = get_embedding_provider()

        # Repository - debe inyectarse en produccion
        self.knowledge_repo = knowledge_repo

        # Configuracion con valores por defecto - MED-004 FIX: Use centralized constants
        self.max_documents = int(self.config.get(
            "max_documents",
            RAG_DEFAULT_MAX_DOCUMENTS
        ))
        self.min_confidence = float(self.config.get(
            "min_confidence",
            RAG_DEFAULT_MIN_CONFIDENCE
        ))
        self.context_template = self.config.get(
            "context_template",
            self.DEFAULT_CONTEXT_TEMPLATE
        )

        # CRIT-002 FIX: Use lazy logging instead of f-strings
        logger.info(
            "KnowledgeRAGAgent initialized: max_docs=%d, min_confidence=%.2f",
            self.max_documents,
            self.min_confidence
        )

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGResult:
        """
        Recupera documentos relevantes para una consulta del estudiante.

        Este metodo orquesta el proceso completo de recuperacion:

        1. Generacion de embedding: Transforma la consulta textual en
           un vector de 384 dimensiones que captura su significado.

        2. Busqueda vectorial: Consulta pgvector para encontrar los
           documentos mas similares, aplicando filtros contextuales.

        3. Evaluacion de confianza: Analiza los scores de similitud
           para determinar si el contexto recuperado es util.

        4. Construccion de contexto: Formatea los documentos en un
           texto estructurado listo para ser prepuesto al prompt.

        En caso de errores, el metodo retorna un resultado vacio en
        lugar de propagar la excepcion, asegurando que el flujo
        principal no se interrumpa.

        Args:
            query: Pregunta o mensaje del estudiante
            filters: Filtros contextuales opcionales:
                - unit: Unidad tematica actual
                - materia_code: Codigo de materia
                - difficulty: Nivel del estudiante
                - content_type: Tipo de contenido preferido

        Returns:
            RAGResult con documentos, nivel de confianza, texto de
            contexto formateado, y el embedding de la query
        """
        # Verificar que tenemos repositorio
        if self.knowledge_repo is None:
            logger.warning("KnowledgeRAGAgent: No repository configured")
            return self._empty_result(query)

        # 1. Generar embedding de la consulta
        try:
            query_embedding = await self.embeddings.embed(query)
        except Exception as e:
            # CRIT-002 FIX: Use lazy logging instead of f-strings
            logger.error("Error al generar embedding: %s", e)
            return self._empty_result(query)

        # 2. Buscar documentos similares
        try:
            documents = self.knowledge_repo.search_similar(
                query_embedding=query_embedding,
                filters=filters,
                limit=self.max_documents,
                min_similarity=self.min_confidence
            )
        except Exception as e:
            # CRIT-002 FIX: Use lazy logging instead of f-strings
            logger.error("Error al buscar documentos: %s", e)
            return self._empty_result(query, query_embedding)

        # 3. Evaluar confianza
        confidence = self._evaluate_confidence(documents)
        is_sufficient = confidence in (RAGConfidence.HIGH, RAGConfidence.MEDIUM)

        # 4. Construir contexto solo si es suficiente
        context_text = self._build_context(documents) if is_sufficient else ""

        result = RAGResult(
            documents=documents,
            confidence=confidence,
            is_sufficient=is_sufficient,
            context_text=context_text,
            query_embedding=query_embedding
        )

        # CRIT-002 FIX: Use lazy logging instead of f-strings
        logger.info(
            "RAG retrieval complete: %d docs, confidence=%s, sufficient=%s",
            len(documents),
            confidence.value,
            is_sufficient
        )

        return result

    def _evaluate_confidence(self, documents: List[Dict[str, Any]]) -> RAGConfidence:
        """
        Evalua el nivel de confianza basado en las similitudes.

        La evaluacion considera tanto el promedio de similitud
        (indica calidad general) como el maximo (indica si hay
        al menos un documento muy relevante). Pondera 60% promedio
        y 40% maximo para balancear ambos factores.

        Args:
            documents: Lista de documentos con scores de similitud

        Returns:
            Nivel de confianza (HIGH, MEDIUM, LOW, NONE)
        """
        if not documents:
            return RAGConfidence.NONE

        similarities = [d.get("similarity", 0) for d in documents]
        avg_sim = sum(similarities) / len(similarities)
        max_sim = max(similarities)

        # Ponderacion: 60% promedio, 40% maximo
        score = (avg_sim * 0.6) + (max_sim * 0.4)

        if score >= self.CONFIDENCE_HIGH:
            return RAGConfidence.HIGH
        elif score >= self.CONFIDENCE_MEDIUM:
            return RAGConfidence.MEDIUM
        elif score >= self.CONFIDENCE_LOW:
            return RAGConfidence.LOW
        else:
            return RAGConfidence.NONE

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Construye el texto de contexto a partir de los documentos.

        Cada documento se formatea incluyendo su tipo, titulo (si existe),
        resumen (si existe), y contenido (truncado a 1000 caracteres para
        evitar contextos excesivamente largos).

        Args:
            documents: Lista de documentos recuperados

        Returns:
            Texto de contexto formateado listo para inyectar en el prompt
        """
        if not documents:
            return ""

        doc_texts = []
        for i, doc in enumerate(documents, 1):
            doc_text = f"--- Documento {i} ({doc.get('content_type', 'desconocido')}) ---\n"

            if doc.get("title"):
                doc_text += f"Titulo: {doc['title']}\n"

            if doc.get("summary"):
                doc_text += f"Resumen: {doc['summary']}\n"

            # Truncar contenido largo - MED-004 FIX: Use centralized constant
            content = doc.get("content", "")
            if len(content) > RAG_CONTENT_TRUNCATE_LENGTH:
                content = content[:RAG_CONTENT_TRUNCATE_LENGTH] + "..."

            doc_text += f"Contenido:\n{content}"
            doc_texts.append(doc_text)

        documents_text = "\n\n".join(doc_texts)
        return self.context_template.format(documents=documents_text)

    def _empty_result(
        self,
        query: str,
        embedding: Optional[List[float]] = None
    ) -> RAGResult:
        """Retorna un resultado vacio para casos de error o sin matches."""
        return RAGResult(
            documents=[],
            confidence=RAGConfidence.NONE,
            is_sufficient=False,
            context_text="",
            query_embedding=embedding or []
        )

    def enrich_prompt(
        self,
        original_prompt: str,
        rag_result: RAGResult
    ) -> str:
        """
        Enriquece un prompt con el contexto RAG recuperado.

        Este metodo es utilizado por AIGateway para construir el
        prompt final que se enviara al agente destino.

        Args:
            original_prompt: Prompt original del estudiante
            rag_result: Resultado de la recuperacion RAG

        Returns:
            Prompt enriquecido con contexto (si hay) o el original
        """
        if not rag_result.is_sufficient or not rag_result.context_text:
            return original_prompt

        return f"{rag_result.context_text}\n\n[PREGUNTA DEL ESTUDIANTE]\n{original_prompt}"

    async def close(self) -> None:
        """Libera recursos del agente."""
        if self.embeddings:
            await self.embeddings.close()
            logger.debug("KnowledgeRAGAgent: Embedding provider closed")


# Factory function para crear el agente con configuracion de entorno
def create_rag_agent(
    knowledge_repo: Optional["KnowledgeRepository"] = None,
    **kwargs
) -> Optional[KnowledgeRAGAgent]:
    """
    Factory para crear el agente RAG si esta habilitado.

    Verifica la variable de entorno RAG_ENABLED y solo crea
    el agente si esta activa.

    Args:
        knowledge_repo: Repositorio de conocimiento (inyectado)
        **kwargs: Configuracion adicional

    Returns:
        KnowledgeRAGAgent si RAG esta habilitado, None si no
    """
    rag_enabled = os.getenv("RAG_ENABLED", "false").lower() == "true"

    if not rag_enabled:
        logger.info("RAG is disabled (RAG_ENABLED=false)")
        return None

    return KnowledgeRAGAgent(
        knowledge_repo=knowledge_repo,
        **kwargs
    )


__all__ = [
    "KnowledgeRAGAgent",
    "RAGResult",
    "RAGConfidence",
    "create_rag_agent",
]
