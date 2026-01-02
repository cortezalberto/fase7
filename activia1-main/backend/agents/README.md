# Agentes de IA del Sistema AI-Native MVP

Este directorio contiene los seis agentes de inteligencia artificial especializados que conforman el núcleo del sistema de enseñanza-aprendizaje. Cada agente tiene una responsabilidad específica y todos trabajan de forma coordinada bajo la orquestación del AIGateway.

---

## 1. Visión General del Ecosistema de Agentes

El sistema AI-Native MVP implementa un paradigma de **evaluación basada en procesos cognitivos**, no en productos finales. Esto significa que no importa solo si el código del estudiante funciona, sino **cómo llegó a esa solución**: qué razonamiento siguió, qué alternativas consideró, qué errores cometió y cómo los superó.

Para lograr esto, seis agentes especializados colaboran en tiempo real:

| Agente | Código | Archivo Principal | Responsabilidad |
|--------|--------|-------------------|-----------------|
| Tutor Cognitivo | T-IA-Cog | `tutor.py` | Guiar sin dar respuestas directas |
| Evaluador de Procesos | E-IA-Proc | `evaluator.py` | Evaluar el camino cognitivo, no el código |
| Simuladores Profesionales | S-IA-X | `simulators/` | Simular roles profesionales reales |
| Analista de Riesgos | AR-IA | `risk_analyst.py` | Detectar riesgos en 5 dimensiones |
| Gobernanza | GOV-IA | `governance.py` | Asegurar cumplimiento de políticas |
| Trazabilidad N4 | TC-N4 | `traceability.py` | Capturar evidencia cognitiva completa |

Estos agentes no son simples wrappers de prompts. Cada uno implementa lógica compleja basada en investigación pedagógica y psicología cognitiva, con patrones de diseño sofisticados como Strategy Pattern y detección heurística optimizada.

---

## 2. T-IA-Cog: El Tutor Cognitivo

**Archivos**: `tutor.py`, `tutor_modes/`, `tutor_rules.py`, `tutor_governance.py`

### 2.1 Filosofía Pedagógica

El Tutor Cognitivo representa la filosofía central del sistema: **la IA no debe resolver problemas por el estudiante, sino ayudarlo a desarrollar la capacidad de resolverlos por sí mismo**. Esto se traduce en cuatro reglas pedagógicas inquebrantables:

1. **Nunca código completo**: El tutor jamás proporciona soluciones ejecutables que el estudiante pueda copiar directamente.

2. **Siempre descomponer**: Todo problema se presenta en partes manejables, guiando al estudiante a abordar cada parte antes de integrarlas.

3. **Exigir justificación**: Antes de avanzar, el estudiante debe explicar por qué su aproximación tiene sentido.

4. **Priorizar razonamiento sobre sintaxis**: El entendimiento conceptual siempre precede a los detalles de implementación.

### 2.2 Los Cuatro Modos del Tutor (Strategy Pattern)

El tutor implementa un **patrón Strategy** donde cada modo representa una aproximación pedagógica diferente. La selección del modo es dinámica, basada en el estado cognitivo del estudiante y las políticas de la actividad.

#### Modo Socrático (`tutor_modes/socratic.py`)

El modo más restrictivo y poderoso. El tutor **solo hace preguntas**, nunca proporciona información directamente. La filosofía socrática busca que el estudiante descubra el conocimiento a través de su propio razonamiento.

**Cómo funciona internamente**: Cuando un estudiante pregunta "¿Cómo ordeno una lista?", el modo socrático analiza qué conocimientos previos debería tener el estudiante y formula preguntas que lo guíen a conectar esos conocimientos. En lugar de decir "usa sorted()", pregunta "¿Qué significa para ti que algo esté ordenado?" seguido de "¿Conoces algún criterio para comparar dos elementos?".

El sistema prompt del modo socrático instruye al LLM a:
- Formular preguntas abiertas que requieran reflexión
- Evitar afirmaciones directas
- Construir sobre las respuestas del estudiante
- Nunca revelar la solución, solo el camino hacia ella

#### Modo Explicativo (`tutor_modes/explicative.py`)

Se activa cuando el estudiante está genuinamente atascado (no solo impaciente). Proporciona explicaciones conceptuales, pero siempre respetando las cuatro reglas pedagógicas.

