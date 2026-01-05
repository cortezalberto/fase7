# Backend del Sistema AI-Native MVP

## 1. Visión General y Propósito del Sistema

El backend de AI-Native MVP constituye el núcleo computacional de un sistema revolucionario diseñado para transformar la enseñanza de programación mediante inteligencia artificial generativa. A diferencia de las plataformas educativas tradicionales que evalúan únicamente el código final producido por los estudiantes, este sistema implementa un paradigma completamente diferente: **evaluación basada en procesos cognitivos**.

El concepto fundamental que sustenta toda la arquitectura es que el verdadero aprendizaje de programación no se mide por si un código compila o pasa tests, sino por el camino mental que el estudiante recorre para llegar a una solución. Un estudiante que copia y pega código de ChatGPT puede producir una solución correcta, pero no ha aprendido nada. En cambio, un estudiante que razona, comete errores, los identifica, formula hipótesis, las valida y gradualmente construye una solución está desarrollando habilidades cognitivas transferibles.

Este backend implementa un ecosistema de **seis agentes de IA especializados** que trabajan coordinadamente para:

1. **Tutorar sin sustituir**: El agente tutor guía al estudiante mediante preguntas socráticas, nunca proporcionando respuestas directas que cortocircuiten el proceso de aprendizaje.

2. **Evaluar procesos, no productos**: El sistema captura cada interacción, cada cambio de estrategia, cada momento de confusión y cada insight, construyendo una "radiografía cognitiva" del proceso de resolución.

3. **Detectar riesgos en tiempo real**: Desde la delegación excesiva a la IA hasta posibles problemas de integridad académica, el sistema identifica y clasifica riesgos en cinco dimensiones.

4. **Simular contextos profesionales**: Los estudiantes pueden interactuar con simuladores de Product Owners, Scrum Masters, entrevistadores técnicos y otros roles para desarrollar habilidades blandas.

5. **Garantizar gobernanza institucional**: Todas las interacciones cumplen con políticas configurables que la institución puede ajustar según sus necesidades pedagógicas.

6. **Mantener trazabilidad completa**: Cada decisión, cada prompt, cada respuesta queda registrada con metadatos cognitivos que permiten reconstruir el camino mental del estudiante.

### 1.1 Estadísticas del Sistema

El backend comprende **más de 265 archivos Python** organizados en una arquitectura modular:

| Componente | Archivos | Clases/Funciones |
|------------|----------|------------------|
| Routers API | 25+ | 161+ endpoints |
| Agentes IA | 6 principales | 15+ estrategias |
| Modelos ORM | 16 | 25+ clases |
| Repositorios | 15 | 24 clases |
| Proveedores LLM | 5 | 5 clases |
| Servicios | 4 | 12+ métodos |
| Excepciones | 1 | 50+ clases |

---

## 2. Arquitectura de Alto Nivel

### 2.1 El Flujo de una Solicitud

Para entender cómo funciona el backend, es útil seguir el camino de una solicitud típica desde que llega hasta que genera una respuesta. Cuando un estudiante envía un mensaje a través del frontend, ese mensaje atraviesa múltiples capas de procesamiento, cada una agregando valor y registrando información:

```
CLIENT REQUEST
    ↓
[API Router] ─────────────────────────────────────────────────────
    │ • Validación JWT
    │ • Validación Pydantic
    │ • Rate Limiting
    ↓
[AI Gateway] (STATELESS ORCHESTRATOR) ─────────────────────────────
    │
    ├─► [CRPE - Motor Cognitivo]
    │     └─ Clasificación de ~137 señales en 10 categorías
    │
    ├─► [GOV-IA - Gobernanza]
    │     └─ Sistema semáforo (Verde/Amarillo/Rojo)
    │
    ├─► [Selección de Agente]
    │     ├─ T-IA-Cog (Tutor) → TutorModeStrategy (6 modos)
    │     ├─ S-IA-X (Simuladores) → SimulatorStrategy (11 roles)
    │     ├─ E-IA-Proc (Evaluador) → Asíncrono
    │     └─ AR-IA (Riesgos) → Async o background
    │
    ├─► [LLM Provider Factory]
    │     └─ Gemini/Ollama/OpenAI/Mistral/Mock
    │
    ├─► [Response Generators] (7 tipos + 4 fallbacks)
    │
    ├─► [TC-N4 Trace Coordinator]
    │     └─ Captura traza 6D cognitiva
    │
    └─► [AR-IA Risk Coordinator]
          └─ Análisis 5D de riesgos
    ↓
[Repositories] ─────────────────────────────────────────────────────
    │ • Persistencia PostgreSQL
    │ • Cache Redis
    │ • Batch loading (N+1 prevention)
    ↓
[Response Serialization]
    │ • UTF8JSONResponse
    │ • APIResponse wrapper
    ↓
CLIENT RESPONSE
```

Primero, la solicitud llega a un **Router de FastAPI** que valida la autenticación JWT y los datos de entrada mediante esquemas Pydantic. Si todo es válido, la solicitud pasa al corazón del sistema: el **AIGateway**.

El AIGateway es el orquestador central y tiene una característica crítica: es completamente **stateless** (sin estado). Esto significa que no mantiene ninguna información en memoria entre solicitudes. Cada vez que llega una solicitud, el gateway lee el estado actual desde PostgreSQL, procesa la solicitud, persiste los cambios y retorna la respuesta. Esta decisión arquitectónica permite ejecutar múltiples instancias del backend detrás de un balanceador de carga sin preocuparse por sincronización de estado.

Dentro del AIGateway, la solicitud primero pasa por el **Motor Cognitivo CRPE** (Cognitive-Reflective Processing Engine), que analiza qué está intentando hacer el estudiante y en qué estado cognitivo se encuentra. ¿Está explorando el problema? ¿Ya tiene un plan y está implementando? ¿Está atascado depurando? Esta clasificación determina cómo responderá el sistema.

Paralelamente, el **Agente de Gobernanza GOV-IA** verifica que la solicitud cumpla con las políticas institucionales. Si un estudiante pide una solución completa ("dame el código entero"), este agente lo detecta y redirige la interacción hacia un modo pedagógico apropiado.

Una vez clasificada y verificada la solicitud, se delega al **agente apropiado** según su naturaleza: el Tutor para consultas de aprendizaje, el Evaluador para solicitudes de evaluación, o alguno de los simuladores profesionales para escenarios de rol.

El agente procesa la solicitud, frecuentemente invocando al **proveedor LLM** (Ollama, Gemini, u otro configurado) para generar respuestas inteligentes. Sin embargo, el LLM nunca interactúa directamente con el estudiante; sus respuestas son filtradas y formateadas por los agentes para asegurar que cumplan con las reglas pedagógicas.

Mientras la respuesta se prepara, dos procesos ocurren en paralelo: el **sistema de trazabilidad TC-N4** registra la interacción con todos sus metadatos cognitivos, y el **Analista de Riesgos AR-IA** examina los patrones de comportamiento buscando señales de alerta.

Finalmente, la respuesta se persiste a PostgreSQL a través de los **Repositorios** y se retorna al cliente. Todo el proceso está diseñado para ser auditable y reproducible.

### 2.2 El Principio de Statelessness

Un aspecto crítico del diseño es que el **AIGateway es completamente stateless**. Esta decisión tiene profundas implicaciones para la arquitectura:

La **escalabilidad horizontal** se vuelve trivial. Podemos ejecutar diez, cien o mil instancias del backend detrás de un balanceador de carga sin ninguna preocupación por sincronización de estado. Cada solicitud puede ser manejada por cualquier instancia.

La **resiliencia** mejora dramáticamente. Si una instancia falla en medio de una solicitud, otra puede continuar procesando solicitudes inmediatamente. No hay estado perdido porque todo está en PostgreSQL.

El **deployment** se simplifica. No hay necesidad de sticky sessions, no hay estado compartido en memoria, no hay complejidades de clustering.

El estado del sistema se divide en dos ubicaciones:
- **PostgreSQL**: Almacena sesiones, trazas cognitivas, evaluaciones, riesgos detectados, usuarios, actividades, contenido académico. Esta es la fuente de verdad del sistema.
- **Redis**: Actúa como cache para respuestas de LLM frecuentes y almacenamiento temporal para sesiones de entrenamiento/examen en progreso.

### 2.3 Thread Safety y Concurrencia

El sistema implementa varios patrones de concurrencia seguros (FIX Cortez70):

**Double-checked locking para singletons**:
```python
_instance = None
_lock = threading.Lock()

def get_instance():
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = create_instance()
    return _instance
```

**Semáforos asyncio para LLM concurrency**:
```python
async def _get_semaphore(self) -> asyncio.Semaphore:
    if self._semaphore is None:
        async with self._semaphore_lock:
            if self._semaphore is None:
                self._semaphore = asyncio.Semaphore(self._max_concurrent)
    return self._semaphore
```

**Pessimistic locking para updates de base de datos**:
```python
def update_with_lock(self, entity_id: str, **kwargs):
    stmt = select(EntityDB).where(EntityDB.id == entity_id).with_for_update()
    entity = self.db.execute(stmt).scalar_one_or_none()
    # Update fields...
    self.db.commit()
```

---

## 3. Los Seis Agentes de IA

