# Propuesta Tecnica de Implementacion: Arquitectura Multi-Agente Active-IA

## Indice

1. [Vision Ejecutiva](#1-vision-ejecutiva)
2. [Analisis del Estado Actual](#2-analisis-del-estado-actual)
3. [Arquitectura Propuesta](#3-arquitectura-propuesta)
4. [Especificacion de Agentes](#4-especificacion-de-agentes)
5. [Flujo de Procesamiento](#5-flujo-de-procesamiento)
6. [Implementacion Tecnica](#6-implementacion-tecnica)
7. [Integracion con Componentes Existentes](#7-integracion-con-componentes-existentes)
8. [Plan de Migracion](#8-plan-de-migracion)
9. [Metricas y Observabilidad](#9-metricas-y-observabilidad)
10. [Consideraciones de Seguridad](#10-consideraciones-de-seguridad)

---

## 1. Vision Ejecutiva

### 1.1 El Problema Fundamental

El sistema AI-Native MVP enfrenta un desafio pedagogico que trasciende la simple generacion de respuestas: garantizar que la asistencia de inteligencia artificial promueva el aprendizaje genuino en lugar de convertirse en un atajo cognitivo. Los estudiantes de programacion frecuentemente formulan preguntas ambiguas, buscan soluciones directas sin esfuerzo, o desarrollan dependencia excesiva de las herramientas de IA. Un chatbot educativo generico no puede abordar estos riesgos porque carece de la arquitectura cognitiva necesaria para distinguir entre una solicitud legitima de ayuda y un intento de delegacion total.

Esta propuesta presenta una arquitectura de **seis agentes especializados** donde cada componente mitiga un riesgo pedagogico especifico. El diseno sigue el principio de que **la IA no debe ensegnar directamente, sino orquestar decisiones pedagogicas** que guien al estudiante hacia el descubrimiento autonomo.

### 1.2 Filosofia de Diseno

El sistema propuesto opera bajo tres axiomas fundamentales:

**Axioma 1: Separacion de Responsabilidades Cognitivas**. Ningun agente individual maneja todo el flujo. El CRPE decide como se ensgena, el Knowledge-Retrieval determina que conocimiento es valido, el Tutor genera respuestas, Safety valida, y Scaffolding personaliza. Esta separacion permite auditar cada decision y corregir comportamientos especificos sin afectar el sistema completo.

**Axioma 2: Trazabilidad como Ciudadano de Primera Clase**. Cada interaccion produce evidencia del proceso cognitivo del estudiante. No se trata de logging para debugging, sino de capturar el "camino mental" que permite evaluar el proceso de aprendizaje, no solo el producto final.

**Axioma 3: Conocimiento Autorizado sobre Generacion Libre**. El sistema debe responder exclusivamente con contenido academico validado. Cuando el conocimiento local no alcanza, el fallback pedagogico proporciona explicaciones generales desacopladas de la evaluacion, protegiendo la integridad academica.

---

## 2. Analisis del Estado Actual

### 2.1 Componentes Existentes

El backend actual ya implementa una arquitectura de agentes parcialmente alineada con la vision propuesta:

| Agente Propuesto | Componente Actual | Estado | Ubicacion |
|------------------|-------------------|--------|-----------|
| CRPE / Gatekeeper | `CognitiveReasoningEngine` | **Parcial** | `core/cognitive_engine.py` |
| Knowledge-Retrieval | No existe | **Pendiente** | - |
| T-IA-Cog (Tutor) | `TutorCognitivoAgent` + modos | **Implementado** | `agents/tutor.py`, `agents/tutor_modes/` |
| Fallback Pedagogico | Respuestas fallback en AIGateway | **Parcial** | `core/ai_gateway.py` |
| Safety & Governance | `GobernanzaAgent` + `AnalistaRiesgoAgent` | **Implementado** | `agents/governance.py`, `agents/risk_analyst.py` |
| Scaffolding / Guidance | `GuidedStrategy` en tutor_modes | **Parcial** | `agents/tutor_modes/guided.py` |

### 2.2 Brechas Identificadas

**Brecha 1: Ausencia de Knowledge-Retrieval Agent**. El sistema actual envia prompts directamente al LLM sin consultar primero una base de conocimiento autorizado. Esto significa que el tutor puede generar respuestas basadas en conocimiento general del LLM que no este alineado con el curriculo de la catedra.

**Brecha 2: CRPE como Clasificador, no como Gatekeeper**. El `CognitiveReasoningEngine` actual clasifica intenciones y genera estrategias pedagogicas, pero no actua como verdadero "portero cognitivo" que decide rutas. La decision de bloqueo ocurre en el AIGateway, no en el motor cognitivo.

**Brecha 3: Fallback Pedagogico Basico**. Los fallbacks actuales en `_get_fallback_socratic_response()`, `_get_fallback_conceptual_explanation()` y `_get_fallback_guided_hints()` son respuestas estaticas cuando el LLM falla. El concepto de Fallback Pedagogico propuesto es diferente: respuestas para cuando el conocimiento local no alcanza, independientemente de la disponibilidad del LLM.

**Brecha 4: Scaffolding Fragmentado**. El andamiaje progresivo existe dentro de `GuidedStrategy` con 4 niveles de pistas, pero no como agente autonomo que personaliza el acompanamiento basandose en el historial completo del estudiante.

### 2.3 Fortalezas a Preservar

El sistema actual tiene fortalezas arquitectonicas significativas que deben preservarse:

- **AIGateway STATELESS**: La arquitectura sin estado permite escalabilidad horizontal. Cualquier nueva implementacion debe mantener este principio.
- **Repository Pattern**: La abstraccion de persistencia facilita testing y cambios de base de datos.
- **Strategy Pattern en Tutor Modes**: Los 6 modos pedagogicos (socratic, explicative, guided, metacognitive, training_hints, clarification) estan bien encapsulados.
- **Sistema de Trazabilidad N4**: Los 4 niveles de trazabilidad (superficial, tecnico, interaccional, cognitivo) ya capturan informacion rica.
- **Analista de Riesgos 5D**: Las 5 dimensiones de riesgo (cognitivo, etico, epistemico, tecnico, gobernanza) estan implementadas con deteccion heuristica y LLM.

---

## 3. Arquitectura Propuesta

### 3.1 Diagrama de Flujo Completo

```
                                    Estudiante
                                        |
                                        v
                    +-------------------------------------------+
                    |         CRPE / Gatekeeper Cognitivo       |
                    |  (core/cognitive_gatekeeper.py) [NUEVO]   |
                    +-------------------------------------------+
                          |                              |
                          | Clasifica intencion          | Detecta riesgo
                          | Sanitiza prompt              | Decide ruta
                          v                              v
        +-------------------------+         +-------------------------+
        |   Knowledge-Retrieval   |         |    Ruteo de Agentes     |
        | (core/knowledge_rag.py) |         |                         |
        |        [NUEVO]          |         | - Tutoria local         |
        +-------------------------+         | - Simulacion            |
                    |                       | - Evaluacion            |
                    | top-k documentos      | - Bloqueo               |
                    | score confianza       | - Escalamiento          |
                    v                       +-------------------------+
        +-------------------------+                     |
        |  Confianza >= umbral?   |<--------------------+
        +-------------------------+
              |              |
              | SI           | NO
              v              v
    +------------------+   +----------------------+
    |    T-IA-Cog      |   | Fallback Pedagogico  |
    | (agents/tutor.py)|   | (agents/fallback.py) |
    |    [EXISTENTE]   |   |       [NUEVO]        |
    +------------------+   +----------------------+
              |                      |
              v                      v
        +-------------------------------------------+
        |       Safety & Governance Agent           |
        | (agents/governance.py + risk_analyst.py)  |
        |              [EXISTENTE]                  |
        +-------------------------------------------+
                          |
            OK / WARN / BLOCK + correcciones
                          |
                          v
        +-------------------------------------------+
        |        Scaffolding / Guidance Agent       |
        |    (agents/scaffolding_agent.py) [NUEVO]  |
        +-------------------------------------------+
                          |
                          v
        +-------------------------------------------+
        |              TC-N4 Trazabilidad           |
        |         (agents/traceability.py)          |
        |              [EXISTENTE]                  |
        +-------------------------------------------+
                          |
                          v
                    Respuesta Final
              (con trazabilidad cognitiva)
```

### 3.2 Principios de Comunicacion Inter-Agente

Los agentes se comunican mediante objetos tipados que encapsulan tanto datos como metadatos de trazabilidad:

```python
@dataclass
class AgentMessage:
    """Mensaje estandarizado para comunicacion inter-agente"""
    id: str
    source_agent: str           # Agente emisor
    target_agent: str           # Agente receptor
    timestamp: datetime
    payload: Dict[str, Any]     # Contenido del mensaje
    trace_context: TraceContext # Contexto de trazabilidad
    routing_decision: Optional[RoutingDecision] = None
```

Cada agente recibe un `AgentMessage`, lo procesa, y produce otro `AgentMessage` para el siguiente en la cadena. El `trace_context` se propaga automaticamente, acumulando evidencia del camino de procesamiento.

---

## 4. Especificacion de Agentes

### 4.1 CRPE / Gatekeeper Cognitivo

**Ubicacion propuesta**: `backend/core/cognitive_gatekeeper.py`

**Rol**: Actua como "cerebro frontal" del sistema. No ensegna, sino que decide como se ensgena. Clasifica la intencion cognitiva del estudiante, sanitiza la interaccion para seguridad, y determina la ruta pedagogica apropiada.

**Responsabilidades**:
1. Clasificar intencion cognitiva: exploracion, pedido de ayuda, validacion, frustracion, intento de copia
2. Evaluar nivel de riesgo: bajo (exploracion conceptual), medio (dependencia de ayuda), alto (atajo cognitivo)
3. Sanitizar prompt: bloquear prompt injection, normalizar lenguaje, filtrar PII
4. Decidir ruta: tutoria local, simulacion, fallback, bloqueo, escalamiento a docente

**Entradas**:
```python
@dataclass
class GatekeeperInput:
    student_message: str
    activity_context: ActivityContext
    session_history: List[CognitiveTrace]
    policies: PolicyConfig
```

**Salidas**:
```python
@dataclass
class GatekeeperOutput:
    cognitive_intent: CognitiveIntent  # Enum: HELP, SOLUTION, VALIDATE, FRUSTRATION, EXPLORATION
    active_restrictions: List[str]      # Nivel de ayuda permitido, modo pedagogico
    risk_level: RiskLevel               # LOW, MEDIUM, HIGH, CRITICAL
    routing_decision: RoutingDecision   # TUTOR, SIMULATOR, FALLBACK, BLOCK, ESCALATE
    sanitized_prompt: str
    delegation_signals: List[str]
```

**Implementacion**:

```python
class CognitiveGatekeeper:
    """
    CRPE/Gatekeeper Cognitivo - Punto de entrada para clasificacion y ruteo.

    Extiende el CognitiveReasoningEngine existente con capacidades de
    gatekeeper: sanitizacion, evaluacion de riesgo, y decision de ruteo.
    """

    def __init__(
        self,
        cognitive_engine: CognitiveReasoningEngine,
        governance_agent: GobernanzaAgent,
        risk_analyst: AnalistaRiesgoAgent,
        config: Optional[Dict[str, Any]] = None
    ):
        self.cognitive_engine = cognitive_engine
        self.governance_agent = governance_agent
        self.risk_analyst = risk_analyst
        self.config = config or {}

        # Umbrales configurables
        self.risk_thresholds = {
            "delegation_signals_for_high": 2,
            "frustration_keywords_for_medium": 3,
        }

    def process(self, input: GatekeeperInput) -> GatekeeperOutput:
        """
        Procesa la entrada del estudiante y determina la ruta pedagogica.

        Este metodo es el punto de entrada principal del sistema. Coordina:
        1. Sanitizacion de seguridad (PII, prompt injection)
        2. Clasificacion cognitiva
        3. Evaluacion de riesgo
        4. Decision de ruteo
        """
        # 1. Sanitizar prompt (reusar GobernanzaAgent existente)
        sanitized_prompt, pii_detected = self.governance_agent.sanitize_prompt(
            input.student_message
        )

        # 2. Clasificar con CognitiveReasoningEngine existente
        classification = self.cognitive_engine.classify_prompt(
            sanitized_prompt,
            context={"activity": input.activity_context}
        )

        # 3. Mapear a intencion cognitiva
        cognitive_intent = self._map_to_cognitive_intent(classification)

        # 4. Evaluar nivel de riesgo
        risk_level = self._evaluate_risk_level(
            classification,
            input.session_history
        )

        # 5. Determinar ruta
        routing = self._determine_routing(
            cognitive_intent,
            risk_level,
            input.policies
        )

        return GatekeeperOutput(
            cognitive_intent=cognitive_intent,
            active_restrictions=self._get_active_restrictions(input.policies, risk_level),
            risk_level=risk_level,
            routing_decision=routing,
            sanitized_prompt=sanitized_prompt,
            delegation_signals=classification.get("delegation_signals", [])
        )

    def _determine_routing(
        self,
        intent: CognitiveIntent,
        risk: RiskLevel,
        policies: PolicyConfig
    ) -> RoutingDecision:
        """
        Decide la ruta basandose en intencion, riesgo y politicas.

        Logica de decision:
        - CRITICAL risk -> BLOCK (siempre)
        - HIGH risk + SOLUTION intent -> BLOCK
        - HIGH risk + HELP intent -> TUTOR (modo socratico estricto)
        - MEDIUM risk -> TUTOR (con warnings)
        - LOW risk -> TUTOR (normal)
        - FRUSTRATION intent -> puede escalar a docente
        """
        if risk == RiskLevel.CRITICAL:
            return RoutingDecision.BLOCK

        if risk == RiskLevel.HIGH:
            if intent == CognitiveIntent.SOLUTION:
                return RoutingDecision.BLOCK
            return RoutingDecision.TUTOR  # Con modo socratico forzado

        if intent == CognitiveIntent.FRUSTRATION:
            if policies.allow_escalation:
                return RoutingDecision.ESCALATE

        return RoutingDecision.TUTOR
```

### 4.2 Knowledge-Retrieval Agent

**Ubicacion propuesta**: `backend/core/knowledge_rag.py`

**Rol**: Ejecuta RAG (Retrieval-Augmented Generation) educativo sobre el conocimiento autorizado del sistema. Garantiza que las respuestas se basen exclusivamente en contenido academico validado por la catedra.

**Responsabilidades**:
1. Recibir consultas normalizadas del Gatekeeper
2. Buscar en el corpus de conocimiento autorizado (teoria, ejemplos, consignas, FAQ)
3. Aplicar filtros pedagogicos (unidad, dificultad, tipo de contenido)
4. Retornar top-k documentos con scores de confianza y trazabilidad de fuentes

**Entradas**:
```python
@dataclass
class KnowledgeQuery:
    normalized_query: str
    filters: PedagogicalFilters  # unidad, dificultad, tipo_contenido
    max_results: int = 5
    min_confidence: float = 0.7
```

**Salidas**:
```python
@dataclass
class KnowledgeResult:
    documents: List[RetrievedDocument]
    confidence_score: float          # Promedio de confianza
    source_traceability: List[str]   # IDs de documentos, unidades, referencias
    sufficient: bool                 # True si confianza >= umbral
```

**Implementacion**:

```python
class KnowledgeRetrievalAgent:
    """
    Agente de Recuperacion de Conocimiento Educativo.

    Implementa RAG sobre una base de conocimiento curada que incluye:
    - Contenido teorico de la catedra
    - Consignas de ejercicios
    - Ejemplos parciales (sin soluciones completas)
    - FAQ academico

    El agente nunca genera conocimiento; solo recupera lo que existe
    en la base autorizada.
    """

    def __init__(
        self,
        vector_store: VectorStore,          # Almacen de embeddings
        embedding_provider: EmbeddingProvider,
        config: Optional[Dict[str, Any]] = None
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.config = config or {}
        self.default_k = self.config.get("default_k", 5)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)

    async def retrieve(self, query: KnowledgeQuery) -> KnowledgeResult:
        """
        Recupera documentos relevantes para la consulta.

        El proceso:
        1. Genera embedding de la consulta
        2. Busca en el vector store con filtros pedagogicos
        3. Aplica re-ranking basado en relevancia educativa
        4. Retorna documentos con trazabilidad completa
        """
        # Generar embedding
        query_embedding = await self.embedding_provider.embed(query.normalized_query)

        # Construir filtros para vector store
        filters = self._build_filters(query.filters)

        # Buscar documentos similares
        raw_results = await self.vector_store.similarity_search(
            embedding=query_embedding,
            k=query.max_results * 2,  # Recuperar mas para re-ranking
            filters=filters
        )

        # Re-ranking educativo
        ranked_results = self._educational_rerank(raw_results, query)

        # Tomar top-k
        top_documents = ranked_results[:query.max_results]

        # Calcular confianza agregada
        avg_confidence = sum(d.score for d in top_documents) / len(top_documents) if top_documents else 0

        return KnowledgeResult(
            documents=top_documents,
            confidence_score=avg_confidence,
            source_traceability=[d.source_id for d in top_documents],
            sufficient=avg_confidence >= query.min_confidence
        )

    def _educational_rerank(
        self,
        results: List[RetrievedDocument],
        query: KnowledgeQuery
    ) -> List[RetrievedDocument]:
        """
        Re-ranking que prioriza contenido educativamente apropiado.

        Factores de re-ranking:
        - Alineacion con nivel de dificultad del estudiante
        - Preferencia por explicaciones conceptuales sobre codigo
        - Penalizacion de contenido que podria ser "solucion directa"
        """
        for doc in results:
            # Bonus por alineacion de dificultad
            if doc.difficulty == query.filters.difficulty:
                doc.score *= 1.2

            # Bonus por contenido conceptual
            if doc.content_type == "theory":
                doc.score *= 1.1
            elif doc.content_type == "complete_solution":
                doc.score *= 0.5  # Penalizar fuertemente

            # Bonus por misma unidad tematica
            if doc.unit == query.filters.unit:
                doc.score *= 1.15

        return sorted(results, key=lambda d: d.score, reverse=True)
```

### 4.3 Fallback Pedagogico

**Ubicacion propuesta**: `backend/agents/fallback_pedagogico.py`

**Rol**: Actua cuando el conocimiento local no es suficiente para responder. A diferencia de los fallbacks de error actuales, este agente proporciona explicaciones generales desacopladas de la consigna, protegiendo la integridad academica.

**Principio Fundamental**: "Si no esta en el programa, no se evalua". Las respuestas del fallback nunca deben poder usarse para resolver ejercicios evaluados.

**Implementacion**:

```python
class FallbackPedagogicoAgent:
    """
    Agente de Fallback Pedagogico.

    Actua cuando Knowledge-Retrieval no encuentra suficiente contexto
    en la base de conocimiento autorizada. Proporciona:
    - Explicaciones conceptuales generales
    - Disclaimer explicito de que no es contenido del curso
    - Sugerencia de consultar al docente
    - Referencias a documentacion externa

    REGLA DE ORO: Si no esta en el programa, no se evalua.
    Por lo tanto, las respuestas de este agente estan desacopladas
    de cualquier ejercicio o evaluacion.
    """

    def __init__(self, llm_provider: LLMProvider, config: Optional[Dict[str, Any]] = None):
        self.llm_provider = llm_provider
        self.config = config or {}

    async def generate_fallback(self, query: str, context: FallbackContext) -> FallbackResponse:
        """
        Genera una respuesta de fallback pedagogicamente segura.
        """
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=self._get_fallback_system_prompt()
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=f"Consulta del estudiante: {query}"
            )
        ]

        response = await self.llm_provider.generate(
            messages,
            max_tokens=400,
            temperature=0.7
        )

        return FallbackResponse(
            explanation=response.content,
            disclaimer=self._generate_disclaimer(),
            suggestions=[
                "Consulta con tu docente para verificar si esto aplica a tu ejercicio",
                "Revisa la documentacion oficial del lenguaje/framework",
                "Este contenido NO esta incluido en los criterios de evaluacion"
            ],
            is_evaluable=False  # Explicito: no puede usarse para evaluar
        )

    def _get_fallback_system_prompt(self) -> str:
        return """Eres un asistente educativo que proporciona explicaciones GENERALES
sobre conceptos de programacion.

REGLAS ESTRICTAS:
1. NO des codigo completo ni soluciones implementables
2. Explica conceptos de forma general, sin vinculacion a ejercicios especificos
3. Siempre aclara que esta informacion puede no estar en el programa del curso
4. Sugiere al estudiante verificar con su docente
5. Enfocate en el "por que" conceptual, no en el "como" implementar

Tu respuesta debe ser util para entender el concepto, pero NO debe permitir
resolver un ejercicio especifico. Mantene la explicacion abstracta y conceptual."""

    def _generate_disclaimer(self) -> str:
        return """⚠️ NOTA IMPORTANTE: Esta explicacion es de caracter GENERAL y puede
no estar incluida en el contenido del curso. No se utilizara para evaluar
tu desempeno. Si necesitas ayuda con un ejercicio especifico, consulta
con tu docente o revisa el material del curso."""
```

### 4.4 Scaffolding / Guidance Agent

**Ubicacion propuesta**: `backend/agents/scaffolding_agent.py`

**Rol**: Personaliza el acompanamiento pedagogico mediante andamiaje progresivo. A diferencia de `GuidedStrategy` que genera pistas dentro de una respuesta, este agente decide el nivel de andamiaje apropiado basandose en el historial completo del estudiante.

**Implementacion**:

```python
class ScaffoldingAgent:
    """
    Agente de Andamiaje Progresivo.

    Personaliza el nivel de ayuda basandose en:
    - Historial de interacciones del estudiante
    - Patron de uso de pistas previas
    - Estado cognitivo actual
    - Progreso en la actividad

    Produce pistas graduadas con justificacion pedagogica.
    """

    HELP_LEVELS = {
        1: "muy_abstracto",    # "Piensa en estructuras de datos..."
        2: "conceptual",       # "Considera estructuras FIFO..."
        3: "mas_concreto",     # "Una cola tiene operaciones enqueue/dequeue..."
        4: "especifico"        # "Podrias usar lista con append y pop(0)..."
    }

    def __init__(
        self,
        guided_strategy: GuidedStrategy,  # Reusar estrategia existente
        trace_repository: TraceRepositoryProtocol,
        config: Optional[Dict[str, Any]] = None
    ):
        self.guided_strategy = guided_strategy
        self.trace_repo = trace_repository
        self.config = config or {}

    def determine_scaffolding(
        self,
        student_id: str,
        activity_id: str,
        current_state: CognitiveState,
        session_context: SessionContext
    ) -> ScaffoldingDecision:
        """
        Determina el nivel de andamiaje apropiado para el estudiante.

        Algoritmo:
        1. Cargar historial de pistas usadas en esta actividad
        2. Calcular "distancia a la solucion" basada en intentos
        3. Evaluar si el estudiante esta estancado
        4. Ajustar nivel de ayuda progresivamente
        """
        # Obtener historial de pistas en esta sesion
        hint_history = self._get_hint_history(student_id, activity_id)
        current_level = self._calculate_current_level(hint_history)

        # Evaluar si debe subir de nivel
        attempts_since_last_hint = session_context.attempts_count - len(hint_history)
        time_since_last_hint = session_context.current_duration - (hint_history[-1].timestamp if hint_history else 0)

        should_advance = (
            attempts_since_last_hint >= 3 or  # 3 intentos fallidos
            time_since_last_hint > timedelta(minutes=5)  # 5 minutos estancado
        )

        if should_advance and current_level < 4:
            current_level += 1

        return ScaffoldingDecision(
            help_level=current_level,
            help_type=self.HELP_LEVELS[current_level],
            pedagogical_justification=self._generate_justification(
                current_level, attempts_since_last_hint, current_state
            ),
            hints=self._generate_graduated_hints(
                current_level, session_context.exercise_context
            )
        )

    def _generate_graduated_hints(
        self,
        level: int,
        exercise_context: ExerciseContext
    ) -> List[str]:
        """
        Genera 2-4 pistas graduadas segun el nivel de ayuda.

        Nivel 1: Solo preguntas orientadoras
        Nivel 2: Preguntas + nombres de conceptos
        Nivel 3: Preguntas + estrategia de alto nivel
        Nivel 4: Preguntas + pseudocodigo abstracto (sin sintaxis real)
        """
        # Delegar a GuidedStrategy existente
        return self.guided_strategy.generate_hints(
            exercise_context,
            help_level=level
        )
```

---

## 5. Flujo de Procesamiento

### 5.1 Ejemplo Completo: "No me sale este ejercicio"

Este ejemplo ilustra como fluye una solicitud tipica a traves de la arquitectura completa:

**Paso 1: Recepcion en AIGateway**
```python
# Endpoint /api/v1/interactions recibe:
{
    "session_id": "sess_abc123",
    "prompt": "No me sale este ejercicio",
    "context": {"activity_id": "act_sort_list"}
}
```

**Paso 2: Gatekeeper Cognitivo**
```python
# CognitiveGatekeeper.process()
gatekeeper_output = GatekeeperOutput(
    cognitive_intent=CognitiveIntent.HELP,          # Pide ayuda, no solucion
    active_restrictions=["max_help_level=0.7"],
    risk_level=RiskLevel.MEDIUM,                    # Ambiguo, podria ser frustracion
    routing_decision=RoutingDecision.TUTOR,
    sanitized_prompt="No me sale este ejercicio",
    delegation_signals=[]                           # Sin seniales de delegacion
)
```

**Paso 3: Knowledge-Retrieval**
```python
# KnowledgeRetrievalAgent.retrieve()
knowledge_result = KnowledgeResult(
    documents=[
        RetrievedDocument(
            content="Ordenamiento: conceptos de comparacion...",
            source_id="doc_sorting_theory",
            unit="algorithms",
            score=0.85
        ),
        RetrievedDocument(
            content="FAQ: Como abordar problemas de ordenamiento",
            source_id="doc_faq_sorting",
            unit="algorithms",
            score=0.82
        )
    ],
    confidence_score=0.835,
    source_traceability=["doc_sorting_theory", "doc_faq_sorting"],
    sufficient=True  # 0.835 >= 0.7 umbral
)
```

**Paso 4: T-IA-Cog (Modo Socratico)**
```python
# TutorCognitivoAgent con SocraticStrategy
# Recibe knowledge_result como contexto RAG
tutor_response = TutorResponse(
    content="""
    Entiendo que estas teniendo dificultades. Antes de ayudarte,
    necesito entender mejor tu situacion:

    1. ¿Que parte especifica del ejercicio te esta costando?
    2. ¿Que has intentado hasta ahora?
    3. ¿Que resultado esperabas obtener vs. que obtuviste?

    Cuando me cuentes esto, podre guiarte mejor en tu razonamiento.
    """,
    mode="socratic",
    rag_sources=["doc_sorting_theory", "doc_faq_sorting"]
)
```

**Paso 5: Safety & Governance**
```python
# GobernanzaAgent.verify_compliance()
compliance_result = {
    "status": ComplianceStatus.COMPLIANT,
    "violations": [],
    "warnings": [],
    "allow_action": True
}

# AnalistaRiesgoAgent (en background)
# No detecta riesgos porque el estudiante aun no mostro patrones problematicos
```

**Paso 6: Scaffolding**
```python
# ScaffoldingAgent.determine_scaffolding()
# Este es el primer intento, nivel 1 de ayuda
scaffolding = ScaffoldingDecision(
    help_level=1,
    help_type="muy_abstracto",
    pedagogical_justification="Primera solicitud de ayuda, comenzar con orientacion minima",
    hints=[]  # En nivel 1, solo preguntas socraticas, sin pistas adicionales
)
```

**Paso 7: Respuesta Final con Trazabilidad**
```python
# TC-N4 registra la traza cognitiva
cognitive_trace = CognitiveTrace(
    session_id="sess_abc123",
    student_id="student_xyz",
    activity_id="act_sort_list",
    trace_level=TraceLevel.N4_COGNITIVO,
    interaction_type=InteractionType.AI_RESPONSE,
    content=tutor_response.content,
    cognitive_state=CognitiveState.EXPLORACION,
    cognitive_intent="help_request",
    ai_involvement=0.3,  # Bajo porque solo hizo preguntas
    rag_sources=["doc_sorting_theory", "doc_faq_sorting"]
)
```

### 5.2 Diagrama de Secuencia

```
Estudiante    AIGateway    Gatekeeper    KnowledgeRAG    Tutor    Safety    Scaffolding    TC-N4
    |             |            |              |            |         |           |           |
    |--prompt---->|            |              |            |         |           |           |
    |             |--input---->|              |            |         |           |           |
    |             |            |--classify--->|            |         |           |           |
    |             |            |<--routing----|            |         |           |           |
    |             |            |              |            |         |           |           |
    |             |            |-----------query---------->|         |           |           |
    |             |            |<---------documents--------|         |           |           |
    |             |            |              |            |         |           |           |
    |             |            |------------context+query----------->|           |           |
    |             |            |              |            |<--------|           |           |
    |             |            |              |            |--response---------->|           |
    |             |            |              |            |         |<--verify--|           |
    |             |            |              |            |         |--ok------>|           |
    |             |            |              |            |         |           |--level--->|
    |             |            |              |            |         |           |<--ok------|
    |             |            |              |            |         |           |           |
    |             |<------------------------final response + trace------------------|
    |<--response--|            |              |            |         |           |           |
```

---

## 6. Implementacion Tecnica

### 6.1 Nuevos Archivos a Crear

```
backend/
├── core/
│   ├── cognitive_gatekeeper.py     # CRPE/Gatekeeper (nuevo)
│   ├── knowledge_rag.py            # Knowledge-Retrieval Agent (nuevo)
│   └── agent_protocols.py          # Protocolos de comunicacion (nuevo)
├── agents/
│   ├── fallback_pedagogico.py      # Fallback Pedagogico (nuevo)
│   ├── scaffolding_agent.py        # Scaffolding Agent (nuevo)
│   └── agent_message.py            # AgentMessage dataclass (nuevo)
└── database/
    ├── models/
    │   └── knowledge_document.py   # Modelo para documentos RAG (nuevo)
    └── repositories/
        └── knowledge_repository.py # Repositorio para RAG (nuevo)
```

### 6.2 Modificaciones a Archivos Existentes

**`core/ai_gateway.py`**:
- Integrar `CognitiveGatekeeper` como primer paso del flujo
- Agregar llamada a `KnowledgeRetrievalAgent` antes del tutor
- Modificar `_process_tutor_mode` para recibir contexto RAG
- Agregar `ScaffoldingAgent` antes de generar respuesta final

**`core/cognitive_engine.py`**:
- Extraer logica de clasificacion a metodos reutilizables por Gatekeeper
- Agregar enums `CognitiveIntent` y `RoutingDecision`

**`agents/tutor.py`**:
- Modificar para recibir `KnowledgeResult` como contexto
- Agregar referencias a fuentes en respuestas

### 6.3 Integracion con Vector Store

Para el Knowledge-Retrieval Agent, se recomienda usar una solucion de vector store que pueda deployearse localmente para mantener datos en infraestructura propia:

**Opcion 1: ChromaDB** (Recomendada para MVP)
```python
# Instalacion: pip install chromadb
import chromadb

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "./chroma_data"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("knowledge_base")

    async def similarity_search(
        self,
        embedding: List[float],
        k: int,
        filters: Optional[Dict] = None
    ) -> List[RetrievedDocument]:
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
            where=filters
        )
        return self._parse_results(results)
```

**Opcion 2: PostgreSQL con pgvector** (Para produccion)
```sql
-- Agregar extension pgvector
CREATE EXTENSION vector;

-- Tabla de documentos con embeddings
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    content_type VARCHAR(50),  -- theory, example, faq, consigna
    unit VARCHAR(100),
    difficulty VARCHAR(20),
    embedding vector(1536),    -- Dimension de OpenAI embeddings
    source_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indice para busqueda de similitud
CREATE INDEX ON knowledge_documents
USING ivfflat (embedding vector_cosine_ops);
```

---

## 7. Integracion con Componentes Existentes

### 7.1 Mapeo de Componentes Actuales a Propuestos

| Propuesto | Actual | Estrategia de Integracion |
|-----------|--------|---------------------------|
| `CognitiveGatekeeper` | `CognitiveReasoningEngine` | **Composicion**: Gatekeeper usa Engine internamente |
| `KnowledgeRetrievalAgent` | No existe | **Nuevo**: Crear desde cero |
| Fallback en Tutor | Fallbacks en AIGateway | **Refactor**: Extraer a agente dedicado |
| `ScaffoldingAgent` | `GuidedStrategy` | **Composicion**: Agent usa Strategy internamente |
| Safety & Governance | `GobernanzaAgent` + `AnalistaRiesgoAgent` | **Sin cambios**: Usar como estan |
| TC-N4 | `traceability.py` | **Extension**: Agregar campos RAG |

### 7.2 Backward Compatibility

Para mantener compatibilidad con codigo existente, la integracion sera opcional mediante feature flags:

```python
# En .env
ENABLE_COGNITIVE_GATEKEEPER=true   # Usar nuevo flujo con Gatekeeper
ENABLE_KNOWLEDGE_RAG=true          # Usar RAG antes del tutor
ENABLE_SCAFFOLDING_AGENT=true      # Usar andamiaje personalizado

# En ai_gateway.py
if settings.ENABLE_COGNITIVE_GATEKEEPER:
    gatekeeper_output = self.cognitive_gatekeeper.process(input)
    if gatekeeper_output.routing_decision == RoutingDecision.BLOCK:
        return self._generate_blocked_response(...)
else:
    # Flujo actual sin Gatekeeper
    classification = self.cognitive_engine.classify_prompt(prompt, context)
```

---

## 8. Plan de Migracion

### 8.1 Fase 1: Infraestructura Base (2 semanas)

**Objetivo**: Crear los nuevos archivos y modelos sin afectar el flujo actual.

**Entregables**:
1. `agent_protocols.py` con dataclasses `AgentMessage`, `GatekeeperInput/Output`, etc.
2. `cognitive_gatekeeper.py` con logica basica (wrapper sobre CognitiveReasoningEngine)
3. `knowledge_document.py` modelo ORM para documentos RAG
4. `knowledge_repository.py` repositorio basico
5. Migracion de base de datos para tabla `knowledge_documents`

**Criterio de Exito**: Tests unitarios pasan, no hay cambios en comportamiento del sistema.

### 8.2 Fase 2: Knowledge-Retrieval (3 semanas)

**Objetivo**: Implementar RAG funcional con ChromaDB.

**Entregables**:
1. `knowledge_rag.py` con integracion ChromaDB
2. Script de ingesta para cargar contenido academico inicial
3. Modificacion de `_process_tutor_mode` para recibir contexto RAG
4. Feature flag `ENABLE_KNOWLEDGE_RAG`

**Criterio de Exito**: El tutor puede citar fuentes en sus respuestas cuando RAG esta habilitado.

### 8.3 Fase 3: Gatekeeper Completo (2 semanas)

**Objetivo**: Gatekeeper toma decisiones de ruteo.

**Entregables**:
1. Logica completa de `_determine_routing` en Gatekeeper
2. Integracion en AIGateway como primer paso del flujo
3. Feature flag `ENABLE_COGNITIVE_GATEKEEPER`
4. Nuevas metricas Prometheus para routing decisions

**Criterio de Exito**: El Gatekeeper bloquea correctamente intentos de delegacion total.

### 8.4 Fase 4: Scaffolding y Fallback (2 semanas)

**Objetivo**: Completar los agentes restantes.

**Entregables**:
1. `scaffolding_agent.py` funcional
2. `fallback_pedagogico.py` funcional
3. Integracion en flujo principal
4. Feature flags correspondientes

**Criterio de Exito**: El nivel de ayuda se ajusta progresivamente segun historial.

### 8.5 Fase 5: Observabilidad y Tuning (1 semana)

**Objetivo**: Metricas, logging, y ajuste de umbrales.

**Entregables**:
1. Dashboard Grafana para visualizar flujo de agentes
2. Alertas para patrones anomalos
3. Documentacion de umbrales configurables
4. Tests de integracion end-to-end

---

## 9. Metricas y Observabilidad

### 9.1 Metricas Prometheus Propuestas

```python
# Nuevas metricas en api/monitoring/metrics.py

# Gatekeeper
gatekeeper_routing_decisions = Counter(
    "gatekeeper_routing_decisions_total",
    "Decisiones de ruteo del Gatekeeper",
    ["decision"]  # TUTOR, BLOCK, ESCALATE, FALLBACK
)

gatekeeper_cognitive_intents = Counter(
    "gatekeeper_cognitive_intents_total",
    "Intenciones cognitivas detectadas",
    ["intent"]  # HELP, SOLUTION, VALIDATE, FRUSTRATION, EXPLORATION
)

gatekeeper_risk_levels = Counter(
    "gatekeeper_risk_levels_total",
    "Niveles de riesgo evaluados",
    ["level"]  # LOW, MEDIUM, HIGH, CRITICAL
)

# Knowledge-Retrieval
rag_queries_total = Counter(
    "rag_queries_total",
    "Total de consultas al sistema RAG"
)

rag_confidence_histogram = Histogram(
    "rag_confidence_score",
    "Distribucion de scores de confianza RAG",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

rag_fallback_triggers = Counter(
    "rag_fallback_triggers_total",
    "Veces que RAG disparo fallback por baja confianza"
)

# Scaffolding
scaffolding_levels = Counter(
    "scaffolding_help_levels_total",
    "Niveles de ayuda aplicados",
    ["level"]  # 1, 2, 3, 4
)

scaffolding_progressions = Counter(
    "scaffolding_level_progressions_total",
    "Progresiones de nivel de ayuda"
)
```

### 9.2 Logging Estructurado

Cada agente producira logs estructurados que permitan reconstruir el flujo:

```python
logger.info(
    "Gatekeeper decision",
    extra={
        "flow_id": flow_id,
        "session_id": session_id,
        "cognitive_intent": output.cognitive_intent.value,
        "risk_level": output.risk_level.value,
        "routing_decision": output.routing_decision.value,
        "delegation_signals": output.delegation_signals,
        "duration_ms": duration
    }
)
```

---

## 10. Consideraciones de Seguridad

### 10.1 Proteccion contra Prompt Injection

El Gatekeeper debe implementar protecciones adicionales contra ataques de prompt injection:

```python
class PromptInjectionDetector:
    """
    Detector de intentos de prompt injection.

    Patrones detectados:
    - Instrucciones para ignorar reglas previas
    - Intentos de cambiar el rol del sistema
    - Solicitudes de revelar prompts internos
    """

    INJECTION_PATTERNS = [
        r"ignor[ae]?\s+(las|todas|cualquier).*(reglas?|instrucciones?)",
        r"olvid[ae]?\s+(lo|todo).*(anterior|previo)",
        r"ahora\s+sos\s+un",
        r"nuevo\s+rol:",
        r"system\s*prompt",
        r"reveal\s+your\s+instructions",
    ]

    def detect(self, prompt: str) -> Tuple[bool, List[str]]:
        """Retorna (is_injection, matched_patterns)"""
        prompt_lower = prompt.lower()
        matches = []
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, prompt_lower):
                matches.append(pattern)
        return len(matches) > 0, matches
```

### 10.2 Aislamiento de Datos Sensibles

El Knowledge-Retrieval Agent solo debe acceder a contenido academico, nunca a datos personales de estudiantes:

```python
class KnowledgeRetrievalAgent:
    def __init__(self, ...):
        # Verificar que el vector store solo tiene documentos academicos
        self._verify_collection_isolation()

    def _verify_collection_isolation(self):
        """
        Verifica que la coleccion no contiene datos sensibles.

        Esto es un check de seguridad que previene mezclar
        documentos academicos con datos de estudiantes.
        """
        # La coleccion debe estar en un namespace separado
        assert self.collection.name == "knowledge_base"

        # No debe haber metadatos de estudiantes
        sample = self.collection.peek(10)
        for doc in sample["metadatas"]:
            assert "student_id" not in doc
            assert "email" not in doc
```

---

## Conclusion

Esta propuesta tecnica presenta una evolucion significativa de la arquitectura actual hacia un sistema multi-agente donde cada componente mitiga un riesgo pedagogico especifico. Los seis agentes (CRPE/Gatekeeper, Knowledge-Retrieval, T-IA-Cog, Fallback Pedagogico, Safety & Governance, Scaffolding) trabajan coordinadamente para garantizar que la asistencia de IA promueva el aprendizaje genuino.

Las principales fortalezas de la propuesta son:

1. **Reutilizacion**: Los componentes existentes (CognitiveReasoningEngine, GobernanzaAgent, GuidedStrategy) se integran mediante composicion, no reemplazo.

2. **Gradualidad**: El plan de migracion permite activar cada nuevo componente mediante feature flags, minimizando riesgo.

3. **Trazabilidad**: Cada decision de cada agente genera evidencia para auditoria pedagogica.

4. **Escalabilidad**: La arquitectura stateless se preserva, permitiendo scaling horizontal.

El resultado final sera un sistema que no simplemente responde preguntas, sino que orquesta decisiones pedagogicas con trazabilidad cognitiva completa, protegiendo la integridad del proceso de aprendizaje.

---

*Documento generado: Enero 2026*
*Version: 1.0*
*Autor: Propuesta tecnica basada en analisis de backend/README.md y ImplementacionAgentes.md original*