**Cómo funciona internamente**: El modo explicativo construye explicaciones en capas. Primero presenta el concepto abstracto, luego lo relaciona con conocimientos previos del estudiante, después ofrece una analogía o ejemplo no-código, y finalmente invita al estudiante a formular cómo aplicaría el concepto. Nunca termina con código funcional.

El sistema detecta cuándo activar este modo analizando:
- Número de intentos fallidos consecutivos
- Señales de frustración en el lenguaje ("no entiendo nada", "estoy perdido")
- Tiempo excesivo sin progreso

#### Modo Guiado (`tutor_modes/guided.py`)

Implementa un sistema de **pistas graduales con cuatro niveles de especificidad**, cada nivel revelando más información pero manteniendo el desafío cognitivo.

**Los cuatro niveles de pistas**:

| Nivel | Descripción | Ejemplo (para "cómo implementar una cola") |
|-------|-------------|---------------------------------------------|
| 1 | Muy abstracto | "Piensa en estructuras que mantienen un orden específico" |
| 2 | Conceptual | "Considera estructuras FIFO donde el primero en entrar es el primero en salir" |
| 3 | Más concreto | "Una cola necesita operaciones de agregar al final y remover del principio" |
| 4 | Específico | "Podrías usar una lista con append() para agregar y pop(0) para remover, aunque hay opciones más eficientes" |

**Cómo funciona internamente**: El modo guiado mantiene un contador de pistas proporcionadas (`hints_count`) y avanza de nivel solo cuando el estudiante demuestra que no puede progresar con la pista actual. Cada pista viene acompañada de "scaffolding" (andamiaje) que proporciona contexto adicional sin dar la respuesta.

El código implementa esto con la clase `TutorResponse` que incluye:
```python
hints_provided: Optional[List[Dict[str, str]]]  # Lista de pistas dadas
hints_count: int                                 # Cuántas pistas se han dado
previous_hints_count: int                        # Pistas de sesiones anteriores
```

#### Modo Metacognitivo (`tutor_modes/metacognitive.py`)

El modo más sofisticado, diseñado para desarrollar la capacidad del estudiante de **reflexionar sobre su propio proceso de pensamiento**. Las preguntas típicas incluyen:

- "¿Por qué elegiste esta aproximación y no otra?"
- "¿Qué alternativas consideraste antes de decidirte?"
- "Si tuvieras que explicar tu solución a un compañero, ¿qué pasos describirías?"
- "¿Qué parte del problema te resultó más difícil y por qué?"

**Cómo funciona internamente**: El modo metacognitivo analiza las trazas previas del estudiante para identificar momentos de decisión y cambios de estrategia. Luego formula preguntas específicas sobre esos momentos, ayudando al estudiante a hacer explícito su razonamiento implícito.

Este modo es especialmente valioso porque las habilidades metacognitivas son **transferibles a cualquier dominio**: un estudiante que aprende a reflexionar sobre su proceso de resolución de problemas en programación puede aplicar esas mismas habilidades en matemáticas, física o cualquier área.

### 2.3 Sistema de Semáforos Pedagógicos

El tutor implementa un **sistema de semáforos** que determina el nivel de restricción pedagógica:

- **Verde (VERDE)**: Modo normal, el estudiante puede recibir explicaciones y pistas según su necesidad.
- **Amarillo (AMARILLO)**: Modo de advertencia, se detectaron señales de delegación excesiva, las respuestas son más restrictivas.
- **Rojo (ROJO)**: Modo estricto, el estudiante ha intentado delegar repetidamente, solo modo socrático disponible.

El archivo `tutor_governance.py` implementa la lógica del semáforo, analizando patrones como:
- Intentos de obtener código completo
- Dependencia excesiva de respuestas de IA
- Falta de justificaciones propias

### 2.4 Niveles de Andamiaje Cognitivo

El archivo `tutor_rules.py` define los niveles de andamiaje (`CognitiveScaffoldingLevel`):

- **PRINCIPIANTE**: Máximo apoyo, explicaciones detalladas, ejemplos concretos
- **INTERMEDIO**: Apoyo moderado, pistas conceptuales, menos ejemplos
- **AVANZADO**: Mínimo apoyo, preguntas desafiantes, espera autonomía

El nivel se ajusta dinámicamente basándose en el perfil del estudiante y su desempeño en la sesión actual.