El corazón del sistema son seis agentes de IA especializados, cada uno con responsabilidades claramente definidas y comportamientos pedagógicamente fundamentados. Estos agentes no son simples wrappers de prompts; implementan lógica compleja basada en décadas de investigación en pedagogía y psicología cognitiva.

### 3.1 T-IA-Cog: El Tutor Cognitivo

**Ubicación**: [agents/tutor/](agents/tutor/) y [agents/tutor_modes/](agents/tutor_modes/)

El Tutor Cognitivo es quizás el agente más sofisticado del sistema, y su diseño refleja la filosofía central del proyecto. Su responsabilidad fundamental es guiar al estudiante en su proceso de aprendizaje **sin nunca darle la respuesta directa**. Esto puede parecer contraintuitivo en un sistema con acceso a IA generativa, pero es precisamente el punto: la IA no debe ser un atajo hacia la solución, sino un andamiaje que ayuda al estudiante a construir su propio entendimiento.

#### Estructura del Paquete Tutor (Cortez66)

```
agents/tutor/
├── __init__.py      # Re-exports para backward compatibility
├── agent.py         # TutorCognitivoAgent - clase principal (~1,100 líneas)
├── rules.py         # 4 reglas pedagógicas inquebrantables
├── governance.py    # Sistema semáforo (Verde/Amarillo/Rojo)
├── metadata.py      # Metadata N4 para trazabilidad
└── prompts.py       # System prompts por contexto
```

#### Patrón Strategy: 6 Modos Pedagógicos

El tutor implementa un **patrón Strategy** con seis modos pedagógicos, cada uno representando una aproximación diferente a la enseñanza según el contexto y las necesidades del estudiante:

**El Modo Socrático** ([socratic.py](agents/tutor_modes/socratic.py)) es el modo por defecto y más restrictivo. Aquí, el tutor solo puede hacer preguntas. Nunca proporciona información directa, solo guía al estudiante a través de cuestionamientos que lo llevan a descubrir la respuesta por sí mismo. Por ejemplo, si un estudiante pregunta "¿Cómo ordeno una lista en Python?", el tutor socrático no responderá "Usa `sorted(lista)`". En cambio, preguntará: "¿Qué significa para ti que una lista esté ordenada? ¿Qué criterio usarías para comparar dos elementos? ¿Conoces alguna técnica de la vida real para ordenar cosas?". Esta aproximación fuerza al estudiante a articular su entendimiento del problema antes de buscar la solución técnica.

**El Modo Explicativo** ([explicative.py](agents/tutor_modes/explicative.py)) se activa cuando el sistema detecta que el estudiante está genuinamente atascado, no solo impaciente. En este modo, el tutor puede proporcionar explicaciones conceptuales, pero sigue las **4 reglas pedagógicas inquebrantables**:

1. **Nunca código completo**: Jamás proporciona una solución funcional que el estudiante pueda copiar.
2. **Siempre descomponer**: Cualquier problema se presenta en partes manejables.
3. **Exigir justificación**: Antes de avanzar, el estudiante debe explicar por qué la aproximación tiene sentido.
4. **Priorizar razonamiento sobre sintaxis**: El entendimiento conceptual siempre precede a los detalles de implementación.

**El Modo Guiado** ([guided.py](agents/tutor_modes/guided.py)) implementa un sistema de pistas graduales con **cuatro niveles de especificidad**:

| Nivel | Nombre | Descripción | Ejemplo |
|-------|--------|-------------|---------|
| 1 | MINIMO | Muy abstracto | "Piensa en estructuras que mantienen orden entre elementos" |
| 2 | BAJO | Conceptual | "Considera estructuras FIFO que has estudiado" |
| 3 | MEDIO | Más concreto | "Una cola tiene operaciones enqueue y dequeue. ¿Las recuerdas?" |
| 4 | ALTO | Específico | "Podrías usar lista con append() y pop(0). ¿Qué problema podría tener?" |

**El Modo Metacognitivo** ([metacognitive.py](agents/tutor_modes/metacognitive.py)) ayuda al estudiante a reflexionar sobre su propio proceso de pensamiento: "¿Por qué elegiste esa aproximación?", "¿Qué alternativas consideraste?", "¿Qué parte del problema te resultó más difícil?".

**El Modo de Clarificación** (también en metacognitive.py) se activa cuando el sistema detecta que el estudiante necesita aclarar su pregunta antes de poder recibir ayuda efectiva.

**El Modo de Pistas para Entrenamiento** ([training_hints.py](agents/tutor_modes/training_hints.py), añadido en Cortez50) extiende el Modo Guiado específicamente para ejercicios del Entrenador Digital. Construye "prompts implícitos" a partir del contexto del ejercicio, historial de intentos y errores del estudiante para generar pistas contextuales y personalizadas.

#### TutorModeFactory

```python
# agents/tutor_modes/factory.py
class TutorModeFactory:
    """Factory para crear estrategias del tutor."""

    _cache: Dict[str, TutorModeStrategy] = {}

    @classmethod
    def create(cls, mode: str, llm_provider, context: dict = None) -> TutorModeStrategy:
        """Crea o retorna cached strategy."""
        cache_key = f"{mode}_{id(llm_provider)}"
        if cache_key not in cls._cache:
            strategy_class = cls._get_strategy_class(mode)
            cls._cache[cache_key] = strategy_class(llm_provider, context)
        return cls._cache[cache_key]
```

### 3.2 E-IA-Proc: El Evaluador de Procesos

**Ubicación**: [agents/evaluator.py](agents/evaluator.py)

El Evaluador de Procesos representa el cambio de paradigma más radical del sistema respecto a la educación tradicional. En lugar de evaluar si el código funciona, evalúa **cómo el estudiante llegó a la solución**. Esta distinción es fundamental: dos estudiantes pueden producir código idéntico, pero si uno lo razonó paso a paso mientras el otro lo copió de una fuente externa, sus procesos de aprendizaje son completamente diferentes.

#### Dimensiones Evaluadas

| Dimensión | Qué mide | Indicadores |
|-----------|----------|-------------|
| Comprensión conceptual | Entendimiento del problema | Preguntas formuladas, reformulaciones |
| Razonamiento algorítmico | Descomposición del problema | Pasos identificados, casos considerados |
| Pensamiento crítico | Cuestionamiento de suposiciones | Eficiencia analizada, casos límite |
| Metacognición | Reflexión sobre el proceso | Errores identificados, explicaciones |

#### Métricas de Proceso

```python
class ProcessMetrics:
    strategy_changes: int      # Cambios de aproximación
    ai_usage_percentage: float # Porcentaje delegado a IA
    justifications_count: int  # Explicaciones de decisiones
    self_corrections: int      # Autocorrecciones sin ayuda
    time_in_exploration: float # Tiempo explorando vs implementando
    cognitive_transitions: List[str]  # Secuencia de estados cognitivos
```

### 3.3 S-IA-X: Los Simuladores Profesionales

**Ubicación**: [agents/simulators/](agents/simulators/)

Los simuladores profesionales abordan una carencia crítica en la educación tradicional de programación: los estudiantes aprenden a escribir código pero no a trabajar como desarrolladores. El desarrollo de software profesional implica comunicarse con stakeholders no técnicos, participar en ceremonias ágiles, manejar crisis de producción, conducir entrevistas técnicas, y tomar decisiones de seguridad con consecuencias reales.

#### Arquitectura del Paquete

```
agents/simulators/
├── __init__.py              # SimuladorProfesionalAgent (wrapper)
├── base.py                  # BaseSimulator ABC + SimulatorConfig
├── factory.py               # SimuladorFactory
├── product_owner.py         # ProductOwnerSimulator
├── scrum_master.py          # ScrumMasterSimulator
├── tech_interviewer.py      # TechInterviewerSimulator (scores 0-100)
├── incident_responder.py    # IncidentResponderSimulator
├── devsecops.py             # DevSecOpsSimulator
├── client.py                # ClientSimulator
├── senior_dev.py            # SeniorDevSimulator
├── qa_engineer.py           # QAEngineerSimulator
├── security_auditor.py      # SecurityAuditorSimulator
└── tech_lead.py             # TechLeadSimulator
```

#### Los 11 Roles Profesionales

| Simulador | Archivo | Competencias Evaluadas |
|-----------|---------|------------------------|
| **Product Owner** | product_owner.py | Elicitación de requisitos, priorización |
| **Scrum Master** | scrum_master.py | Comunicación ágil, facilitación |
| **Tech Interviewer** | tech_interviewer.py | Algoritmos, diseño de sistemas, comunicación técnica |
| **Incident Responder** | incident_responder.py | Diagnóstico, mitigación, comunicación en crisis |
| **DevSecOps** | devsecops.py | Análisis de vulnerabilidades, remediación |
| **Client** | client.py | Comunicación no técnica, gestión de expectativas |
| **Senior Dev** | senior_dev.py | Code review, mentoring, decisiones técnicas |
| **QA Engineer** | qa_engineer.py | Testing, casos de prueba, calidad |
| **Security Auditor** | security_auditor.py | OWASP, compliance, auditoría |
| **Tech Lead** | tech_lead.py | Arquitectura, estimaciones, trade-offs |
| **Demanding Client** | client.py (variant) | Manejo de clientes difíciles |

