# Propuesta de Integración: Entrenador Digital con Ecosistema de Agentes

**Documento**: Propuesta Arquitectónica de Integración
**Autor**: Arquitecto de Software
**Fecha**: Diciembre 2025
**Versión**: 1.0
**Estado**: Propuesta para revisión

---

## 1. Resumen Ejecutivo

El Entrenador Digital actualmente opera como un módulo aislado que no aprovecha el ecosistema de agentes de IA ni el sistema de trazabilidad N4. Esta propuesta presenta una arquitectura de integración que:

1. Incorpora al agente **T-IA-Cog** (Tutor Cognitivo) para la generación de pistas contextualizadas
2. Integra la **trazabilidad N4** para capturar el proceso de resolución de ejercicios
3. Conecta con **AR-IA** (Analista de Riesgos) para detectar patrones de comportamiento
4. Mantiene **compatibilidad hacia atrás** con el flujo actual

La integración permitirá evaluar no solo si el estudiante resuelve el ejercicio, sino **cómo lo resuelve**, alineando el Entrenador Digital con la filosofía central del sistema AI-Native.

---

## 2. Análisis de la Situación Actual

### 2.1 Arquitectura Actual del Entrenador Digital

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA ACTUAL                          │
│                    (Módulo Aislado)                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌────────────────┐    ┌───────────────┐    ┌─────┐
│Estudiante│───▶│ Router         │───▶│ CodeEvaluator │───▶│ LLM │
│          │    │ /training/*    │    │ ("Alex")      │    │     │
└──────────┘    └────────────────┘    └───────────────┘    └──┬──┘
                       │                                       │
                       ▼                                       ▼
                ┌─────────────┐                         ┌──────────┐
                │ Session     │                         │ Respuesta│
                │ Storage     │                         │ directa  │
                │ (Redis)     │                         └──────────┘
                └─────────────┘
                       │
                       ▼
                ┌─────────────┐
                │ Pistas      │◀─── Texto estático de BD
                │ predefinidas│     (sin contextualización)
                └─────────────┘
```

### 2.2 Problemas Identificados

| Problema | Impacto | Severidad |
|----------|---------|-----------|
| **Sin trazabilidad N4** | No se captura el proceso cognitivo durante ejercicios | Alta |
| **Pistas estáticas** | Las pistas no se adaptan al contexto del estudiante | Media |
| **Sin análisis de riesgos** | No se detecta copy-paste, delegación o frustración | Alta |
| **Sin continuidad pedagógica** | El progreso en entrenamiento no alimenta al tutor | Media |
| **Evaluación solo de producto** | "Alex" evalúa código final, no el proceso | Alta |

### 2.3 Código Actual del Endpoint de Pistas

```python
# backend/api/routers/training/endpoints.py (líneas 302-362)
@router.post("/pista", response_model=PistaResponse)
async def solicitar_pista(request: SolicitarPistaRequest, ...):
    # Obtiene pista de lista predefinida
    pista = ejercicio['pistas'][request.numero_pista]  # ← Texto estático

    return PistaResponse(
        contenido=pista,
        numero=request.numero_pista,
        total_pistas=len(ejercicio['pistas'])
    )
```

**Observación crítica**: Las pistas son texto plano almacenado en BD, sin ningún procesamiento cognitivo ni adaptación al contexto del estudiante.

---

## 3. Propuesta de Integración (Modelo C4)

### 3.1 Diagrama de Contexto (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SISTEMA AI-NATIVE MVP                           │
│                    (con Entrenador Digital Integrado)                   │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────┐
                              │Estudiante│
                              └────┬─────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐        ┌─────────────────┐        ┌───────────────┐
│  Modo Tutor   │        │   Entrenador    │        │  Simuladores  │
│ (conversación │        │    Digital      │        │ Profesionales │
│   abierta)    │        │  (ejercicios)   │        │               │
└───────┬───────┘        └────────┬────────┘        └───────┬───────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │      AIGateway          │
                    │   (Orquestador Central) │
                    └─────────────────────────┘
                                  │
        ┌─────────────┬───────────┼───────────┬─────────────┐
        ▼             ▼           ▼           ▼             ▼
    ┌───────┐    ┌────────┐  ┌────────┐  ┌────────┐   ┌─────────┐
    │T-IA-Cog│   │E-IA-Proc│ │ AR-IA  │  │ GOV-IA │   │  TC-N4  │
    │ Tutor │    │Evaluador│ │Riesgos │  │Gobierno│   │Trazabil.│
    └───────┘    └────────┘  └────────┘  └────────┘   └─────────┘
```

### 3.2 Diagrama de Contenedores (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENTRENADOR DIGITAL INTEGRADO                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Training       │     │   Training       │     │    Training      │
│   Router         │────▶│   Gateway        │────▶│    Orchestrator  │
│   (endpoints)    │     │   (NUEVO)        │     │    (NUEVO)       │
└──────────────────┘     └────────┬─────────┘     └────────┬─────────┘
                                  │                        │
                    ┌─────────────┼─────────────┐          │
                    ▼             ▼             ▼          ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
            │ T-IA-Cog  │  │  AR-IA    │  │  TC-N4    │  │CodeEvalua-│
            │(Guided    │  │(Análisis  │  │(Trazas de │  │tor "Alex" │
            │ Mode)     │  │ en tiempo │  │ ejercicio)│  │(Evaluación│
            │           │  │ real)     │  │           │  │ final)    │
            └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

### 3.3 Diagrama de Componentes (C4 Level 3)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TrainingGateway (NUEVO)                            │
│                                                                         │
│  Responsabilidad: Orquestar la integración del Entrenador Digital       │
│                   con el ecosistema de agentes                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ HintOrchestrator│    │ TraceCollector  │    │ RiskMonitor     │     │
│  │                 │    │                 │    │                 │     │
│  │ - Decide si usar│    │ - Captura N4 de │    │ - Monitorea     │     │
│  │   T-IA-Cog o    │    │   cada intento  │    │   tiempo entre  │     │
│  │   pista estática│    │ - Registra      │    │   intentos      │     │
│  │ - Contextualiza │    │   solicitudes   │    │ - Detecta       │     │
│  │   con historial │    │   de pistas     │    │   copy-paste    │     │
│  │ - Aplica nivel  │    │ - Crea          │    │ - Identifica    │     │
│  │   de andamiaje  │    │   secuencias    │    │   frustración   │     │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘     │
│           │                      │                      │               │
│           └──────────────────────┼──────────────────────┘               │
│                                  │                                      │
│                                  ▼                                      │
│                    ┌─────────────────────────┐                          │
│                    │   TrainingContext       │                          │
│                    │   (Estado compartido)   │                          │
│                    │                         │                          │
│                    │ - session_id            │                          │
│                    │ - exercise_id           │                          │
│                    │ - attempts_history      │                          │
│                    │ - hints_requested       │                          │
│                    │ - cognitive_state       │                          │
│                    │ - time_spent            │                          │
│                    │ - risk_alerts[]         │                          │
│                    └─────────────────────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Diseño Detallado de Integración

### 4.1 Nuevo Agente: T-IA-Cog-Training (Tutor para Entrenamiento)

Este no es un agente nuevo, sino una **especialización del modo Guiado** de T-IA-Cog adaptada al contexto de ejercicios estructurados.

```python
# backend/agents/tutor_modes/training_hints.py (NUEVO)

class TrainingHintsStrategy(GuidedStrategy):
    """
    Estrategia de pistas para el Entrenador Digital.

    Extiende GuidedStrategy con:
    1. Conocimiento del ejercicio específico (consigna, tests, restricciones)
    2. Historial de intentos previos del estudiante
    3. Análisis de errores de compilación/ejecución
    4. Contexto de la lección (qué conceptos se están practicando)

    Mantiene las 4 reglas pedagógicas inquebrantables:
    - Nunca código completo
    - Siempre descomponer
    - Exigir justificación
    - Priorizar razonamiento
    """

    @property
    def mode(self) -> TutorMode:
        return TutorMode.GUIADO

    @property
    def pedagogical_intent(self) -> str:
        return "training_scaffolding"

    async def generate_contextual_hint(
        self,
        exercise_context: ExerciseContext,
        student_attempts: List[AttemptTrace],
        requested_hint_level: int,
        last_error: Optional[str] = None
    ) -> TutorResponse:
        """
        Genera pista contextualizada basada en:

        1. El ejercicio específico (qué se está practicando)
        2. Los intentos previos (qué errores cometió)
        3. El error actual (si hay uno)
        4. El nivel de pista solicitado (1-4)
        5. El historial de pistas ya recibidas
        """
        # Construir contexto enriquecido
        context = TutorModeContext(
            student_prompt=self._build_implicit_prompt(exercise_context, last_error),
            cognitive_state=self._infer_cognitive_state(student_attempts),
            student_history=student_attempts,
            llm_provider=self.llm_provider,
            strategy={
                "help_level": self._map_hint_level(requested_hint_level),
                "exercise_type": exercise_context.exercise_type,
                "target_concepts": exercise_context.learning_objectives
            }
        )

        # Usar la generación guiada pero con contexto de ejercicio
        return await self.generate_response(context)

    def _build_implicit_prompt(
        self,
        exercise: ExerciseContext,
        last_error: Optional[str]
    ) -> str:
        """
        Construye un "prompt implícito" que representa lo que el estudiante
        está preguntando al solicitar una pista.
        """
        if last_error:
            return f"""
            Estoy trabajando en el ejercicio "{exercise.title}".
            Mi último intento produjo este error: {last_error}
            Necesito ayuda para entender qué está mal.
            """
        else:
            return f"""
            Estoy trabajando en el ejercicio "{exercise.title}".
            La consigna es: {exercise.mission[:200]}...
            No sé cómo empezar o continuar.
            """

    def _infer_cognitive_state(self, attempts: List[AttemptTrace]) -> str:
        """
        Infiere el estado cognitivo basado en el patrón de intentos.
        """
        if not attempts:
            return "exploracion"  # Primer intento

        last_attempts = attempts[-3:]  # Últimos 3 intentos

        # Si todos fallan con el mismo error → atascado
        if len(set(a.error_type for a in last_attempts)) == 1:
            return "atascado"

        # Si hay progreso (menos errores) → implementando
        if self._shows_progress(last_attempts):
            return "implementacion"

        # Si hay muchos intentos rápidos → posible frustración
        if self._shows_frustration(last_attempts):
            return "confusion"

        return "depuracion"
```

### 4.2 Integración con Trazabilidad N4

```python
# backend/core/training_traceability.py (NUEVO)

class TrainingTraceCollector:
    """
    Colector de trazas N4 para el Entrenador Digital.

    Captura eventos cognitivos durante la resolución de ejercicios:
    - Inicio de ejercicio (exploración)
    - Cada intento de código (implementación/depuración)
    - Solicitud de pistas (búsqueda de ayuda)
    - Errores de ejecución (debugging)
    - Éxito final (validación)
    """

    def __init__(self, traceability_agent: TrazabilidadN4Agent):
        self.tc_n4 = traceability_agent

    async def trace_exercise_start(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str
    ) -> CognitiveTrace:
        """Registra inicio de ejercicio como estado EXPLORACIÓN."""
        return self.tc_n4.capture_interaction(
            student_id=student_id,
            activity_id=exercise_id,
            interaction_type=InteractionType.STRATEGY_CHANGE,
            content=f"Inició ejercicio {exercise_id}",
            level=TraceLevel.N4_COGNITIVO,
            cognitive_state="exploracion",
            cognitive_intent="comprension_problema",
            session_id=session_id,
            context={"event": "exercise_start", "exercise_id": exercise_id}
        )

    async def trace_code_attempt(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        code: str,
        result: dict,
        attempt_number: int
    ) -> CognitiveTrace:
        """Registra cada intento de código."""
        # Determinar estado cognitivo basado en resultado
        if result.get("tests_passed") == result.get("tests_total"):
            cognitive_state = "validacion"
            intent = "verificacion_solucion"
        elif result.get("stderr"):
            cognitive_state = "depuracion"
            intent = "correccion_error"
        else:
            cognitive_state = "implementacion"
            intent = "construccion_solucion"

        return self.tc_n4.capture_interaction(
            student_id=student_id,
            activity_id=exercise_id,
            interaction_type=InteractionType.CODE_COMMIT,
            content=f"Intento #{attempt_number}: {len(code)} chars",
            level=TraceLevel.N4_COGNITIVO,
            cognitive_state=cognitive_state,
            cognitive_intent=intent,
            session_id=session_id,
            context={
                "event": "code_attempt",
                "attempt_number": attempt_number,
                "tests_passed": result.get("tests_passed", 0),
                "tests_total": result.get("tests_total", 0),
                "has_error": bool(result.get("stderr")),
                "code_length": len(code)
            }
        )

    async def trace_hint_request(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        hint_level: int,
        hints_already_used: int,
        time_since_last_attempt: float
    ) -> CognitiveTrace:
        """Registra solicitud de pista con contexto cognitivo."""
        # Analizar el patrón de solicitud
        if time_since_last_attempt < 30:  # Menos de 30 segundos
            cognitive_intent = "busqueda_rapida_ayuda"
        elif hints_already_used > 2:
            cognitive_intent = "dependencia_pistas"
        else:
            cognitive_intent = "busqueda_orientacion"

        return self.tc_n4.capture_interaction(
            student_id=student_id,
            activity_id=exercise_id,
            interaction_type=InteractionType.STUDENT_PROMPT,
            content=f"Solicitó pista nivel {hint_level}",
            level=TraceLevel.N4_COGNITIVO,
            cognitive_state="atascado",
            cognitive_intent=cognitive_intent,
            session_id=session_id,
            ai_involvement=0.3 + (hint_level * 0.15),  # Más pista = más ayuda IA
            context={
                "event": "hint_request",
                "hint_level": hint_level,
                "hints_already_used": hints_already_used,
                "time_since_last_attempt": time_since_last_attempt
            }
        )
```

### 4.3 Integración con Análisis de Riesgos

```python
# backend/core/training_risk_monitor.py (NUEVO)

class TrainingRiskMonitor:
    """
    Monitor de riesgos en tiempo real para el Entrenador Digital.

    Detecta patrones problemáticos durante la resolución de ejercicios:
    - Copy-paste sospechoso (código aparece muy rápido)
    - Frustración (muchos intentos rápidos fallidos)
    - Dependencia de pistas (usa todas sin intentar)
    - Abandono (inactividad prolongada)
    """

    def __init__(self, risk_analyst: AnalistaRiesgoAgent):
        self.ar_ia = risk_analyst
        self.thresholds = {
            "copy_paste_min_chars": 100,
            "copy_paste_max_seconds": 5,
            "frustration_attempts": 5,
            "frustration_window_seconds": 120,
            "hint_dependency_ratio": 0.8,  # 80% de intentos con pista previa
            "abandonment_seconds": 600  # 10 minutos
        }

    async def analyze_attempt(
        self,
        student_id: str,
        exercise_id: str,
        code: str,
        time_since_last: float,
        attempt_history: List[dict]
    ) -> List[Risk]:
        """
        Analiza un intento de código buscando riesgos.

        Returns:
            Lista de riesgos detectados (puede estar vacía)
        """
        risks = []

        # 1. Detección de copy-paste
        if (len(code) > self.thresholds["copy_paste_min_chars"] and
            time_since_last < self.thresholds["copy_paste_max_seconds"]):
            risks.append(Risk(
                risk_type=RiskType.ETHICAL_SUSPICIOUS_CODE,
                risk_level=RiskLevel.MEDIUM,
                dimension=RiskDimension.ETHICAL,
                description=f"Código de {len(code)} caracteres enviado en {time_since_last:.1f}s",
                evidence=[f"code_length={len(code)}", f"time={time_since_last}s"],
                recommendations=[
                    "Verificar si el código fue copiado de fuente externa",
                    "Preguntar al estudiante sobre su proceso de resolución"
                ],
                pedagogical_intervention="Solicitar explicación del código línea por línea"
            ))

        # 2. Detección de frustración
        recent_attempts = [a for a in attempt_history[-5:]
                         if a.get("success") == False]
        if len(recent_attempts) >= self.thresholds["frustration_attempts"]:
            risks.append(Risk(
                risk_type=RiskType.COGNITIVE_OVERLOAD,
                risk_level=RiskLevel.MEDIUM,
                dimension=RiskDimension.COGNITIVE,
                description=f"{len(recent_attempts)} intentos fallidos consecutivos",
                evidence=[f"attempts={len(recent_attempts)}"],
                recommendations=[
                    "Ofrecer pista proactivamente",
                    "Sugerir revisión de conceptos básicos",
                    "Considerar ejercicio más simple"
                ],
                pedagogical_intervention="Activar modo explicativo del tutor"
            ))

        # 3. Dependencia de pistas
        hints_before_attempts = sum(
            1 for a in attempt_history
            if a.get("hint_requested_before", False)
        )
        if len(attempt_history) > 3:
            dependency_ratio = hints_before_attempts / len(attempt_history)
            if dependency_ratio > self.thresholds["hint_dependency_ratio"]:
                risks.append(Risk(
                    risk_type=RiskType.COGNITIVE_DEPENDENCY,
                    risk_level=RiskLevel.LOW,
                    dimension=RiskDimension.COGNITIVE,
                    description=f"Solicita pista antes del {dependency_ratio*100:.0f}% de intentos",
                    evidence=[f"dependency_ratio={dependency_ratio}"],
                    recommendations=[
                        "Reducir nivel de detalle de pistas",
                        "Exigir intento antes de dar pista",
                        "Usar modo socrático para próximas pistas"
                    ],
                    pedagogical_intervention="Cambiar a pistas de nivel 1 (preguntas)"
                ))

        return risks
```

### 4.4 Nuevo Flujo Integrado

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUJO INTEGRADO PROPUESTO                            │
└─────────────────────────────────────────────────────────────────────────┘

1. INICIO DE EJERCICIO
   ┌──────────┐    ┌────────────────┐    ┌───────────────┐
   │Estudiante│───▶│ /training/     │───▶│TrainingGateway│
   │ inicia   │    │   iniciar      │    │               │
   └──────────┘    └────────────────┘    └───────┬───────┘
                                                 │
                          ┌──────────────────────┼──────────────────────┐
                          ▼                      ▼                      ▼
                   ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
                   │ Crear       │       │ TC-N4:      │       │ AR-IA:      │
                   │ Sesión      │       │ trace_start │       │ init_monitor│
                   └─────────────┘       └─────────────┘       └─────────────┘


2. ENVÍO DE CÓDIGO (INTENTO)
   ┌──────────┐    ┌────────────────┐    ┌───────────────┐
   │Estudiante│───▶│ /training/     │───▶│TrainingGateway│
   │ submit   │    │   submit       │    │               │
   └──────────┘    └────────────────┘    └───────┬───────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
            ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
            │ Sandbox:    │              │ TC-N4:      │              │ AR-IA:      │
            │ ejecutar    │              │ trace_      │              │ analyze_    │
            │ tests       │              │ attempt     │              │ attempt     │
            └──────┬──────┘              └─────────────┘              └──────┬──────┘
                   │                                                         │
                   ▼                                                         ▼
            ┌─────────────┐                                           ┌─────────────┐
            │ CodeEvalua- │                                           │ ¿Riesgos?   │
            │ tor "Alex"  │                                           │             │
            └──────┬──────┘                                           └──────┬──────┘
                   │                                                         │
                   │         ┌───────────────────────────────────────────────┘
                   ▼         ▼
            ┌─────────────────────┐
            │ Respuesta enriqueci-│
            │ da con riesgos      │
            │ detectados          │
            └─────────────────────┘


3. SOLICITUD DE PISTA (FLUJO MEJORADO)
   ┌──────────┐    ┌────────────────┐    ┌───────────────┐
   │Estudiante│───▶│ /training/     │───▶│TrainingGateway│
   │ pista    │    │   pista        │    │               │
   └──────────┘    └────────────────┘    └───────┬───────┘
                                                 │
                                                 ▼
                                    ┌─────────────────────────┐
                                    │ HintOrchestrator        │
                                    │                         │
                                    │ 1. ¿Tiene intentos      │
                                    │    previos?             │
                                    │ 2. ¿Cuántas pistas usó? │
                                    │ 3. ¿Cuál es el error?   │
                                    └───────────┬─────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          │                                           │
                          ▼                                           ▼
                  ┌───────────────┐                           ┌───────────────┐
                  │ SI hay context│                           │ NO hay context│
                  │               │                           │               │
                  │ T-IA-Cog      │                           │ Pista estática│
                  │ (Guided Mode) │                           │ de BD         │
                  │               │                           │               │
                  │ Genera pista  │                           │ Retorna texto │
                  │ contextual    │                           │ predefinido   │
                  └───────┬───────┘                           └───────┬───────┘
                          │                                           │
                          └─────────────────┬─────────────────────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ TC-N4:        │
                                    │ trace_hint   │
                                    └───────────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Respuesta con │
                                    │ pista + meta  │
                                    └───────────────┘
```

---

## 5. Cambios en Modelos de Datos

### 5.1 Extensión del Modelo de Sesión de Entrenamiento

```python
# backend/api/routers/training/schemas.py (MODIFICADO)

class SesionEntrenamientoExtended(SesionEntrenamiento):
    """Sesión de entrenamiento con campos de trazabilidad."""

    # Campos existentes heredados...

    # NUEVOS campos para integración
    trace_sequence_id: Optional[str] = None  # ID de secuencia N4
    cognitive_state: Optional[str] = "exploracion"  # Estado cognitivo actual
    risk_alerts: List[dict] = []  # Alertas de riesgo detectadas
    ai_involvement_score: float = 0.0  # Score de dependencia IA acumulado

    # Métricas de proceso
    total_time_thinking: int = 0  # Tiempo sin pedir ayuda (segundos)
    total_time_with_hints: int = 0  # Tiempo después de pedir pista
    hint_effectiveness: Optional[float] = None  # ¿Las pistas ayudaron?
```

### 5.2 Extensión del Modelo de Intento

```python
# backend/database/models/exercise.py (MODIFICADO)

class ExerciseAttemptDB(Base):
    """Intento de ejercicio con campos de trazabilidad."""

    # Campos existentes...

    # NUEVOS campos para integración N4
    trace_id: Optional[str] = Column(String, nullable=True)  # Referencia a traza N4
    cognitive_state: Optional[str] = Column(String, nullable=True)
    hint_requested_before: bool = Column(Boolean, default=False)
    time_since_last_attempt: Optional[float] = Column(Float, nullable=True)

    # Análisis de riesgos
    risk_flags: Optional[dict] = Column(JSON, nullable=True)
```

---

## 6. API: Nuevos Endpoints y Modificaciones

### 6.1 Endpoint de Pista Mejorado

```python
# backend/api/routers/training/endpoints.py (MODIFICADO)

@router.post("/pista/v2", response_model=PistaResponseEnhanced)
async def solicitar_pista_v2(
    request: SolicitarPistaRequest,
    current_user: User = Depends(get_current_user),
    llm_provider = Depends(get_llm_provider),
    db: Session = Depends(get_db)
):
    """
    Solicita pista contextualizada usando T-IA-Cog.

    Mejoras sobre /pista:
    1. Genera pista adaptada al error actual del estudiante
    2. Considera historial de intentos
    3. Registra traza N4
    4. Ajusta nivel de ayuda según dependencia detectada

    Falls back a pista estática si no hay contexto suficiente.
    """
    # Obtener sesión y contexto
    sesion = obtener_sesion(request.session_id)

    # Obtener historial de intentos
    attempt_repo = ExerciseAttemptRepository(db)
    attempts = attempt_repo.get_by_session(request.session_id)

    # Obtener ejercicio actual
    exercise = sesion['ejercicios'][sesion['ejercicio_actual_index']]

    # Crear contexto para T-IA-Cog
    exercise_context = ExerciseContext(
        exercise_id=exercise['id'],
        title=exercise['titulo'],
        mission=exercise['consigna'],
        constraints=exercise.get('restricciones', []),
        learning_objectives=exercise.get('objetivos', [])
    )

    # Determinar si usar T-IA-Cog o fallback
    if len(attempts) > 0 and llm_provider:
        # Usar T-IA-Cog para pista contextualizada
        hint_strategy = TrainingHintsStrategy(llm_provider=llm_provider)

        last_attempt = attempts[-1]
        last_error = last_attempt.stderr if hasattr(last_attempt, 'stderr') else None

        response = await hint_strategy.generate_contextual_hint(
            exercise_context=exercise_context,
            student_attempts=attempts,
            requested_hint_level=request.numero_pista + 1,  # 0-indexed to 1-indexed
            last_error=last_error
        )

        pista_contenido = response.message
        generated_by = "T-IA-Cog"
    else:
        # Fallback a pista estática
        pista_contenido = exercise['pistas'][request.numero_pista]
        generated_by = "static"

    # Registrar traza N4
    trace_collector = TrainingTraceCollector(tc_n4_agent)
    await trace_collector.trace_hint_request(
        session_id=request.session_id,
        student_id=str(current_user.id),
        exercise_id=exercise['id'],
        hint_level=request.numero_pista,
        hints_already_used=sesion.get('pistas_usadas', 0),
        time_since_last_attempt=calculate_time_since_last(attempts)
    )

    # Actualizar sesión
    sesion['pistas_usadas'] = request.numero_pista + 1
    guardar_sesion(request.session_id, sesion)

    return PistaResponseEnhanced(
        contenido=pista_contenido,
        numero=request.numero_pista,
        total_pistas=len(exercise['pistas']),
        generated_by=generated_by,
        cognitive_context={
            "attempts_before_hint": len(attempts),
            "cognitive_state": response.metadata.get("cognitive_state") if hasattr(response, 'metadata') else None,
            "help_level": response.help_level.value if hasattr(response, 'help_level') else None
        }
    )
```

### 6.2 Endpoint de Análisis de Proceso

```python
# backend/api/routers/training/endpoints.py (NUEVO)

@router.get("/sesion/{session_id}/proceso", response_model=ProcesoEntrenamientoReport)
async def obtener_analisis_proceso(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene análisis del proceso de resolución (no solo el resultado).

    Incluye:
    - Camino cognitivo reconstruido
    - Patrones de solicitud de ayuda
    - Riesgos detectados
    - Score de autonomía vs dependencia
    - Recomendaciones pedagógicas
    """
    # Obtener trazas N4 de la sesión
    trace_repo = TraceRepository(db)
    traces = trace_repo.get_by_session(session_id)

    # Reconstruir camino cognitivo
    cognitive_path = [t.cognitive_state for t in traces if t.cognitive_state]

    # Calcular métricas
    total_attempts = sum(1 for t in traces if t.interaction_type == InteractionType.CODE_COMMIT)
    total_hints = sum(1 for t in traces if "hint_request" in str(t.context))

    # Calcular autonomía (intentos sin pista previa / total intentos)
    autonomy_score = calculate_autonomy_score(traces)

    # Obtener riesgos de la sesión
    risk_repo = RiskRepository(db)
    risks = risk_repo.get_by_session(session_id)

    return ProcesoEntrenamientoReport(
        session_id=session_id,
        cognitive_path=cognitive_path,
        total_attempts=total_attempts,
        total_hints_used=total_hints,
        autonomy_score=autonomy_score,
        risks_detected=[r.to_dict() for r in risks],
        recommendations=generate_recommendations(autonomy_score, risks)
    )
```

---

## 7. Medición de la Trazabilidad N4 en Ejercicios

### 7.1 El Problema Fundamental

En el **Modo Tutor**, la trazabilidad N4 es natural porque el estudiante **explicita su razonamiento** en cada mensaje:

```
Estudiante: "Estoy pensando en usar una lista porque necesito agregar
            elementos al final. ¿Es buena idea?"

→ Traza N4: cognitive_state="planificacion",
            cognitive_intent="seleccion_estructura_datos",
            decision_justification="eficiencia en append",
            alternatives_considered=["array", "linked_list"]
```

En el **Entrenador Digital**, el estudiante **no comunica su razonamiento**. Solo envía código:

```
Estudiante: [envía código]

→ Traza actual: code_submitted=True, tests_passed=3/5
→ Traza N4 deseada: ¿Qué estaba pensando? ¿Por qué eligió esa solución?
```

### 7.2 Estrategias de Medición Propuestas

#### Estrategia A: Trazabilidad Inferida (Pasiva)

Reconstruir el estado cognitivo a partir de **señales observables**:

| Señal Observable | Estado Cognitivo Inferido | Confianza |
|------------------|---------------------------|-----------|
| Primer intento, código mínimo | `exploracion` | Alta |
| Múltiples intentos, mismo error | `atascado` | Alta |
| Código crece incrementalmente | `implementacion` | Media |
| Código cambia estructura completa | `cambio_estrategia` | Media |
| Solicita pista | `busqueda_ayuda` | Alta |
| Tests pasan después de pista | `comprension_lograda` | Media |
| Tiempo largo sin actividad | `reflexion` o `abandono` | Baja |

**Limitación**: No captura el **por qué** de las decisiones, solo el **qué**.

#### Estrategia B: Trazabilidad Explícita Opcional (Semi-activa)

Agregar puntos de captura **opcionales pero incentivados**:

```
┌─────────────────────────────────────────────────────────────────┐
│  ANTES DE ENVIAR TU CÓDIGO                                      │
│                                                                 │
│  ¿Qué estrategia estás usando? (opcional, +5 XP)               │
│  ○ Probando una idea rápida                                    │
│  ○ Implementando paso a paso                                   │
│  ○ Corrigiendo un error específico                            │
│  ○ Probando algo diferente porque lo anterior no funcionó     │
│                                                                 │
│  [Enviar sin responder]  [Responder y enviar (+5 XP)]          │
└─────────────────────────────────────────────────────────────────┘
```

**Ventaja**: Captura razonamiento real sin forzar al estudiante.
**Implementación**: Gamificación con XP extra por reflexión.

#### Estrategia C: Reflexión Post-Ejercicio (Activa)

Al completar un ejercicio, solicitar reflexión estructurada:

```python
# Endpoint nuevo: POST /training/reflexion
class ReflexionEjercicio(BaseModel):
    session_id: str
    exercise_id: str

    # Preguntas de reflexión (obligatorias para cerrar ejercicio)
    que_fue_dificil: str  # "¿Qué parte te costó más?"
    como_lo_resolviste: str  # "¿Cómo llegaste a la solución?"
    que_aprendiste: str  # "¿Qué aprendiste de este ejercicio?"

    # Opcional
    alternativas_consideradas: Optional[List[str]] = None
    errores_cometidos: Optional[List[str]] = None
```

**Traza N4 generada:**
```python
CognitiveTrace(
    interaction_type=InteractionType.REFLECTION,
    cognitive_state="reflexion",
    cognitive_intent="metacognicion",
    content=reflexion.como_lo_resolviste,
    decision_justification=reflexion.que_aprendiste,
    alternatives_considered=reflexion.alternativas_consideradas,
    context={
        "difficulty_reported": reflexion.que_fue_dificil,
        "errors_acknowledged": reflexion.errores_cometidos
    }
)
```

### 7.3 Modelo Híbrido Recomendado

Combinar las tres estrategias para máxima captura con mínima fricción:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODELO DE TRAZABILIDAD HÍBRIDO                       │
└─────────────────────────────────────────────────────────────────────────┘

DURANTE EL EJERCICIO (Estrategia A + B):
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   [Intento 1] ────▶ Traza inferida: exploracion                         │
│        │                                                                 │
│        ▼                                                                 │
│   [Intento 2] ────▶ Traza inferida: implementacion                      │
│        │            (código creció 40 líneas)                           │
│        ▼                                                                 │
│   [Pide pista] ───▶ Traza explícita: busqueda_ayuda                     │
│        │            + popup opcional: "¿Por qué la necesitas?"          │
│        ▼                                                                 │
│   [Intento 3] ────▶ Traza inferida: depuracion                          │
│        │            (mismo código, fix puntual)                          │
│        ▼                                                                 │
│   [Intento 4] ────▶ Traza inferida: validacion                          │
│        │            (todos los tests pasan)                              │
│        ▼                                                                 │
│   [ÉXITO] ─────────────────────────────────────────────────────────────│
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

AL COMPLETAR (Estrategia C):
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  ¡Ejercicio completado! 🎉                                      │   │
│   │                                                                 │   │
│   │  Para ganar +20 XP extra, reflexiona brevemente:               │   │
│   │                                                                 │   │
│   │  ¿Qué fue lo más difícil?                                      │   │
│   │  [_______________________________________________]              │   │
│   │                                                                 │   │
│   │  ¿Cómo lo resolviste?                                          │   │
│   │  [_______________________________________________]              │   │
│   │                                                                 │   │
│   │  [Saltar]                    [Reflexionar (+20 XP)]            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ────▶ Traza N4: REFLEXION con justificaciones explícitas              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Métricas de Trazabilidad Resultantes

Con el modelo híbrido, cada sesión de entrenamiento genera:

```python
class TrainingTraceMetrics:
    """Métricas de trazabilidad para una sesión de entrenamiento."""

    # Cobertura de trazabilidad
    total_events: int              # Total de eventos capturados
    inferred_events: int           # Eventos inferidos (Estrategia A)
    explicit_events: int           # Eventos con input del estudiante (B+C)
    coverage_ratio: float          # explicit / total (0.0 - 1.0)

    # Calidad del razonamiento capturado
    has_justifications: bool       # ¿El estudiante explicó decisiones?
    alternatives_count: int        # Alternativas mencionadas
    self_corrections: int          # Autocorrecciones detectadas

    # Camino cognitivo
    cognitive_path: List[str]      # Secuencia de estados
    path_coherence: float          # ¿El camino tiene sentido? (0.0 - 1.0)

    # Comparación con Modo Tutor
    n4_completeness: float         # Qué tan completa es la traza vs Tutor
                                   # Tutor = 1.0, Entrenador ≈ 0.4-0.7
```

### 7.5 Comparación de Niveles de Trazabilidad

| Nivel | Modo Tutor | Entrenador (actual) | Entrenador (propuesto) |
|-------|------------|---------------------|------------------------|
| **N1** (archivos) | ✅ | ✅ | ✅ |
| **N2** (código) | ✅ commits | ✅ intentos | ✅ intentos + diff |
| **N3** (interacciones) | ✅ completo | ⚠️ solo código | ✅ + reflexiones |
| **N4** (cognitivo) | ✅ explícito | ❌ no existe | ⚠️ híbrido (inferido + opcional) |

**Conclusión**: El Entrenador Digital integrado alcanzaría un **N4 parcial** (~60-70% de completitud vs Modo Tutor), suficiente para:
- Detectar patrones de aprendizaje
- Identificar estudiantes en riesgo
- Alimentar reportes institucionales
- Correlacionar con desempeño en modo tutor

Pero **no reemplaza** la trazabilidad completa del Modo Tutor para evaluación profunda del proceso cognitivo.

---

## 8. Plan de Implementación

### 8.1 Fase 1: Infraestructura Base (Sprint 1)

| Tarea | Archivos | Esfuerzo |
|-------|----------|----------|
| Crear `TrainingGateway` | `backend/core/training_gateway.py` | 2 días |
| Crear `TrainingTraceCollector` | `backend/core/training_traceability.py` | 1 día |
| Crear `TrainingRiskMonitor` | `backend/core/training_risk_monitor.py` | 1 día |
| Extender modelos de datos | `schemas.py`, `exercise.py` | 1 día |
| Tests unitarios | `tests/test_training_integration.py` | 2 días |

### 8.2 Fase 2: Integración con T-IA-Cog (Sprint 2)

| Tarea | Archivos | Esfuerzo |
|-------|----------|----------|
| Crear `TrainingHintsStrategy` | `backend/agents/tutor_modes/training_hints.py` | 3 días |
| Modificar endpoint `/pista` | `training/endpoints.py` | 1 día |
| Crear endpoint `/pista/v2` | `training/endpoints.py` | 1 día |
| Prompt templates para ejercicios | `backend/prompts/training_hints.md` | 1 día |
| Tests de integración | `tests/integration/test_training_tutor.py` | 2 días |

### 8.3 Fase 3: Trazabilidad N4 (Sprint 2-3)

| Tarea | Archivos | Esfuerzo |
|-------|----------|----------|
| Integrar trazas en `/iniciar` | `training/endpoints.py` | 0.5 días |
| Integrar trazas en `/submit` | `training/endpoints.py` | 1 día |
| Integrar trazas en `/pista` | `training/endpoints.py` | 0.5 días |
| Crear endpoint `/proceso` | `training/endpoints.py` | 1 día |
| Dashboard de proceso | Frontend | 3 días |

### 8.4 Fase 4: Análisis de Riesgos (Sprint 3)

| Tarea | Archivos | Esfuerzo |
|-------|----------|----------|
| Integrar AR-IA en submit | `training/endpoints.py` | 1 día |
| Alertas en tiempo real | WebSocket + Frontend | 2 días |
| Reportes para docentes | `teacher_tools.py` | 2 días |
| Tests E2E | `tests/e2e/test_training_flow.py` | 2 días |

---

## 9. Compatibilidad y Migración

### 9.1 Estrategia de Compatibilidad

```python
# Mantener endpoints existentes funcionando
@router.post("/pista", response_model=PistaResponse)  # Existente, sin cambios
async def solicitar_pista(...):
    # Comportamiento actual preservado
    pass

@router.post("/pista/v2", response_model=PistaResponseEnhanced)  # Nuevo
async def solicitar_pista_v2(...):
    # Comportamiento mejorado con integración
    pass
```

### 9.2 Feature Flags

```python
# backend/config.py
TRAINING_FEATURES = {
    "use_tutor_hints": os.getenv("TRAINING_USE_TUTOR_HINTS", "false") == "true",
    "enable_n4_tracing": os.getenv("TRAINING_N4_TRACING", "false") == "true",
    "enable_risk_monitor": os.getenv("TRAINING_RISK_MONITOR", "false") == "true",
}
```

### 9.3 Migración Gradual

1. **Semana 1-2**: Desplegar con flags desactivados, solo infraestructura
2. **Semana 3-4**: Activar `enable_n4_tracing` en staging
3. **Semana 5-6**: Activar `use_tutor_hints` en staging
4. **Semana 7-8**: Activar todo en producción con monitoreo

---

## 10. Métricas de Éxito

### 10.1 KPIs Técnicos

| Métrica | Baseline (actual) | Target |
|---------|-------------------|--------|
| Latencia `/pista` | ~50ms | <200ms (con LLM) |
| Cobertura de trazas | 0% | 100% de intentos |
| Detección de copy-paste | 0% | >80% |

### 10.2 KPIs Pedagógicos

| Métrica | Baseline | Target |
|---------|----------|--------|
| Intentos antes de pista | 1.2 | 3.0 |
| Tasa de resolución sin pistas | 15% | 35% |
| Satisfacción con pistas | N/A | >4.0/5.0 |

---

## 11. Conclusión

Esta propuesta de integración resuelve la incoherencia arquitectónica identificada, alineando el Entrenador Digital con la filosofía central del sistema AI-Native: **evaluar procesos, no solo productos**.

Los beneficios clave son:

1. **Consistencia pedagógica**: Las pistas siguen las mismas reglas que el tutor
2. **Visibilidad del proceso**: Se captura cómo el estudiante resuelve ejercicios
3. **Detección temprana**: Los riesgos se identifican durante la práctica
4. **Datos para investigación**: Trazas N4 en ejercicios alimentan análisis institucional
5. **Continuidad**: El progreso en entrenamiento informa al modo tutor

La implementación por fases con feature flags garantiza estabilidad y permite validación incremental.

---

*Documento preparado para revisión del equipo de desarrollo.*
*Última actualización: Diciembre 2025*