---

## 3. E-IA-Proc: El Evaluador de Procesos Cognitivos

**Archivo**: `evaluator.py`

### 3.1 El Cambio de Paradigma

El Evaluador de Procesos representa el cambio más radical respecto a la educación tradicional. En lugar de evaluar **si el código funciona**, evalúa **cómo el estudiante llegó a la solución**. Dos estudiantes pueden producir código idéntico, pero si uno razonó paso a paso mientras el otro copió de una fuente externa, sus procesos de aprendizaje son completamente diferentes.

### 3.2 Las Dimensiones de Evaluación

El evaluador analiza la secuencia completa de trazas cognitivas y genera una evaluación multidimensional:

**Dimensiones Cognitivas**:
- **Descomposición de Problemas**: ¿Dividió el problema en partes manejables?
- **Autorregulación y Metacognición**: ¿Monitoreó y ajustó su proceso?
- **Coherencia Lógica**: ¿Sus decisiones son coherentes con sus justificaciones?

**Métricas de Proceso**:
- **Cambios de estrategia**: Cuántas veces cambió de aproximación (y si fue justificado)
- **Autocorrecciones**: Cuántas veces identificó y corrigió errores propios
- **Crítica a IA**: Cuántas veces cuestionó respuestas del tutor
- **Tasa de justificación**: Qué porcentaje de decisiones fueron justificadas

### 3.3 Cómo Funciona Internamente

El proceso de evaluación sigue estos pasos:

1. **Análisis del Razonamiento** (`_analyze_reasoning`): Reconstruye el "camino cognitivo" que siguió el estudiante, identificando qué fases completó (planificación, exploración, implementación, depuración, validación, reflexión).

2. **Análisis Git** (si disponible): Correlaciona las trazas cognitivas con commits de código para detectar saltos sospechosos (código que aparece sin proceso de razonamiento previo).

3. **Cálculo de Dependencia de IA**: Mide qué porcentaje del razonamiento fue asistido versus autónomo.

4. **Identificación de Riesgos Cognitivos**: Detecta patrones como falta de planificación, ausencia de autocorrecciones, o baja coherencia.

5. **Evaluación por Dimensiones**: Calcula scores 0-10 para cada dimensión de competencia.

6. **Generación de Recomendaciones**: Produce recomendaciones específicas tanto para el estudiante como para el docente.

**Análisis profundo con LLM**: Si hay un proveedor LLM disponible, el método `_analyze_reasoning_deep` usa Gemini Pro para un análisis semántico más sofisticado que puede detectar errores conceptuales y falacias lógicas que el análisis heurístico no capturaría.

### 3.4 El Reporte de Evaluación

El `EvaluationReport` generado incluye:

```python
EvaluationReport(
    reasoning_analysis=...,        # Análisis del camino cognitivo
    git_analysis=...,              # Coherencia con evolución del código
    dimensions=[...],              # Evaluación por dimensión
    ai_dependency_score=0.35,      # 0.0-1.0, cuánta IA usó
    ai_usage_patterns={...},       # Patrones de uso de IA
    reasoning_map={...},           # Mapa visual del razonamiento
    cognitive_risks=[...],         # Riesgos identificados
    overall_competency_level="AUTONOMO",  # Nivel general
    overall_score=7.5,             # Score 0-10
    key_strengths=[...],           # Fortalezas identificadas
    improvement_areas=[...],       # Áreas de mejora
    recommendations_student=[...], # Recomendaciones para estudiante
    recommendations_teacher=[...]  # Recomendaciones para docente
)
```

### 3.5 Retroalimentación Formativa

El método `generate_formative_feedback` produce retroalimentación en markdown, con dos versiones:

- **Para estudiantes** (`_generate_student_feedback`): Lenguaje amigable, emojis, explicaciones de qué significa cada evaluación, recomendaciones accionables.
- **Para docentes** (`_generate_teacher_feedback`): Datos técnicos, métricas detalladas, evidencia específica de las trazas.

---

## 4. S-IA-X: Los Simuladores Profesionales

**Directorio**: `simulators/`

### 4.1 Por Qué Existen los Simuladores