#### Prompts Externalizados (Cortez75 Phase 2)

A partir de Cortez75, los prompts de los simuladores se cargan dinámicamente desde archivos `.md`:

```
prompts/
├── prompt_loader.py                      # Carga con LRU caching
├── simulator_product_owner_config.md     # Config Product Owner
├── simulator_tech_interviewer_config.md  # Config Tech Interviewer
├── simulator_incident_responder_config.md
├── simulator_devsecops_config.md
├── simulator_client_config.md
└── simulator_scrum_master_config.md
```

Cada archivo de configuración tiene la estructura:

```markdown
# Simulator Configuration

## SYSTEM_PROMPT
[Prompt del sistema en español]

## COMPETENCIES
- competencia_1
- competencia_2

## EXPECTS
- expectativa_1
- expectativa_2

## FALLBACK
[Mensaje de fallback si LLM no disponible]
```

**Ventajas de la externalización**:
- Editar prompts sin modificar código
- Facilitar traducción a otros idiomas
- Permitir A/B testing de prompts
- Reducir tamaño de archivos Python

### 3.4 AR-IA: El Analista de Riesgos

**Ubicación**: [agents/risk_analyst.py](agents/risk_analyst.py)

El Analista de Riesgos monitorea continuamente el comportamiento del estudiante para detectar patrones problemáticos. Este monitoreo no es intrusivo ni punitivo; su objetivo es identificar estudiantes que podrían beneficiarse de intervención temprana antes de que los problemas se agraven.

#### Las 5 Dimensiones de Riesgo

```
┌─────────────────────────────────────────────────────────────────┐
│                    5 DIMENSIONES DE RIESGO                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │   RC        │ │   RE        │ │   REp       │               │
│  │ COGNITIVO   │ │   ÉTICO     │ │ EPISTÉMICO  │               │
│  ├─────────────┤ ├─────────────┤ ├─────────────┤               │
│  │ • Delegación│ │ • Plagio    │ │ • Aceptación│               │
│  │ • Depend.IA │ │ • Integridad│ │   acrítica  │               │
│  │ • Sin just. │ │ • Fraude    │ │ • Errores   │               │
│  └─────────────┘ └─────────────┘ │   concept.  │               │
│                                   └─────────────┘               │
│         ┌─────────────┐ ┌─────────────┐                        │
│         │   RT        │ │   RG        │                        │
│         │  TÉCNICO    │ │ GOBERNANZA  │                        │
│         ├─────────────┤ ├─────────────┤                        │
│         │ • SQL Inj.  │ │ • Sesión >4h│                        │
│         │ • XSS       │ │ • Scripts   │                        │
│         │ • Hardcoded │ │ • Políticas │                        │
│         │   secrets   │ │   violadas  │                        │
│         │ • DRY viols.│ │             │                        │
│         └─────────────┘ └─────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

#### Optimizaciones de Rendimiento (Cortez41/70)

El análisis de riesgos implementa varias optimizaciones algorítmicas:

**O(1) lookup para señales de delegación**:
```python
# frozenset para búsqueda O(1)
DELEGATION_SIGNALS = frozenset([
    "dame el código", "hacé todo", "resolvelo", "dame la solución",
    "complétame", "terminalo vos", "no entiendo nada"
])
```

**O(n log n) para correlación temporal** (en lugar de O(n²)):
```python
from bisect import bisect_right

# Buscar AI response antes de timestamp
sorted_responses = sorted([r.timestamp for r in ai_responses])
idx = bisect_right(sorted_responses, target_timestamp)
```

**MD5 fingerprinting para detección de duplicados** (O(n)):
```python
from hashlib import md5

def get_code_fingerprint(code: str) -> str:
    normalized = normalize_whitespace(code)
    return md5(normalized.encode()).hexdigest()
```

### 3.5 GOV-IA: El Agente de Gobernanza

**Ubicación**: [agents/governance.py](agents/governance.py)

El Agente de Gobernanza operacionaliza las políticas institucionales, asegurando que todas las interacciones cumplan con las reglas establecidas por la institución educativa.

#### Sistema de Semáforos

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA SEMÁFORO                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   🟢 VERDE (COMPLIANT)                                      │
│   ├─ Acción cumple todas las políticas                      │
│   └─ Puede proceder sin modificaciones                      │
│                                                             │
│   🟡 AMARILLO (WARNING)                                     │
│   ├─ Acción puede proceder con advertencias                 │
│   ├─ Se registra para auditoría                             │
│   └─ Estudiante rozando límites                             │
│                                                             │
│   🔴 ROJO (VIOLATION)                                       │
│   ├─ Acción viola política y está bloqueada                 │
│   ├─ Solicitud redirigida a modo pedagógico                 │
│   └─ Se genera alerta para docente                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Políticas Configurables

```python
policies = {
    # Niveles de asistencia
    "max_ai_assistance_level": 0.7,      # Máximo 70% de asistencia IA
    "require_explicit_ai_usage": True,   # Exigir declaración de uso de IA
    "block_complete_solutions": True,    # Bloquear soluciones completas

    # Trazabilidad
    "require_traceability": True,        # Exigir trazabilidad N4
    "min_trace_level": "n4_cognitivo",   # Nivel mínimo requerido

    # Integridad académica
    "enforce_academic_integrity": True,
    "max_copy_paste_chars": 50,          # Máximo caracteres copiados
    "min_typing_speed_threshold": 5,     # Segundos mínimos entre envíos

    # Sesiones
    "max_session_hours": 4,              # Máximo 4 horas por sesión
    "require_breaks": True,              # Sugerir descansos
}
```

#### Filtro de Privacidad (PII)

El agente detecta y redacta información personal antes de enviarla al LLM:

| Tipo | Patrón | Reemplazo |
|------|--------|-----------|
| Email | `\b[\w.-]+@[\w.-]+\.\w+\b` | `[EMAIL_REDACTED]` |
| DNI | `\b\d{7,8}\b` | `[DNI_REDACTED]` |
| Teléfono | `\b\d{2,4}[-\s]?\d{4}[-\s]?\d{4}\b` | `[PHONE_REDACTED]` |
| Tarjeta | `\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b` | `[CARD_REDACTED]` |

### 3.6 TC-N4: El Sistema de Trazabilidad Cognitiva

**Ubicación**: [agents/traceability.py](agents/traceability.py) y [database/models/trace.py](database/models/trace.py)

La Trazabilidad Cognitiva N4 es el sistema que captura y organiza toda la evidencia del proceso de aprendizaje.

#### Los 4 Niveles de Trazabilidad

```
┌─────────────────────────────────────────────────────────────────┐
│                    NIVELES DE TRAZABILIDAD                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  N1 - SUPERFICIAL                                               │
│  └─ Solo entregas finales y archivos                            │
│     (sistemas tradicionales)                                    │
│                                                                 │
│  N2 - TÉCNICO                                                   │
│  └─ Commits Git, ejecución de tests, cambios en código          │
│     (línea temporal técnica)                                    │
│                                                                 │
│  N3 - INTERACCIONAL                                             │
│  └─ Prompts enviados y respuestas recibidas                     │
│     (qué preguntó y qué obtuvo)                                 │
│                                                                 │
│  N4 - COGNITIVO ★ (Este sistema)                                │
│  └─ Estado cognitivo, intención, justificación,                 │
│     alternativas consideradas, estrategia,                      │
│     nivel de involucramiento IA                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Las 6 Dimensiones de N4

Cada traza cognitiva captura información en 6 dimensiones:

| Dimensión | Campo JSON | Contenido |
|-----------|------------|-----------|
| **Semántica** | `semantic_understanding` | ¿Qué entendió el estudiante? |
| **Algorítmica** | `algorithmic_evolution` | Evolución del código, alternativas |
| **Cognitiva** | `cognitive_reasoning` | Razonamiento explícito, justificaciones |
| **Interaccional** | `interactional_data` | Prompts usados, tipo de intervención IA |
| **Ética/Riesgo** | `ethical_risk_data` | Detección de sesgos, intentos de fraude |
| **Procesual** | `process_data` | Timing, secuencia lógica |

#### Modelo CognitiveTraceDB

```python
class CognitiveTraceDB(Base, BaseModel):
    __tablename__ = "cognitive_traces"

    # Identificación
    session_id = Column(String(36), ForeignKey("sessions.id"))
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=False)

    # Metadata
    trace_level = Column(String(20), default="n4_cognitivo")
    interaction_type = Column(String(50), nullable=False)

    # Contenido
    content = Column(Text, nullable=False)
    context = Column(JSON, default=dict)

    # Análisis cognitivo N4
    cognitive_state = Column(String(50))
    cognitive_intent = Column(String(200))
    decision_justification = Column(Text)
    alternatives_considered = Column(JSON, default=list)
    strategy_type = Column(String(100))
    ai_involvement = Column(Float, default=0.0)  # 0.0 a 1.0

    # 6 Dimensiones (JSONB)
    semantic_understanding = Column(JSONBCompatible)
    algorithmic_evolution = Column(JSONBCompatible)
    cognitive_reasoning = Column(JSONBCompatible)
    interactional_data = Column(JSONBCompatible)
    ethical_risk_data = Column(JSONBCompatible)
    process_data = Column(JSONBCompatible)

    # Jerarquía auto-referencial
    parent_trace_id = Column(String(36), ForeignKey("cognitive_traces.id"))
```

---

## 4. El Entrenador Digital y su Integración con Agentes

**Ubicación**: [api/routers/training/](api/routers/training/), [services/code_evaluator.py](services/code_evaluator.py), y [core/training/](core/training/)

El Entrenador Digital es el módulo de práctica estructurada del sistema, diseñado para que los estudiantes puedan ejercitar sus habilidades de programación de forma guiada y evaluada.

### 4.1 Arquitectura de Integración (Cortez50)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRENADOR DIGITAL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Solicitud → [TrainingGateway] → ¿Qué necesita?                 │
│                                    │                            │
│                    ┌───────────────┼───────────────┐            │
│                    ▼               ▼               ▼            │
│              ¿Trazabilidad?  ¿Análisis de    ¿Pista            │
│                              riesgos?        contextual?        │
│                    │               │               │            │
│                    ▼               ▼               ▼            │
│                 TC-N4         AR-IA         T-IA-Cog            │
│            (TrainingTrace  (TrainingRisk  (TrainingHints       │
│             Collector)      Monitor)       Strategy)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Componentes de Integración

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| **TrainingGateway** | `core/training/gateway.py` | Orquestador central (~700 líneas) |
| **TrainingTraceCollector** | `core/training/traceability.py` | Captura trazas N4 (~500 líneas) |
| **TrainingRiskMonitor** | `core/training/risk_monitor.py` | Detección de riesgos (~600 líneas) |
| **TrainingHintsStrategy** | `agents/tutor_modes/training_hints.py` | Pistas contextuales (~600 líneas) |

### 4.2 Feature Flags

```python
# backend/api/config.py
TRAINING_USE_TUTOR_HINTS = os.getenv("TRAINING_USE_TUTOR_HINTS", "false").lower() == "true"
TRAINING_N4_TRACING = os.getenv("TRAINING_N4_TRACING", "false").lower() == "true"
TRAINING_RISK_MONITOR = os.getenv("TRAINING_RISK_MONITOR", "false").lower() == "true"
```

### 4.3 Estados Cognitivos Inferidos

```
┌─────────────────────────────────────────────────────────────────┐
│                  ESTADOS COGNITIVOS INFERIDOS                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INICIO ──────────► EXPLORACION ──────────► IMPLEMENTACION      │
│    │                     │                        │             │
│    │                     │                        ▼             │
│    │                     │                   DEPURACION         │
│    │                     │                        │             │
│    │                     ▼                        │             │
│    │            CAMBIO_ESTRATEGIA ◄───────────────┘             │
│    │                     │                                      │
│    │                     ▼                                      │
│    └───────────► ESTANCAMIENTO ──────► BUSQUEDA_AYUDA           │
│                         │                                       │
│                         ▼                                       │
│                    VALIDACION ──────────► REFLEXION             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Estado | Señales de Inferencia | Confianza |
|--------|----------------------|-----------|
| `EXPLORACION` | `attempt_number == 1` | Alta |
| `IMPLEMENTACION` | Cambios moderados en código | Media |
| `DEPURACION` | Cambios pequeños (<5 líneas) | Media |
| `CAMBIO_ESTRATEGIA` | Cambio estructural >50% | Alta |
| `BUSQUEDA_AYUDA` | Solicitud explícita de pista | Alta |
| `VALIDACION` | Todos los tests pasan | Alta |
| `ESTANCAMIENTO` | ≥3 intentos fallidos recientes | Alta |
| `REFLEXION` | Contenido explícito de reflexión | Alta |

### 4.4 Tipos de Riesgo en Entrenamiento

| Tipo | Severidad | Detección | Umbral |
|------|-----------|-----------|--------|
| `COPY_PASTE` | HIGH/CRITICAL | Velocidad de escritura | >50 chars/seg |
| `FRUSTRATION` | MEDIUM/HIGH | Intentos fallidos consecutivos | ≥5 en 2 min |
| `HINT_DEPENDENCY` | MEDIUM/HIGH | Pistas sin progreso | ≥3 seguidas |
| `RAPID_SUBMISSION` | LOW | Envío muy rápido | <3 segundos |
| `POSSIBLE_ABANDONMENT` | MEDIUM | Inactividad prolongada | >10 minutos |

### 4.5 Endpoints V1 (Legacy) y V2

**Endpoints V1 (Legacy)** - `routers/training/endpoints.py`:

```
GET  /training/lenguajes          # Estructura: Lenguaje → Lecciones → Ejercicios
GET  /training/materias           # Alias de compatibilidad
POST /training/iniciar            # Iniciar sesión de entrenamiento
POST /training/submit-ejercicio   # Enviar código para evaluación (Cortez56)
POST /training/pista              # Solicitar pista estática
POST /training/corregir-ia        # Corrección asistida por IA (Cortez56)
GET  /training/sesion/{id}/estado # Estado con campos N4 (Cortez56)
DELETE /training/sesion/{id}      # Cancelar sesión
```

**Endpoints V2 (Integración con Agentes)** - `routers/training/integration_endpoints.py`:

```
POST /training/pista/v2           # Pista contextual con T-IA-Cog (4 niveles)
POST /training/reflexion          # Capturar reflexión post-ejercicio
GET  /training/sesion/{id}/proceso # Análisis de proceso cognitivo
POST /training/submit/v2          # Envío con trazabilidad extendida
```

---

## 5. El Motor Cognitivo (CRPE)

**Ubicación**: [core/cognitive_engine.py](core/cognitive_engine.py)

El Motor Cognitivo, también conocido como CRPE (Cognitive-Reflective Processing Engine), es el cerebro analítico del sistema.

### 5.1 Clasificación de ~137 Señales (Cortez64)

El CRPE analiza el input del estudiante y clasifica ~137 señales en 10 categorías:

| Categoría | Señales | Flag resultante |
|-----------|---------|-----------------|
| **Delegación** | "dame el código", "hacé todo" | `is_delegation` |
| **Frustración** | "no entiendo", "esto no funciona" | `is_frustrated` |
| **Validación** | "¿está bien?", "¿es correcto?" | `requests_validation` |
| **Confusión** | "no sé", "estoy perdido" | `is_confused` |
| **Ejemplos** | "dame un ejemplo", "muéstrame" | `requests_example` |
| **Metacognición** | "¿cómo pienso esto?", "mi proceso" | `is_metacognitive` |
| **Preguntas** | "¿qué es?", "¿cómo funciona?" | `is_question` |
| **Explicación** | "explicame", "no entiendo qué" | `requests_explanation` |
| **Optimización** | "más eficiente", "mejorar" | `requests_optimization` |
| **Comparación** | "diferencia entre", "vs" | `requests_comparison` |

### 5.2 Estados Cognitivos

```python
class CognitiveState(str, Enum):
    INICIO = "INICIO"
    EXPLORACION = "EXPLORACION"
    IMPLEMENTACION = "IMPLEMENTACION"
    DEPURACION = "DEPURACION"
    CAMBIO_ESTRATEGIA = "CAMBIO_ESTRATEGIA"
    VALIDACION = "VALIDACION"
    ESTANCAMIENTO = "ESTANCAMIENTO"
    REFLEXION = "REFLEXION"
```

### 5.3 Tipos de Respuesta

El CRPE determina cuál de los **7 tipos de respuesta** generar:

| Tipo | Handler | Cuándo se usa |
|------|---------|---------------|
| `socratic` | `_generate_socratic()` | Modo por defecto, preguntas guía |
| `explicative` | `_generate_explicative()` | Estudiante genuinamente atascado |
| `guided` | `_generate_guided()` | Pistas graduales (4 niveles) |
| `metacognitive` | `_generate_metacognitive()` | Reflexión sobre proceso |
| `empathetic_support` | `_generate_empathetic_support()` | Estudiante frustrado |
| `metacognitive_guidance` | `_generate_metacognitive_guidance()` | "¿Cómo pienso esto?" |
| `example_based` | `_generate_example_based()` | Solicita ejemplos análogos |

Más **4 fallbacks** cuando el LLM no está disponible:
- `_fallback_generic()` - Pista genérica
- `_fallback_clarification()` - Solicitar aclaración
- `_fallback_encouragement()` - Mensaje motivacional
- `_fallback_resources()` - Apuntar a recursos

---

## 6. Integración con Proveedores LLM

**Ubicación**: [llm/](llm/)

El sistema soporta múltiples proveedores de LLM a través de un **patrón Factory**.

### 6.1 Proveedores Disponibles

| Proveedor | Archivo | Características |
|-----------|---------|-----------------|
| **Gemini** | `gemini_provider.py` | API de Google, connection pooling, retry con jitter |
| **Ollama** | `ollama_provider.py` | Local, semáforo de concurrencia, CircuitBreaker (Cortez75) |
| **Mistral** | `mistral_provider.py` | API Mistral AI, streaming |
| **OpenAI** | `openai_provider.py` | GPT-4, GPT-3.5 |
| **Mock** | `mock.py` | Testing, respuestas predefinidas |

### 6.2 Circuit Breaker (Cortez74/75)

```python
# llm/circuit_breaker.py
class CircuitBreaker:
    """Previene cascading failures en llamadas LLM."""

    class State(Enum):
        CLOSED = "closed"      # Normal operation
        OPEN = "open"          # Failures exceeded, rejecting calls
        HALF_OPEN = "half_open" # Testing if service recovered

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[float] = None
```

### 6.3 Retry con Jitter (Cortez75)

```python
# En ollama_provider.py y gemini_provider.py
def _calculate_retry_delay(self, attempt: int) -> float:
    """Calcula delay con exponential backoff + jitter."""
    base_delay = self.retry_delay * (self.retry_backoff ** attempt)
    # Jitter entre 0 y 50% del base delay
    jitter = random.uniform(0, base_delay * 0.5)
    return base_delay + jitter