La educación tradicional de programación tiene una carencia crítica: los estudiantes aprenden a escribir código pero no a **trabajar como desarrolladores profesionales**. El desarrollo de software real implica comunicarse con stakeholders no técnicos, participar en ceremonias ágiles, manejar crisis de producción, y tomar decisiones bajo presión.

Los simuladores profesionales abordan esta carencia permitiendo a los estudiantes interactuar con diferentes roles del mundo laboral.

### 4.2 Arquitectura (Strategy Pattern)

Todos los simuladores heredan de `BaseSimulator` (definido en `simulators/base.py`), que proporciona:

- Generación de respuestas con LLM
- Carga de historial de conversación
- Análisis de competencias transversales
- Manejo de errores y fallbacks
- Validación de input

Cada simulador específico define:
- `ROLE_NAME`: Nombre del rol simulado
- `SYSTEM_PROMPT`: Prompt que define la personalidad y comportamiento
- `COMPETENCIES`: Lista de competencias que evalúa
- `EXPECTS`: Lo que el simulador espera del estudiante

### 4.3 Los Once Simuladores Disponibles

#### ProductOwnerSimulator (`product_owner.py`) - PO-IA

Simula un Product Owner que presenta requisitos de manera deliberadamente **ambigua**, como ocurre en la vida real. El estudiante debe hacer las preguntas correctas para clarificar.

**Competencias evaluadas**: comunicación técnica, análisis de requisitos, priorización, justificación de decisiones.

**Ejemplo de interacción**: El PO dice "necesitamos que los usuarios puedan compartir cosas con sus amigos". El estudiante debe preguntar: ¿Qué tipos de cosas? ¿Quiénes son los amigos? ¿Qué significa "compartir"?

#### ScrumMasterSimulator (`scrum_master.py`) - SM-IA

Facilita ceremonias ágiles simuladas. En un daily standup, el estudiante debe comunicar qué hizo, qué hará y qué impedimentos tiene, de manera concisa y relevante.

**Competencias evaluadas**: gestión de tiempo, comunicación de estado, identificación de impedimentos.

#### TechInterviewerSimulator (`tech_interviewer.py`) - IT-IA

Conduce entrevistas técnicas realistas con preguntas de diseño de sistemas y algoritmos. Proporciona feedback constructivo sobre las respuestas.

**Competencias evaluadas**: análisis algorítmico, dominio conceptual, comunicación técnica.

#### IncidentResponderSimulator (`incident_responder.py`) - IR-IA

Presenta situaciones de crisis de producción donde el estudiante debe diagnosticar y resolver problemas bajo presión simulada.

**Competencias evaluadas**: resolución bajo presión, priorización, comunicación de crisis.

#### DevSecOpsSimulator (`devsecops.py`) - DSO-IA

Presenta escenarios de seguridad donde el estudiante debe identificar vulnerabilidades y proponer mitigaciones.

**Competencias evaluadas**: análisis de seguridad, evaluación de riesgos, justificación de decisiones de seguridad.

#### ClientSimulator (`client.py`) - CX-IA

Simula un cliente no técnico que necesita explicaciones claras de conceptos técnicos.

**Competencias evaluadas**: comunicación con stakeholders, traducción técnica-negocio.

#### Simuladores V2 (Enhanced - Sprint 6)

- **SeniorDevSimulator** (SD-IA): Desarrollador senior que revisa código y arquitectura
- **QAEngineerSimulator** (QA-IA): Ingeniero de QA que cuestiona casos de prueba
- **SecurityAuditorSimulator** (SA-IA): Auditor de seguridad más riguroso
- **TechLeadSimulator** (TL-IA): Tech Lead que evalúa decisiones arquitectónicas
- **DemandingClientSimulator** (DC-IA): Cliente exigente (versión más difícil)

### 4.4 Memoria de Conversación

Los simuladores mantienen memoria del historial de conversación mediante la integración con el repositorio de trazas. El método `_load_conversation_history` recupera todas las trazas de la sesión y las convierte en mensajes LLM, permitiendo que el simulador "recuerde" lo que se discutió anteriormente.

### 4.5 Análisis de Competencias

El método `_analyze_competencies` evalúa competencias transversales basándose en heurísticas:

- **Comunicación técnica**: Longitud del mensaje, presencia de términos técnicos, estructura
- **Análisis algorítmico**: Términos como "complejidad", "algoritmo", "estructura"
- **Elicitación de requisitos**: Presencia de preguntas
- **Gestión de tiempo**: Términos de priorización como "urgente", "crítico", "primero"