```

### 6.4 LLM Timeouts (Cortez73)

Todas las llamadas LLM tienen timeout de 30 segundos:

```python
LLM_TIMEOUT_SECONDS = 30.0

response = await asyncio.wait_for(
    self.llm.generate(messages, max_tokens=300, temperature=0.7),
    timeout=LLM_TIMEOUT_SECONDS
)
```

---

## 7. Sistema de Gestión de Contenido Académico (Cortez72)

**Ubicación**: [api/routers/academic_content.py](api/routers/academic_content.py), [database/models/unidad.py](database/models/unidad.py)

### 7.1 Patrón Maestro-Detalle de 3 Niveles

```
┌─────────────────────────────────────────────────────────────────┐
│                 ESTRUCTURA ACADÉMICA                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NIVEL 1: MATERIA (Subject)                                     │
│  ├─ nombre, codigo, descripcion                                 │
│  │                                                              │
│  └─► NIVEL 2: UNIDAD (Unit)                                     │
│      ├─ numero, titulo, objetivos, tiempo_estimado_horas        │
│      │                                                          │
│      └─► NIVEL 3: CONTENIDO                                     │
│          ├─ APUNTES (Notes)                                     │
│          │   └─ titulo, contenido_markdown, recursos_externos   │
│          │                                                      │
│          └─ ARCHIVOS ADJUNTOS (Files)                           │
│              └─ nombre, path, tipo_mime, tamaño_bytes           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Modelos de Base de Datos

```python
class MateriaDB(Base, BaseModel):
    __tablename__ = "materias"
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(50), unique=True)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

class UnidadDB(Base, BaseModel):
    __tablename__ = "unidades"
    materia_id = Column(String(36), ForeignKey("materias.id"))
    numero = Column(Integer, nullable=False)
    titulo = Column(String(255), nullable=False)
    objetivos = Column(Text)
    tiempo_estimado_horas = Column(Float)

    __table_args__ = (
        UniqueConstraint('materia_id', 'numero', name='uq_unidad_materia_numero'),
    )

class ApuntesDB(Base, BaseModel):
    __tablename__ = "apuntes"
    unidad_id = Column(String(36), ForeignKey("unidades.id"))
    titulo = Column(String(255), nullable=False)
    contenido_markdown = Column(Text)
    recursos_externos = Column(JSONBCompatible, default=list)
    orden = Column(Integer, default=0)

class ArchivoAdjuntoDB(Base, BaseModel):
    __tablename__ = "archivos_adjuntos"
    nombre = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    tipo_mime = Column(String(100))
    tamaño_bytes = Column(Integer)
    apuntes_id = Column(String(36), ForeignKey("apuntes.id"), nullable=True)
    unidad_id = Column(String(36), ForeignKey("unidades.id"), nullable=True)

    __table_args__ = (
        # XOR constraint: debe tener exactamente un parent
        CheckConstraint(
            "(apuntes_id IS NOT NULL AND unidad_id IS NULL) OR "
            "(apuntes_id IS NULL AND unidad_id IS NOT NULL)",
            name='ck_archivo_has_exactly_one_parent'
        ),
    )
```

### 7.3 Endpoints Académicos

```
# Materias
GET    /academic/materias           # Listar todas
POST   /academic/materias           # Crear materia
GET    /academic/materias/{id}      # Obtener detalle
PUT    /academic/materias/{id}      # Actualizar
DELETE /academic/materias/{id}      # Soft delete
GET    /academic/materias/{id}/unidades  # Listar unidades

# Unidades
GET    /academic/unidades           # Listar todas
POST   /academic/unidades           # Crear unidad
GET    /academic/unidades/{id}      # Obtener detalle
PUT    /academic/unidades/{id}      # Actualizar
DELETE /academic/unidades/{id}      # Soft delete
GET    /academic/unidades/{id}/apuntes   # Listar apuntes

# Apuntes
GET    /academic/apuntes            # Listar todos
POST   /academic/apuntes            # Crear apuntes
GET    /academic/apuntes/{id}       # Obtener detalle
PUT    /academic/apuntes/{id}       # Actualizar
DELETE /academic/apuntes/{id}       # Soft delete

# Archivos
POST   /files/upload/apuntes/{id}   # Subir a apuntes
POST   /files/upload/unidad/{id}    # Subir a unidad
GET    /files/apuntes/{id}          # Listar archivos de apuntes
GET    /files/unidad/{id}           # Listar archivos de unidad
DELETE /files/{id}                  # Eliminar archivo
GET    /files/download/{path}       # Descargar archivo
```

### 7.4 Servicio de Almacenamiento

```python
# services/file_storage.py

class StorageProvider(ABC):
    """Interfaz abstracta para almacenamiento."""

    @abstractmethod
    async def save(self, file: UploadFile, filename: str) -> str: ...

    @abstractmethod
    async def delete(self, path: str) -> bool: ...

    @abstractmethod
    def exists(self, path: str) -> bool: ...

    @abstractmethod
    def get_path(self, filename: str) -> str: ...

class LocalStorageProvider(StorageProvider):
    """Implementación local con protección path traversal."""

    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile, filename: str) -> str:
        # Validación de seguridad (Cortez74)
        if ".." in filename or filename.startswith("/"):
            raise FileAccessDeniedError("Invalid filename")
        # ...
```

### 7.5 Validaciones de Seguridad (Cortez74)

**Path Traversal Protection**:
```python
def _validate_path(self, path: str) -> bool:
    """Valida que el path no contenga traversal attacks."""
    # Rechazar patrones peligrosos
    if ".." in path:
        return False
    if path.startswith("/") or path.startswith("\\"):
        return False
    if "\x00" in path:  # Null bytes
        return False
    # Verificar que no sea symlink
    full_path = self.base_dir / path
    if full_path.is_symlink():
        return False
    return True
```

**Validación de tipo y tamaño**:
```python
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif", "image/webp"
}
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
```

---

## 8. Integración LTI 1.3 con Moodle (Cortez65)

**Ubicación**: [api/routers/lti.py](api/routers/lti.py) (NOT ENABLED by default)

### 8.1 Flujo de Autenticación OIDC

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO LTI 1.3                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MOODLE                          AI-NATIVE                      │
│    │                                │                           │
│    │ 1. Clic en actividad          │                           │
│    │──────────────────────────────►│                           │
│    │   POST /lti/login             │                           │
│    │   (OIDC initiation)           │                           │
│    │                                │                           │
│    │◄──────────────────────────────│                           │
│    │   Redirect to Moodle auth     │                           │
│    │                                │                           │
│    │ 2. Usuario autoriza           │                           │
│    │──────────────────────────────►│                           │
│    │   POST /lti/launch            │                           │
│    │   (JWT con claims)            │                           │
│    │                                │                           │
│    │                                │ 3. Verifica JWT          │
│    │                                │    Busca actividad        │
│    │                                │    Crea sesión LTI        │
│    │                                │                           │
│    │◄──────────────────────────────│                           │
│    │   Redirect a frontend         │                           │
│    │   con session_id              │                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Matching Automático de Actividades (Cortez65.1)

```python
# ActivityDB fields for Moodle matching
moodle_course_id = Column(String(100), index=True)      # context_id
moodle_course_name = Column(String(255))                # context_title
moodle_course_label = Column(String(100))               # context_label (comisión)
moodle_resource_name = Column(String(255), index=True)  # resource_link_title

# Composite index for efficient matching
Index('idx_activity_moodle_match', 'moodle_course_id', 'moodle_resource_name')
```

**Estrategias de matching**:
1. **Específico**: `moodle_course_id` + `moodle_resource_name`
2. **Fallback**: Solo `moodle_resource_name`

### 8.3 Endpoints LTI

```
POST /lti/login                    # OIDC login initiation
POST /lti/launch                   # LTI launch callback + activity matching
GET  /lti/jwks                     # Public key endpoint (AGS)
POST /lti/deployments              # Create deployment (admin)
GET  /lti/deployments              # List deployments
DELETE /lti/deployments/{id}       # Deactivate deployment
POST /lti/activities/link          # Link activity to Moodle course
DELETE /lti/activities/{id}/link   # Unlink activity
GET  /lti/activities/linked        # List linked activities
```

### 8.4 Configuración

```bash
# .env
LTI_ENABLED=false                    # Master switch (NOT ENABLED by default)
LTI_FRONTEND_URL=http://localhost:3000
LTI_STATE_EXPIRATION_MINUTES=10
LTI_NONCE_EXPIRATION_HOURS=1
LTI_JWKS_CACHE_TTL_SECONDS=3600
```

---

## 9. Contexto Académico sin LTI (Cortez65.2)

Para instituciones que no usan Moodle pero necesitan mostrar información de curso/comisión:

### 9.1 Campos en UserDB

```python
class UserDB(Base, BaseModel):
    # ... campos existentes ...
    course_name = Column(String(255), nullable=True)   # "Programación 1"
    commission = Column(String(100), nullable=True)    # "PROG1-A"
```

### 9.2 Métodos en UserRepository

```python
async def update_academic_context(
    self, user_id: str, course_name: str, commission: str
) -> UserDB: ...

async def get_by_commission(self, commission: str) -> List[UserDB]: ...

async def get_students_by_course(self, course_name: str) -> List[UserDB]: ...
```

---

## 10. Herramientas para Docentes (Teacher Tools)

**Ubicación**: [api/routers/teacher_tools.py](api/routers/teacher_tools.py)

### 10.1 Endpoints de Trazabilidad N4 (Cortez63)

```
GET /teacher/students/{id}/traceability
    # Trazas N4 con distribución de estados cognitivos
    # Paginación: limit, offset
    # Filtro: activity_id

GET /teacher/students/{id}/cognitive-path
    # Timeline de evolución cognitiva
    # Transiciones de estado con timestamps
    # Insights generados automáticamente

GET /teacher/traceability/summary
    # Métricas globales de trazabilidad
    # Clasificación de dependencia IA (high >70%, medium 40-70%, low <40%)
    # Alertas de trazabilidad
```

### 10.2 Otros Endpoints para Docentes

```
GET  /teacher/alerts                      # Listar alertas
POST /teacher/alerts/{id}/acknowledge     # Reconocer alerta
GET  /teacher/students/compare            # Comparar estudiantes por actividad

# Actividades
GET    /activities                        # Listar actividades
POST   /activities                        # Crear actividad
PUT    /activities/{id}                   # Actualizar
DELETE /activities/{id}                   # Eliminar
POST   /activities/{id}/publish           # Publicar
POST   /activities/{id}/archive           # Archivar

# Reportes
POST /reports/cohort                      # Generar reporte de cohorte
GET  /reports/analytics                   # Datos analíticos
POST /reports/export                      # Exportar reporte (JSON/CSV/PDF)
```

---

## 11. Capa de Persistencia

### 11.1 Modelos ORM

**Ubicación**: [database/models/](database/models/) - 16 archivos, 25+ clases

```
database/models/
├── __init__.py           # Re-exports
├── base.py               # Base, BaseModel, JSONBCompatible, utc_now
├── session.py            # SessionDB
├── trace.py              # CognitiveTraceDB, TraceSequenceDB
├── risk.py               # RiskDB
├── evaluation.py         # EvaluationDB
├── user.py               # UserDB
├── activity.py           # ActivityDB
├── student_profile.py    # StudentProfileDB
├── git.py                # GitTraceDB
├── exercise.py           # ExerciseDB, HintDB, TestDB, AttemptDB, RubricDB
├── reports.py            # CourseReportDB, RemediationPlanDB, RiskAlertDB
├── simulation.py         # InterviewSessionDB, IncidentSimulationDB, SimulatorEventDB
├── lti.py                # LTIDeploymentDB, LTISessionDB
├── subject.py            # SubjectDB (inherits BaseModel - FIX Cortez73)
└── unidad.py             # MateriaDB, UnidadDB, ApuntesDB, ArchivoAdjuntoDB
```

### 11.2 Repositorios

**Ubicación**: [database/repositories/](database/repositories/) - 15 archivos, 24 clases

| Archivo | Repositorios |
|---------|--------------|
| `base.py` | BaseRepository (ABC) |
| `session_repository.py` | SessionRepository |
| `trace_repository.py` | TraceRepository |
| `risk_repository.py` | RiskRepository |
| `evaluation_repository.py` | EvaluationRepository |
| `activity_repository.py` | ActivityRepository |
| `user_repository.py` | UserRepository |
| `exercise_repository.py` | ExerciseRepository, HintRepository, TestRepository, AttemptRepository, RubricRepository |
| `git_repository.py` | GitTraceRepository |
| `institutional_repository.py` | CourseReportRepository, RemediationPlanRepository, RiskAlertRepository |
| `simulator_repository.py` | InterviewSessionRepository, IncidentSimulationRepository, SimulatorEventRepository |
| `lti_repository.py` | LTIDeploymentRepository, LTISessionRepository |
| `profile_repository.py` | StudentProfileRepository, SubjectRepository, TraceSequenceRepository |
| `unidad_repository.py` | MateriaRepository, UnidadRepository, ApuntesRepository, ArchivoRepository |

### 11.3 Batch Loading para N+1 Prevention (Cortez70)

```python
# CORRECTO - una sola query para todas las sesiones
traces_by_session = trace_repo.get_by_session_ids(session_ids)

# INCORRECTO - N queries en un loop
for session_id in session_ids:
    traces = trace_repo.get_by_session(session_id)  # N+1 problem!
```

### 11.4 Pessimistic Locking (Cortez70)

```python
def update_with_lock(self, entity_id: str, **kwargs):
    try:
        stmt = select(EntityDB).where(EntityDB.id == entity_id).with_for_update()
        entity = self.db.execute(stmt).scalar_one_or_none()
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            self.db.commit()
        return entity
    except Exception as e:
        self.db.rollback()
        raise DatabaseOperationError(operation="update", details=str(e))
```

---

## 12. API REST

### 12.1 Estructura de Routers

La API está organizada en **25+ routers** que exponen **161+ endpoints** bajo el prefijo `/api/v1`.

```
api/routers/
├── sessions.py              # CRUD sesiones de aprendizaje
├── interactions.py          # Interacción con tutor IA (rate limited)
├── traces.py                # Consultas de trazabilidad N4
├── risks.py                 # Análisis y consulta de riesgos
├── evaluations.py           # Evaluaciones de proceso
├── activities.py            # Gestión de actividades
├── exercises.py             # Ejercicios con rúbricas
├── auth.py                  # Autenticación JWT
├── teacher_tools.py         # Herramientas para docentes
├── cognitive_path.py        # Reconstrucción camino cognitivo
├── cognitive_status.py      # Estado cognitivo de sesión
├── reports.py               # Generación de reportes
├── git_traces.py            # Trazas Git N2
├── git_analytics.py         # Analíticas de Git
├── risk_analysis.py         # Análisis detallado de riesgos
├── traceability.py          # Datos completos de trazabilidad
├── institutional_risks.py   # Riesgos institucionales
├── export.py                # Exportación de datos
├── admin_llm.py             # Administración de LLM
├── metrics.py               # Métricas Prometheus
├── academic_content.py      # Contenido académico (Cortez72)
├── files.py                 # Gestión de archivos (Cortez72)
├── lti.py                   # Integración LTI (Cortez65)
├── training/                # Entrenador Digital
│   ├── endpoints.py         # V1 legacy + Cortez56
│   ├── integration_endpoints.py  # V2 (Cortez50)
│   ├── schemas.py
│   ├── session_storage.py
│   └── helpers.py
├── simulators/              # Simuladores profesionales
│   ├── core.py              # Lista e interacción
│   ├── interview.py         # Entrevista técnica
│   ├── incident.py          # Respuesta a incidentes
│   └── advanced.py          # Simuladores avanzados
└── health/                  # Health checks
    ├── probes.py            # Liveness/readiness
    └── diagnostics.py       # Diagnósticos detallados
```

### 12.2 UTF8JSONResponse (Cortez54)

```python
class UTF8JSONResponse(JSONResponse):
    """JSON response con codificación UTF-8 correcta."""

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,  # 'ó' en lugar de '\u00f3'
            allow_nan=False,
            default=str,
        ).encode("utf-8")
```

### 12.3 Excepciones Personalizadas

**Ubicación**: [api/exceptions.py](api/exceptions.py) - **50+ clases**

```python
# Sesión
class SessionNotFoundError(AINativeAPIException): ...
class SessionAlreadyActiveError(AINativeAPIException): ...
class SessionExpiredError(AINativeAPIException): ...

# Usuario y autenticación
class UserNotFoundError(AINativeAPIException): ...
class UserInactiveError(AINativeAPIException): ...
class RoleRequiredError(AINativeAPIException): ...
class InvalidTokenError(AINativeAPIException): ...
class AuthenticationError(AINativeAPIException): ...

# Trazabilidad
class TraceNotFoundError(AINativeAPIException): ...
class TraceSequenceNotFoundError(AINativeAPIException): ...

# Actividades y ejercicios
class ActivityNotFoundError(AINativeAPIException): ...
class ExerciseNotFoundError(AINativeAPIException): ...

# Riesgos y evaluaciones
class RiskNotFoundError(AINativeAPIException): ...
class EvaluationNotFoundError(AINativeAPIException): ...

# Entrenamiento
class TrainingSessionNotFoundError(AINativeAPIException): ...
class TrainingSessionAccessDeniedError(AINativeAPIException): ...

# Archivos (Cortez72/74)
class FileNotFoundAPIError(AINativeAPIException): ...
class FileUploadError(AINativeAPIException): ...
class FileAccessDeniedError(AINativeAPIException): ...
class FileStorageError(AINativeAPIException): ...

# Reportes
class ReportNotFoundError(AINativeAPIException): ...
class ReportGenerationError(AINativeAPIException): ...

# Simuladores
class SimulatorNotSupportedError(AINativeAPIException): ...
class SimulatorCreationError(AINativeAPIException): ...

# Base de datos
class DatabaseOperationError(AINativeAPIException): ...

# Gobernanza
class GovernanceBlockedError(AINativeAPIException): ...

# LLM
class LLMServiceError(AINativeAPIException): ...
```