En producción, estas heurísticas pueden complementarse con análisis LLM más sofisticado.

---

## 5. AR-IA: El Analista de Riesgos

**Archivo**: `risk_analyst.py`

### 5.1 Las Cinco Dimensiones de Riesgo

El Analista de Riesgos monitorea continuamente el comportamiento del estudiante en cinco dimensiones:

#### Riesgos Cognitivos (RC)

- **RC1 - Delegación Total**: El estudiante pide que la IA resuelva todo sin descomponer el problema.
- **RC2 - Dependencia Excesiva**: Más del 70% del razonamiento es delegado a la IA.
- **RC3 - Falta de Justificación**: El estudiante no explica por qué toma decisiones.

**Detección optimizada**: El código usa un `frozenset` (`DELEGATION_SIGNALS`) para búsquedas O(1) de señales de delegación:
```python
DELEGATION_SIGNALS = frozenset([
    "dame el código completo",
    "hacé todo",
    "resolvelo por mí",
    "código entero",
    "implementa todo",
    "haceme"
])
```

#### Riesgos Éticos (RE)

- **RE1 - Código Sospechoso**: Código de más de 100 caracteres enviado en menos de 5 segundos (velocidad humanamente imposible).

**Cómo funciona**: El método `_analyze_ethical_risks` calcula el tiempo entre trazas consecutivas y verifica si el contenido parece código (contiene keywords como `def`, `class`, `function`, etc.). Si tiempo < 5s y código > 100 chars, genera alerta.

#### Riesgos Epistémicos (REp)

- **REp1 - Aceptación Acrítica**: El estudiante acepta respuestas de IA sin cuestionar.

**Optimización BE-OPT-001**: El análisis usa búsqueda binaria (`bisect_right`) para correlacionar respuestas de IA con críticas posteriores, reduciendo complejidad de O(n²) a O(n log n):
```python
critique_timestamps = sorted([t.timestamp for t in traces if t.interaction_type == InteractionType.AI_CRITIQUE])
for t in traces:
    if t.interaction_type == InteractionType.AI_RESPONSE:
        idx = bisect_right(critique_timestamps, t.timestamp)
        if idx >= len(critique_timestamps):
            uncritical_acceptance_count += 1
```

#### Riesgos Técnicos (RT)

- **RT1 - Vulnerabilidades de Seguridad**: Patrones de SQL injection, hardcoded secrets, uso de eval/exec.
- **RT2 - Violación DRY**: Código excesivamente repetitivo.
- **RT3 - Falta de Manejo de Errores**.

**Detección de duplicados optimizada (BE-OPT-004)**: Usa fingerprinting MD5 para detección O(n) en lugar de comparación pairwise O(n²):
```python
fingerprints: Dict[str, List[int]] = {}
for i, submission in enumerate(code_submissions):
    normalized = ' '.join(submission.content.lower().split())
    fp = md5(normalized.encode()).hexdigest()
    fingerprints.setdefault(fp, []).append(i)
```

#### Riesgos de Gobernanza (RG)

- **RG1 - Sesiones Excesivas**: Más de 4 horas continuas.
- **RG2 - Automatización Sospechosa**: Intervalos entre mensajes con varianza muy baja y promedio muy corto.

### 5.2 El Reporte de Riesgos

Cada riesgo detectado incluye:

```python
Risk(
    id="risk_cog_delegation_123",
    risk_type=RiskType.COGNITIVE_DELEGATION,
    risk_level=RiskLevel.HIGH,
    dimension=RiskDimension.COGNITIVE,
    description="Se detectaron 5 intentos de delegación total...",
    evidence=["dame el código completo", "hacé todo"],
    trace_ids=["trace_1", "trace_2"],
    root_cause="Tendencia a delegar la resolución completa a la IA",
    recommendations=["Solicitar descomposición explícita..."],
    pedagogical_intervention="Modo socrático estricto: solo preguntas"
)
```

### 5.3 Análisis de Tendencias

El método `_analyze_trends` compara la primera mitad de la sesión con la segunda para detectar si el estudiante está mejorando o empeorando:

```python
return {
    "delegation_trend": "mejorando" | "empeorando" | "estable",
    "delegation_first_half": 3,
    "delegation_second_half": 1,
}
```