### 12.4 Rate Limiting

```python
# Configuración por endpoint
RATE_LIMITS = {
    "global": "100/hour",
    "interactions": "10/minute",
    "health_probes": "100/minute",
    "health_deep": "30/minute",
}
```

### 12.5 Middleware

- **CORS**: Orígenes configurables vía `CORS_ALLOWED_ORIGINS`
- **GZip**: Compresión automática (>1000 bytes)
- **TrustedHost**: Validación de Host header en producción
- **Rate Limiting**: SlowAPI con límites por endpoint

---

## 13. Seguridad

### 13.1 Prompt Injection Detection (Cortez73)

**Ubicación**: [utils/prompt_security.py](utils/prompt_security.py)

```python
# 7 categorías de patrones detectados
PATTERN_CATEGORIES = {
    "OVERRIDE": ["ignore previous", "system:", "disregard instructions"],
    "PERSONA": ["you are now", "pretend you are", "act as"],
    "LEAKING": ["show me your prompt", "reveal your instructions"],
    "JAILBREAK": ["dan mode", "developer mode", "bypass safety"],
    "CODE_INJECTION": ["import os", "exec(", "__import__"],
    "SPANISH_INJECTION": ["ignora las instrucciones", "olvida todo"],
    "BASE64_ENCODED": [base64 patterns]
}

def detect_prompt_injection(prompt: str) -> bool: ...
def get_injection_category(prompt: str) -> Optional[str]: ...
```

### 13.2 Sandbox de Ejecución de Código (Cortez70)

**Ubicación**: [utils/sandbox.py](utils/sandbox.py)

```python
def execute_python_code(
    code: str,
    test_input: str = "",
    timeout_seconds: int = 30
) -> Tuple[str, str, float]:
    """
    Ejecuta código en sandbox seguro.

    NUNCA usar exec()/eval() directamente en el proceso del servidor.
    """
    # Subprocess con timeout
    # Captura stdout/stderr
    # Retorna (output, errors, execution_time)
```

### 13.3 Autenticación JWT

```python
# core/security.py
def encode_access_token(user_id: str, role: str, expires_delta: timedelta) -> str: ...
def decode_access_token(token: str, raise_on_error: bool = False) -> dict: ...

# Excepciones específicas
class TokenExpiredError(Exception): ...
class TokenInvalidError(Exception): ...
```

### 13.4 Roles y Permisos

| Rol | Permisos |
|-----|----------|
| `student` | Sesiones propias, interacciones, ejercicios |
| `teacher` | + Actividades, reportes, alertas, estudiantes de su curso |
| `admin` | + Configuración LLM, exportación, gestión de usuarios |

---

## 14. Observabilidad

### 14.1 Métricas Prometheus

**Ubicación**: [core/metrics.py](core/metrics.py), [api/routers/metrics.py](api/routers/metrics.py)

```python
# Métricas disponibles
api_requests_total = Counter("api_requests_total", "Total API requests", ["endpoint", "method", "status"])
api_request_duration = Histogram("api_request_duration_seconds", "Request duration")
llm_calls_total = Counter("llm_calls_total", "Total LLM calls", ["provider", "model"])
llm_call_duration = Histogram("llm_call_duration_seconds", "LLM call duration")
llm_tokens_total = Counter("llm_tokens_total", "Total tokens used", ["provider", "type"])
active_sessions = Gauge("active_sessions", "Currently active sessions")
risks_detected = Counter("risks_detected_total", "Risks detected", ["type", "severity"])
```

**Endpoint protegido**:
```bash
# Local IPs: sin autenticación
# Remoto: requiere METRICS_API_KEY
curl -H "X-API-Key: $METRICS_API_KEY" http://localhost:8000/metrics
```

### 14.2 Structured Logging

```python
# Formato lazy para evitar formateo innecesario
logger.debug("Processing interaction: %s", interaction_id)  # CORRECTO
logger.debug(f"Processing interaction: {interaction_id}")   # INCORRECTO
```

### 14.3 Health Checks

```
GET /health/live      # Liveness probe (K8s)
GET /health/ready     # Readiness probe (K8s)
GET /health           # Status básico
GET /health/deep      # Diagnóstico completo (DB, Redis, LLM)
```

---

## 15. Configuración y Despliegue

### 15.1 Variables de Entorno

```bash
# Base de datos
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ainative
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=secret

# LLM
LLM_PROVIDER=gemini|ollama|mistral|openai|mock
GEMINI_API_KEY=your-key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
OLLAMA_TIMEOUT=60

# Seguridad
JWT_SECRET_KEY=generate-with-make-generate-secrets
SECRET_KEY=generate-with-make-generate-secrets
METRICS_API_KEY=your-metrics-key
CACHE_SALT=generate-with-make-generate-secrets  # REQUIRED in production

# Entrenador Digital (Cortez50)
TRAINING_USE_TUTOR_HINTS=false
TRAINING_N4_TRACING=false
TRAINING_RISK_MONITOR=false

# LTI (Cortez65 - NOT ENABLED by default)
LTI_ENABLED=false
LTI_FRONTEND_URL=http://localhost:3000

# Archivos (Cortez72)
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=50

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 15.2 Docker

```bash
# Desarrollo
docker-compose up -d

# Con herramientas de debug
docker-compose --profile debug up -d  # + pgAdmin + Redis Commander

# Con monitoreo
docker-compose --profile monitoring up -d  # + Prometheus + Grafana

# Producción
docker-compose -f docker-compose.prod.yml up -d
```

### 15.3 Lifecycle de la Aplicación

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI-Native MVP Backend...")

    # 1. Validar configuración
    validate_configuration()

    # 2. Inicializar base de datos
    await init_database()

    # 3. Seed de datos si necesario
    await seed_exercises_if_empty()

    # 4. Inicializar métricas
    init_metrics()

    # 5. Iniciar cleanup periódico
    start_periodic_cache_cleanup()

    yield

    # Shutdown
    logger.info("Shutting down AI-Native MVP Backend...")

    # 1. Detener cleanup (con timeout 10s - Cortez74)
    await asyncio.wait_for(stop_periodic_cache_cleanup(), timeout=10.0)

    # 2. Cerrar conexiones LLM
    await close_llm_connections()

    # 3. Cerrar pool de base de datos
    await dispose_database_pool()
```

---

## 16. Testing

### 16.1 Estructura

```
tests/
├── conftest.py           # Fixtures compartidos
├── test_agents/          # Tests de agentes
├── test_gateway/         # Tests del orquestador
├── test_repositories/    # Tests de persistencia
├── test_api/             # Tests de endpoints
└── integration/          # Tests de integración
```

### 16.2 Comandos

```bash
pytest tests/ -v --cov=backend            # Todos con cobertura
pytest tests/ -v -m "unit"                # Solo unitarios
pytest tests/ -v -m "integration"         # Solo integración
pytest tests/ -v -m "cognitive"           # Tests cognitivos
pytest tests/ -v -m "agents"              # Tests de agentes
pytest -k "test_tutor" -v                 # Por patrón
pytest tests/test_agents.py::test_tutor_mode -v  # Test específico
```

### 16.3 Markers Disponibles

```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.cognitive
@pytest.mark.agents
@pytest.mark.models
@pytest.mark.gateway
@pytest.mark.slow
@pytest.mark.asyncio
```

### 16.4 Cobertura Requerida

- **Global**: 70% mínimo
- **Paths críticos** (`ai_gateway.py`, `cognitive_engine.py`, agentes): 90%+

---

## 17. Patrones de Diseño

| Patrón | Uso | Archivos |
|--------|-----|----------|
| **Factory** | Creación de LLM providers, simuladores, modos tutor | `llm/factory.py`, `simulators/factory.py`, `tutor_modes/factory.py` |
| **Strategy** | Modos del tutor, roles de simuladores | `tutor_modes/`, `simulators/` |
| **Repository** | Abstracción de acceso a datos | `database/repositories/` |
| **Singleton** | Instancias únicas (métricas, cache) | `core/metrics.py`, `core/cache.py` |
| **Gateway** | Orquestación de entrenamiento | `core/training/gateway.py` |
| **Circuit Breaker** | Protección contra fallos LLM | `llm/circuit_breaker.py` |
| **Observer** | Eventos y métricas | Background tasks, Prometheus |

---

## 18. Estructura de Directorios