---

## 6. GOV-IA: El Agente de Gobernanza

**Archivo**: `governance.py`

### 6.1 Marcos de Referencia Implementados

El Agente de Gobernanza operacionaliza políticas institucionales basadas en:

- **UNESCO (2021)**: Recomendación sobre la Ética de la IA
- **OECD AI Principles (2019)**: Principios para administración responsable de IA
- **IEEE Ethically Aligned Design (2019)**: Diseño éticamente alineado
- **ISO/IEC 23894:2023**: Gestión de riesgos en IA
- **ISO/IEC 42001:2023**: Sistemas de gestión de IA

### 6.2 Sistema de Semáforos de Cumplimiento

El método `verify_compliance` retorna uno de tres estados:

- **COMPLIANT (Verde)**: La acción puede proceder sin modificaciones.
- **WARNING (Amarillo)**: La acción puede proceder pero con advertencias registradas.
- **VIOLATION (Rojo)**: La acción está bloqueada y debe ser redirigida.

### 6.3 Políticas Configurables

```python
policies = {
    "max_ai_assistance_level": 0.7,      # Máximo 70% de asistencia IA
    "require_explicit_ai_usage": True,   # Exigir declaración de uso de IA
    "block_complete_solutions": True,    # Bloquear solicitudes de soluciones completas
    "require_traceability": True,        # Exigir trazabilidad N4 completa
    "enforce_academic_integrity": True,  # Verificar integridad académica
}
```

Las políticas pueden configurarse a múltiples niveles (institucional, programa, curso, actividad), con políticas más específicas sobrescribiendo las generales.

### 6.4 Sanitización de PII

El método `sanitize_prompt` detecta y redacta Información Personal Identificable antes de enviarla al LLM:

- Emails → `[EMAIL_REDACTED]`
- DNI (argentino) → `[DNI_REDACTED]`
- Teléfonos → `[PHONE_REDACTED]`
- Tarjetas de crédito → `[CARD_REDACTED]`

Esto es crítico cuando se usan proveedores LLM externos donde los datos saldrían de la infraestructura institucional.

### 6.5 Reportes de Auditoría

El método `generate_audit_report` genera reportes para acreditación institucional, incluyendo métricas de cumplimiento, efectividad de políticas y recomendaciones.

---

## 7. TC-N4: El Sistema de Trazabilidad Cognitiva

**Archivo**: `traceability.py`

### 7.1 Los Cuatro Niveles de Trazabilidad

El nombre "N4" se refiere a cuatro niveles de profundidad de trazabilidad:

| Nivel | Nombre | Qué Captura | Ejemplo |
|-------|--------|-------------|---------|
| N1 | Superficial | Entregas finales, archivos | "Entregó archivo main.py" |
| N2 | Técnico | Commits, tests, cambios | "Commit: 'Fix bug in sort'" |
| N3 | Interaccional | Prompts y respuestas | "Preguntó: ¿Cómo ordeno?" |
| N4 | Cognitivo | Razonamiento completo | "Estado: depuración, justificación: elegí quicksort por eficiencia" |

### 7.2 El Modelo CognitiveTrace

Cada interacción se registra con metadatos cognitivos ricos:

```python
CognitiveTrace(
    id="trace_123",
    session_id="session_456",
    timestamp=datetime.now(),
    student_id="student_789",
    activity_id="activity_101",
    trace_level=TraceLevel.N4_COGNITIVO,
    interaction_type=InteractionType.STUDENT_PROMPT,
    content="Elegí usar quicksort porque...",
    cognitive_intent="JUSTIFICATION",
    decision_justification="Quicksort tiene O(n log n) promedio",
    alternatives_considered=["mergesort", "heapsort"],
    context={"state": "implementacion"},
    metadata={"is_design_decision": True}
)
```

### 7.3 Captura de Decisiones de Diseño

El método `capture_design_decision` registra explícitamente cuando el estudiante toma una decisión importante, incluyendo:

- La decisión tomada
- La justificación de por qué
- Las alternativas que consideró y por qué las descartó

### 7.4 Detección de Decisiones Sin Justificar

El método `detect_unjustified_decisions` analiza una sesión y genera alertas si muchas decisiones carecen de justificación:

```python
return {
    "total_decisions": 10,
    "justified_decisions": 4,
    "unjustified_decisions": 6,
    "justification_ratio": 0.4,
    "alert": True,
    "alert_level": "MEDIUM",
    "recommendation": "Menos de la mitad de las decisiones están justificadas..."
}
```

### 7.5 Reconstrucción del Camino Cognitivo

El método `reconstruct_cognitive_path` genera un mapa completo del proceso de razonamiento:

```python
return {
    "sequence_id": "seq_123",
    "student_id": "student_456",
    "duration": 3600,  # segundos
    "total_interactions": 45,
    "cognitive_path": ["exploracion", "planificacion", "implementacion", ...],
    "phases": [{"phase": "planificacion", "start_time": ...}],
    "key_decisions": [{"decision": "...", "justification": "..."}],
    "strategy_changes": [...],
    "ai_dependency_score": 0.35,
    "timeline": [...]
}
```

### 7.6 Análisis con LLM

El método `reconstruct_cognitive_path_async` complementa el análisis heurístico con análisis LLM que puede identificar:

- Fases cognitivas más sutiles
- Estrategias de resolución utilizadas
- Calidad del razonamiento (superficial vs profundo)
- Insights cognitivos

---

## 8. Estructura de Archivos

```
agents/
├── __init__.py               # Exports de todos los agentes
├── README.md                 # Este documento
│
├── tutor.py                  # T-IA-Cog: Tutor principal
├── tutor_rules.py            # Reglas pedagógicas y niveles
├── tutor_governance.py       # Sistema de semáforos
├── tutor_modes/              # Estrategias del tutor
│   ├── __init__.py
│   ├── base.py               # TutorModeStrategy ABC
│   ├── socratic.py           # Modo socrático
│   ├── explicative.py        # Modo explicativo
│   ├── guided.py             # Modo guiado
│   ├── metacognitive.py      # Modo metacognitivo
│   └── factory.py            # TutorModeFactory
│
├── evaluator.py              # E-IA-Proc: Evaluador de procesos
│
├── simulators/               # S-IA-X: Simuladores profesionales
│   ├── __init__.py           # Re-exports y factory
│   ├── base.py               # BaseSimulator ABC
│   ├── factory.py            # SimulatorFactory
│   ├── product_owner.py      # PO-IA
│   ├── scrum_master.py       # SM-IA
│   ├── tech_interviewer.py   # IT-IA
│   ├── incident_responder.py # IR-IA
│   ├── devsecops.py          # DSO-IA
│   └── client.py             # CX-IA
│
├── risk_analyst.py           # AR-IA: Analista de riesgos
├── governance.py             # GOV-IA: Gobernanza institucional
└── traceability.py           # TC-N4: Trazabilidad cognitiva
```

---

## 9. Patrones de Uso

### 9.1 Inicializar un Agente

Todos los agentes siguen un patrón de inicialización similar:

```python
from backend.agents.tutor import TutorAgent
from backend.llm.factory import LLMProviderFactory

# Crear proveedor LLM
llm_provider = LLMProviderFactory.create_from_env()

# Inicializar agente
tutor = TutorAgent(
    llm_provider=llm_provider,
    config={"max_help_level": 0.7}
)
```

### 9.2 Procesar una Interacción

```python
# Tutor
response = await tutor.process_interaction(
    student_prompt="No entiendo cómo funciona la recursión",
    cognitive_state="exploracion",
    conversation_history=[...]
)

# Simulador
simulator = ProductOwnerSimulator(llm_provider=llm_provider)
response = await simulator.interact(
    student_input="Propongo implementar autenticación OAuth2",
    context={"proyecto": "e-commerce"},
    session_id="session_123"
)
```

### 9.3 Evaluar una Sesión

```python
from backend.agents.evaluator import EvaluadorProcesosAgent

evaluator = EvaluadorProcesosAgent(llm_provider=llm_provider)
report = await evaluator.evaluate_process_async(
    trace_sequence=sequence,
    code_evolution=commits
)

# Generar retroalimentación
feedback = evaluator.generate_formative_feedback(
    report,
    student_friendly=True
)
```

### 9.4 Analizar Riesgos

```python
from backend.agents.risk_analyst import AnalistaRiesgoAgent

analyst = AnalistaRiesgoAgent(llm_provider=llm_provider)
risk_report = await analyst.analyze_session_async(
    trace_sequence=sequence,
    context={"activity_type": "examen"}
)

print(f"Nivel de riesgo: {risk_report.overall_assessment}")
for risk in risk_report.risks:
    print(f"- {risk.risk_type}: {risk.description}")
```

---

## 10. Nota sobre el Entrenador Digital

Es importante aclarar que el **Entrenador Digital** (`backend/api/routers/training/` y `backend/services/code_evaluator.py`) **NO utiliza ninguno de los agentes documentados aquí**. Opera de forma completamente independiente con una arquitectura diferente.

### ¿Por qué el Entrenador Digital no usa agentes?

El Entrenador Digital y el sistema de agentes tienen propósitos pedagógicos distintos:

| Característica | Sistema de Agentes | Entrenador Digital |
|----------------|--------------------|--------------------|
| **Flujo** | AIGateway → GOV-IA → CRPE → Agente → LLM | Router → CodeEvaluator → LLM |
| **Propósito** | Desarrollar razonamiento cognitivo | Práctica deliberada de habilidades |
| **Interacción** | Conversacional, abierta | Ejercicios estructurados |
| **Evaluación** | Proceso (cómo razonaste) | Producto (código + calidad) |
| **Trazabilidad** | N4 completa | Solo intentos/resultados |

### Diagrama de flujo comparado

```
MODO TUTOR (usa agentes):
┌─────────┐    ┌───────────┐    ┌─────────┐    ┌──────────┐
│Estudiante│───▶│ AIGateway │───▶│ GOV-IA  │───▶│   CRPE   │
└─────────┘    └───────────┘    └─────────┘    └────┬─────┘
                                                    │
                    ┌───────────────────────────────┘
                    ▼
              ┌──────────┐    ┌─────┐    ┌───────┐    ┌───────┐
              │ T-IA-Cog │───▶│ LLM │───▶│ TC-N4 │───▶│ AR-IA │
              └──────────┘    └─────┘    └───────┘    └───────┘

ENTRENADOR DIGITAL (NO usa agentes):
┌─────────┐    ┌────────┐    ┌───────────────┐    ┌─────┐
│Estudiante│───▶│ Router │───▶│ CodeEvaluator │───▶│ LLM │
└─────────┘    └────────┘    └───────────────┘    └──┬──┘
                                                     │
                    ┌────────────────────────────────┘
                    ▼
              ┌─────────┐    ┌───────────────┐
              │ Sandbox │───▶│ Respuesta     │
              │ (tests) │    │ directa       │
              └─────────┘    └───────────────┘
```

### Justificación de la separación

1. **No hay riesgo de delegación cognitiva**: En ejercicios estructurados con tests definidos, el estudiante debe producir código concreto. No puede "delegar" su razonamiento porque la evaluación es objetiva (pasa o no pasa los tests).

2. **No hay conversación abierta**: El LLM actúa como evaluador ("Alex"), no como tutor. Califica código ya escrito en lugar de guiar un proceso de descubrimiento.

3. **Trazabilidad N4 no es necesaria**: Lo que importa es el resultado final y cuántos intentos tomó, no el camino mental detallado del estudiante durante la resolución.

4. **Latencia optimizada**: Sin pasar por múltiples agentes, la respuesta es más rápida, importante para feedback inmediato en práctica deliberada.

### Cuándo usar cada módulo

- **Agentes (Modo Tutor)**: Problemas abiertos, desarrollo de pensamiento algorítmico, proyectos donde el proceso importa más que el resultado.

- **Entrenador Digital**: Práctica de sintaxis, preparación para exámenes técnicos, reforzar conceptos específicos con feedback inmediato.

Ambos son complementarios: el Entrenador Digital construye habilidades técnicas básicas, los agentes desarrollan capacidades cognitivas de orden superior.

---

## 11. Referencias Bibliográficas

Los agentes implementan conceptos de:

- **Zimmerman (2002)**: Autorregulación del aprendizaje
- **Vygotsky**: Zona de desarrollo próximo y andamiaje
- **Bloom**: Taxonomía de objetivos educativos
- **UNESCO (2021)**: Ética de IA en educación
- **OECD (2019)**: Principios de IA responsable

---

*Última actualización: Diciembre 2025 (Cortez49)*