```
backend/
├── __init__.py              # Versión y metadata
├── __main__.py              # Entry point: python -m backend
├── cli.py                   # CLI commands
│
├── agents/                  # Los 6 agentes de IA
│   ├── tutor/               # T-IA-Cog (Cortez66)
│   │   ├── agent.py         # TutorCognitivoAgent (~1,100 líneas)
│   │   ├── rules.py         # 4 reglas pedagógicas
│   │   ├── governance.py    # Sistema semáforo
│   │   ├── metadata.py      # Metadata N4
│   │   └── prompts.py       # System prompts
│   ├── tutor_modes/         # Estrategias del tutor (6 modos)
│   │   ├── base.py          # TutorModeStrategy ABC
│   │   ├── socratic.py
│   │   ├── explicative.py
│   │   ├── guided.py        # 4 niveles
│   │   ├── metacognitive.py # + clarificación
│   │   ├── training_hints.py # Cortez50
│   │   └── factory.py
│   ├── evaluator.py         # E-IA-Proc
│   ├── risk_analyst.py      # AR-IA
│   ├── governance.py        # GOV-IA
│   ├── traceability.py      # TC-N4
│   ├── git_integration.py   # Integración Git
│   └── simulators/          # S-IA-X (11 roles)
│       ├── base.py          # BaseSimulator ABC
│       ├── factory.py
│       ├── product_owner.py
│       ├── scrum_master.py
│       ├── tech_interviewer.py
│       ├── incident_responder.py
│       ├── devsecops.py
│       ├── client.py
│       └── ...
│
├── core/                    # Núcleo del sistema
│   ├── ai_gateway.py        # Orquestador central (~2,000 líneas)
│   ├── cognitive_engine.py  # CRPE (~500 líneas)
│   ├── cache.py             # Cache con TTL
│   ├── redis_cache.py       # Distributed cache
│   ├── rate_limiting.py     # Rate limiter
│   ├── metrics.py           # Prometheus metrics
│   ├── security.py          # JWT encode/decode
│   ├── constants.py         # Constantes globales
│   ├── structured_logging.py
│   ├── training/            # Integración entrenador (Cortez50)
│   │   ├── gateway.py       # TrainingGateway
│   │   ├── traceability.py  # TrainingTraceCollector
│   │   └── risk_monitor.py  # TrainingRiskMonitor
│   └── gateway/             # Coordinadores extraídos (Cortez66)
│       ├── protocols.py     # Protocol definitions
│       ├── fallback_responses.py
│       ├── response_generators.py
│       ├── trace_coordinator.py
│       └── risk_coordinator.py
│
├── database/                # Capa de persistencia
│   ├── config.py            # Database configuration
│   ├── session.py           # Session management
│   ├── background_session.py
│   ├── transaction.py       # Transaction handling
│   ├── models/              # ORM models (16 archivos)
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── trace.py
│   │   ├── user.py
│   │   ├── activity.py
│   │   ├── exercise.py
│   │   ├── unidad.py        # Cortez72
│   │   └── ...
│   ├── repositories/        # Data access (15 archivos)
│   │   ├── base.py
│   │   ├── session_repository.py
│   │   ├── trace_repository.py
│   │   ├── unidad_repository.py  # Cortez72
│   │   └── ...
│   └── migrations/          # Database migrations
│
├── llm/                     # Proveedores LLM
│   ├── base.py              # Abstract interface
│   ├── factory.py           # LLMProviderFactory
│   ├── gemini_provider.py
│   ├── ollama_provider.py
│   ├── mistral_provider.py
│   ├── openai_provider.py
│   ├── mock.py
│   └── circuit_breaker.py   # Cortez74
│
├── api/                     # Capa REST
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Configuration
│   ├── deps.py              # Dependencies
│   ├── exceptions.py        # 50+ custom exceptions
│   ├── startup_validation.py
│   ├── routers/             # 25+ routers
│   │   ├── sessions.py
│   │   ├── interactions.py
│   │   ├── training/
│   │   ├── simulators/
│   │   ├── health/
│   │   ├── academic_content.py
│   │   ├── files.py
│   │   ├── lti.py
│   │   └── ...
│   ├── schemas/             # Pydantic models
│   │   ├── common.py
│   │   ├── session.py
│   │   ├── training.py
│   │   └── ...
│   ├── middleware/
│   └── monitoring/
│
├── prompts/                 # Prompts externalizados (Cortez75)
│   ├── prompt_loader.py
│   ├── simulator_product_owner_config.md
│   ├── simulator_tech_interviewer_config.md
│   └── ...
│
├── services/                # Business logic
│   ├── code_evaluator.py    # Evaluador de código "Alex"
│   ├── course_report_generator.py
│   ├── institutional_risk_manager.py
│   └── file_storage.py      # Cortez72
│
├── utils/                   # Utilities
│   ├── sandbox.py           # Secure code execution
│   └── prompt_security.py   # Injection detection (Cortez73)
│
├── scripts/                 # Utility scripts
│   ├── init_db.py
│   ├── seed_dev.py
│   ├── seed_exercises.py
│   └── seed_programacion1.py  # Cortez72
│
└── tests/                   # Test suite
```

---

## 19. Historial de Auditorías

El backend ha pasado por **75+ auditorías** de código:

| Auditoría | Fecha | Foco | Health Score |
|-----------|-------|------|--------------|
| **Cortez75** | Ene 2026 | Architectural Remediation (5 phases) | 9.5 → 9.8 |
| **Cortez74** | Ene 2026 | Deep Remediation (11 CRIT/HIGH) | 9.2 → 9.5 |
| **Cortez73** | Ene 2026 | Comprehensive Audit (65 issues) | 8.8 → 9.2 |
| **Cortez72** | Ene 2026 | Academic Content Management | - |
| **Cortez71** | Ene 2026 | Frontend Audit (27/27 fixed) | 7.5 → 9.2 |
| **Cortez70** | Ene 2026 | Concurrency & Security (14 CRIT) | 8.2 → 8.8 |
| **Cortez69** | Ene 2026 | Inconsistency Audit (238 issues) | 6.8 → 8.2 |
| **Cortez68** | Ene 2026 | Backend Audit (113 issues) | 7.5 → 9.0 |
| **Cortez66** | Ene 2026 | Architecture (5 phases) | - |
| **Cortez65** | Ene 2026 | LTI 1.3 Integration | - |
| **Cortez64** | Ene 2026 | CRPE Signal Expansion | - |
| **Cortez63** | Ene 2026 | N4 Traceability for Teachers | - |
| **Cortez50** | Dic 2025 | Digital Trainer + Agents | - |

### Correcciones Destacadas por Auditoría

**Cortez75 (Phase 1-5)**:
- Pessimistic locking en repositorios
- CircuitBreaker en OllamaProvider
- Prompts externalizados a `.md`
- Retry con jitter
- Schema consolidation (deprecated duplicates)

**Cortez74**:
- Path traversal protection
- SubjectDB inherits BaseModel
- Circuit breaker pattern
- Race condition fixes
- Bounded task registry

**Cortez73**:
- Centralized prompt security
- LLM timeouts (30s)
- Model inheritance fixes
- CheckConstraints for enums

**Cortez70**:
- Thread safety (double-checked locking)
- Async semaphore initialization
- Database pessimistic locking
- Sandbox code execution
- N+1 query prevention

---

## 20. Comandos de Referencia

```bash
# Navegación y setup
cd activia1-main
docker-compose up -d

# Desarrollo
python -m backend                         # Iniciar servidor
docker-compose logs -f api                # Ver logs

# Testing
pytest tests/ -v --cov=backend            # Tests con cobertura
pytest tests/ -v -m "unit"                # Solo unitarios

# Base de datos
python -m backend.database.migrations.add_n4_dimensions
python -m backend.database.migrations.add_cortez_audit_fixes
python -m backend.database.migrations.add_user_academic_context
python -m backend.database.migrations.add_unidades_apuntes

# Health check
curl http://localhost:8000/api/v1/health

# Generar secretos
make generate-secrets
```

---

## 21. Conclusión

El backend de AI-Native MVP representa una aproximación innovadora a la enseñanza de programación que prioriza el proceso de aprendizaje sobre el producto final. A través de sus **seis agentes de IA especializados**, el sistema proporciona:

- **Tutorización adaptativa** con 6 modos pedagógicos
- **Evaluación de procesos cognitivos** con trazabilidad N4 de 6 dimensiones
- **Simulación de contextos profesionales** con 11 roles
- **Análisis de riesgos multidimensional** en 5 dimensiones
- **Gobernanza institucional** con sistema de semáforos
- **Gestión de contenido académico** con patrón Maestro-Detalle de 3 niveles
- **Integración LTI 1.3** para Moodle (opcional)

La arquitectura **stateless** del gateway central, combinada con el **Repository Pattern** para persistencia, el **Factory Pattern** para integración con LLMs, y el **Strategy Pattern** para modos de tutor y simuladores, permite un sistema escalable, mantenible y extensible.

Las **75+ auditorías de código** han refinado tanto la calidad del código como los patrones arquitectónicos empleados, resultando en un sistema robusto con:
- **50+ excepciones personalizadas** para manejo consistente de errores
- **Optimizaciones algorítmicas** (O(n²) → O(n log n))
- **Thread safety** con double-checked locking
- **Circuit breaker** para tolerancia a fallos LLM
- **Prompt injection detection** centralizado

---

*Última actualización: Enero 2026 (Cortez75 - Backend Architectural Remediation COMPLETE)*

*Health Score: 9.8/10*
