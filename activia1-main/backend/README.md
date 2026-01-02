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

---

## 2. Arquitectura de Alto Nivel

### 2.1 El Flujo de una Solicitud

Para entender cómo funciona el backend, es útil seguir el camino de una solicitud típica desde que llega hasta que genera una respuesta. Cuando un estudiante envía un mensaje a través del frontend, ese mensaje atraviesa múltiples capas de procesamiento, cada una agregando valor y registrando información:

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
- **PostgreSQL**: Almacena sesiones, trazas cognitivas, evaluaciones, riesgos detectados, usuarios y actividades. Esta es la fuente de verdad del sistema.
- **Redis**: Actúa como cache para respuestas de LLM frecuentes y almacenamiento temporal para sesiones de entrenamiento/examen en progreso.

---

## 3. Los Seis Agentes de IA

El corazón del sistema son seis agentes de IA especializados, cada uno con responsabilidades claramente definidas y comportamientos pedagógicamente fundamentados. Estos agentes no son simples wrappers de prompts; implementan lógica compleja basada en décadas de investigación en pedagogía y psicología cognitiva.

### 3.1 T-IA-Cog: El Tutor Cognitivo

**Ubicación**: [tutor.py](agents/tutor.py) y [tutor_modes/](agents/tutor_modes/)

El Tutor Cognitivo es quizás el agente más sofisticado del sistema, y su diseño refleja la filosofía central del proyecto. Su responsabilidad fundamental es guiar al estudiante en su proceso de aprendizaje **sin nunca darle la respuesta directa**. Esto puede parecer contraintuitivo en un sistema con acceso a IA generativa, pero es precisamente el punto: la IA no debe ser un atajo hacia la solución, sino un andamiaje que ayuda al estudiante a construir su propio entendimiento.

El tutor implementa un **patrón Strategy** con seis modos pedagógicos, cada uno representando una aproximación diferente a la enseñanza según el contexto y las necesidades del estudiante:

**El Modo Socrático** ([socratic.py](agents/tutor_modes/socratic.py)) es el modo por defecto y más restrictivo. Aquí, el tutor solo puede hacer preguntas. Nunca proporciona información directa, solo guía al estudiante a través de cuestionamientos que lo llevan a descubrir la respuesta por sí mismo. Por ejemplo, si un estudiante pregunta "¿Cómo ordeno una lista en Python?", el tutor socrático no responderá "Usa `sorted(lista)`". En cambio, preguntará: "¿Qué significa para ti que una lista esté ordenada? ¿Qué criterio usarías para comparar dos elementos? ¿Conoces alguna técnica de la vida real para ordenar cosas?". Esta aproximación fuerza al estudiante a articular su entendimiento del problema antes de buscar la solución técnica. El modo socrático es especialmente efectivo cuando el estudiante tiene los conocimientos necesarios pero no los ha conectado correctamente.

**El Modo Explicativo** ([explicative.py](agents/tutor_modes/explicative.py)) se activa cuando el sistema detecta que el estudiante está genuinamente atascado, no solo impaciente. En este modo, el tutor puede proporcionar explicaciones conceptuales, pero sigue las "4 reglas pedagógicas inquebrantables" que garantizan que la explicación promueva el aprendizaje en lugar de reemplazarlo:

1. **Nunca código completo**: Jamás proporciona una solución funcional que el estudiante pueda copiar. Puede mostrar fragmentos aislados para ilustrar conceptos, pero nunca una solución ejecutable.

2. **Siempre descomponer**: Cualquier problema se presenta en partes manejables. En lugar de explicar "cómo implementar una cola", explica primero "qué operaciones necesita una cola", luego "cómo almacenar los elementos", luego "cómo implementar enqueue y dequeue por separado".

3. **Exigir justificación**: Antes de avanzar a la siguiente parte, el estudiante debe explicar por qué la aproximación actual tiene sentido. "Has dicho que usarás una lista. ¿Por qué crees que una lista es apropiada aquí?"

4. **Priorizar razonamiento sobre sintaxis**: El entendimiento conceptual siempre precede a los detalles de implementación. Primero "¿qué debe hacer este código?", después "¿cómo escribirlo en Python?".

**El Modo Guiado** ([guided.py](agents/tutor_modes/guided.py)) implementa un sistema de pistas graduales con cuatro niveles de especificidad. Este modo es especialmente útil cuando el estudiante necesita un pequeño empujón pero no una explicación completa:

- **Nivel 1 (muy abstracto)**: "Piensa en estructuras que mantienen un orden específico entre sus elementos"
- **Nivel 2 (conceptual)**: "Considera las estructuras de datos que has estudiado donde el primer elemento en entrar es el primero en salir"
- **Nivel 3 (más concreto)**: "Una cola es una estructura FIFO. ¿Recuerdas qué operaciones fundamentales tiene?"
- **Nivel 4 (específico)**: "Podrías usar una lista donde `append()` agrega al final y `pop(0)` remueve del principio. ¿Qué problema podría tener esta aproximación?"

Cada pista viene acompañada de "scaffolding" (andamiaje) que proporciona contexto sin dar la respuesta, y el sistema avanza de nivel solo cuando el estudiante demuestra que no puede progresar con la pista actual.

**El Modo Metacognitivo** ([metacognitive.py](agents/tutor_modes/metacognitive.py)) es el más sofisticado y ayuda al estudiante a reflexionar sobre su propio proceso de pensamiento. Las preguntas características de este modo incluyen: "¿Por qué elegiste esa aproximación y no otra?", "¿Qué alternativas consideraste antes de decidirte por esta?", "Si tuvieras que explicar tu solución a un compañero, ¿qué pasos le describirías?", "¿Qué parte del problema te resultó más difícil y por qué?". Este modo es especialmente valioso porque desarrolla habilidades de autorregulación del aprendizaje que son transferibles a cualquier dominio.

**El Modo de Pistas para Entrenamiento** ([training_hints.py](agents/tutor_modes/training_hints.py), añadido en Cortez50) extiende el Modo Guiado específicamente para ejercicios del Entrenador Digital. Este modo construye "prompts implícitos" a partir del contexto del ejercicio, historial de intentos y errores del estudiante para generar pistas contextuales y personalizadas. Se detalla completamente en la Sección 4.

**El Modo de Clarificación** (también en [metacognitive.py](agents/tutor_modes/metacognitive.py)) se activa cuando el sistema detecta que el estudiante necesita aclarar su pregunta o intención antes de poder proporcionar ayuda efectiva.

La selección del modo es dinámica y depende del estado cognitivo del estudiante (determinado por el motor CRPE), su historial de interacciones en la sesión actual, y las políticas configuradas para la actividad específica.

### 3.2 E-IA-Proc: El Evaluador de Procesos

**Ubicación**: [evaluator.py](agents/evaluator.py)

El Evaluador de Procesos representa el cambio de paradigma más radical del sistema respecto a la educación tradicional. En lugar de evaluar si el código funciona, evalúa **cómo el estudiante llegó a la solución**. Esta distinción es fundamental: dos estudiantes pueden producir código idéntico, pero si uno lo razonó paso a paso mientras el otro lo copió de una fuente externa, sus procesos de aprendizaje son completamente diferentes.

El evaluador analiza la secuencia completa de trazas cognitivas de una sesión y genera una evaluación multidimensional. Para entender qué evalúa, considera este ejemplo: un estudiante trabaja en un problema de ordenamiento.

El evaluador examina las **dimensiones cognitivas** del proceso:

La **comprensión conceptual** se mide por las preguntas que hizo el estudiante y cómo formuló el problema. ¿Demostró entender qué significa "ordenar"? ¿Consideró diferentes criterios de ordenamiento?

El **razonamiento algorítmico** se evalúa por cómo descompuso el problema. ¿Identificó los pasos necesarios? ¿Consideró casos base y casos recursivos si aplicaba?

El **pensamiento crítico** se refleja en si el estudiante cuestionó suposiciones. ¿Se preguntó sobre la eficiencia? ¿Consideró casos límite como listas vacías o con un solo elemento?

La **metacognición** se observa en la reflexión del estudiante sobre su proceso. ¿Identificó dónde se equivocó? ¿Pudo explicar por qué una aproximación funcionó mejor que otra?

Además, el evaluador calcula **métricas de proceso**:

Los **cambios de estrategia** cuentan cuántas veces el estudiante cambió de aproximación. Un estudiante que cambia de estrategia porque identificó un problema con su aproximación anterior demuestra pensamiento crítico. Uno que cambia repetidamente sin justificación puede estar adivinando.

El **uso de IA** mide qué porcentaje del razonamiento fue delegado al tutor. Un uso moderado con preguntas específicas es saludable; pedir que el tutor resuelva todo indica delegación cognitiva.

Las **justificaciones** cuentan con qué frecuencia el estudiante explicó sus decisiones, ya sea espontáneamente o cuando el tutor lo solicitó.

Las **autocorrecciones** registran cuántas veces el estudiante identificó y corrigió sus propios errores sin que el tutor señalara el problema.

La evaluación resultante no es una nota numérica simple, sino un perfil cognitivo detallado que los docentes pueden usar para intervenciones personalizadas. Un estudiante con buena comprensión conceptual pero baja metacognición necesita diferentes ejercicios que uno con alta metacognición pero razonamiento algorítmico débil.

### 3.3 S-IA-X: Los Simuladores Profesionales

**Ubicación**: [simulators/](agents/simulators/)

Los simuladores profesionales abordan una carencia crítica en la educación tradicional de programación: los estudiantes aprenden a escribir código pero no a trabajar como desarrolladores. El desarrollo de software profesional implica comunicarse con stakeholders no técnicos, participar en ceremonias ágiles, manejar crisis de producción, conducir entrevistas técnicas, y tomar decisiones de seguridad con consecuencias reales.

Los simuladores implementan un **patrón Strategy** que permite crear escenarios realistas con diferentes roles profesionales:

**ProductOwnerSimulator** ([product_owner.py](agents/simulators/product_owner.py)) simula un Product Owner que presenta requisitos de manera deliberadamente ambigua, como ocurre en la vida real. El PO dice "necesitamos que los usuarios puedan compartir cosas con sus amigos", y el estudiante debe hacer las preguntas correctas para clarificar: ¿Qué tipos de cosas? ¿Quiénes son los amigos (contactos internos, externos, cualquiera)? ¿Qué significa "compartir" (ver, editar, transferir propiedad)? ¿Hay consideraciones de privacidad? Este ejercicio desarrolla habilidades de elicitación de requisitos que son críticas en el trabajo real.

**ScrumMasterSimulator** ([scrum_master.py](agents/simulators/scrum_master.py)) facilita ceremonias ágiles simuladas. En un daily standup, el estudiante debe comunicar qué hizo ayer, qué hará hoy y qué impedimentos tiene, de manera concisa y relevante. En una retrospectiva, debe reflexionar constructivamente sobre qué funcionó y qué mejorar. El simulador evalúa la calidad de la comunicación y proporciona feedback.

**TechInterviewerSimulator** ([tech_interviewer.py](agents/simulators/tech_interviewer.py)) conduce entrevistas técnicas realistas. Comienza con preguntas de diseño de sistemas ("¿Cómo diseñarías un acortador de URLs?"), continúa con problemas de algoritmos ("Encuentra el elemento repetido en un arreglo"), y termina con preguntas de seguimiento que exploran los límites del conocimiento del estudiante. El simulador proporciona feedback constructivo sobre las respuestas, señalando fortalezas y áreas de mejora.

**IncidentResponderSimulator** ([incident_responder.py](agents/simulators/incident_responder.py)) presenta situaciones de crisis de producción. "La aplicación está devolviendo errores 500 para el 30% de los usuarios. Los logs muestran timeouts de base de datos. El CEO está llamando cada 5 minutos." El estudiante debe diagnosticar el problema bajo presión, proponer mitigaciones temporales mientras investiga la causa raíz, y comunicar el estado a stakeholders. Este simulador desarrolla habilidades de troubleshooting y comunicación en crisis que son imposibles de enseñar en un aula tradicional.

**DevSecOpsSimulator** ([devsecops.py](agents/simulators/devsecops.py)) presenta escenarios de seguridad. "El escaneo de seguridad ha detectado una vulnerabilidad de SQL injection en el endpoint de login. Tenemos un deployment a producción programado en 2 horas." El estudiante debe identificar la vulnerabilidad, proponer una mitigación, evaluar el riesgo de postponer el deployment, y justificar sus decisiones de seguridad.

**ClientSimulator** ([client.py](agents/simulators/client.py)) simula un cliente no técnico que necesita explicaciones claras de conceptos técnicos. "¿Por qué tardó una semana hacer algo que parece tan simple?" El estudiante debe explicar complejidades técnicas de manera accesible sin condescendencia, desarrollando la capacidad de comunicación con stakeholders que no tienen background técnico.

Cada simulador mantiene estado de la conversación, una personalidad consistente (el PO puede ser exigente pero justo, el cliente puede ser impaciente pero razonable), y genera escenarios cada vez más complejos a medida que el estudiante progresa.

### 3.4 AR-IA: El Analista de Riesgos

**Ubicación**: [risk_analyst.py](agents/risk_analyst.py)

El Analista de Riesgos monitorea continuamente el comportamiento del estudiante para detectar patrones problemáticos. Este monitoreo no es intrusivo ni punitivo; su objetivo es identificar estudiantes que podrían beneficiarse de intervención temprana antes de que los problemas se agraven.

El agente analiza **cinco dimensiones de riesgo**:

**Riesgos Cognitivos (RC)** detectan problemas en cómo el estudiante está abordando el aprendizaje:

La **delegación total** ocurre cuando el estudiante pide a la IA que resuelva todo sin descomponer el problema. El sistema detecta frases como "dame el código completo", "hacé todo", "resolvelo por mí", usando un conjunto predefinido de señales en español implementado como un `frozenset` para búsquedas O(1). Cuando se detectan múltiples intentos de delegación total en una sesión, el sistema genera una alerta y puede activar automáticamente el modo socrático estricto.

La **dependencia excesiva de IA** se mide por el porcentaje de razonamiento delegado. Si más del 70% de las interacciones del estudiante son preguntas directas al tutor sin intentos previos de resolución, el sistema detecta un patrón de dependencia que está impidiendo el desarrollo de autonomía.

La **falta de justificación** indica que el estudiante acepta sugerencias sin explicar por qué tienen sentido. Esto sugiere aprendizaje superficial: el estudiante está siguiendo instrucciones pero no interiorizando el conocimiento.

**Riesgos Éticos (RE)** detectan posibles problemas de integridad académica:

El **código sospechoso** se detecta cuando un estudiante envía código de más de 100 caracteres en menos de 5 segundos. La velocidad humanamente posible de escritura de código (incluso para expertos) hace imposible producir código funcional significativo en ese tiempo, lo que sugiere que fue copiado de una fuente externa. El sistema no acusa directamente de plagio, pero registra la anomalía y puede solicitar que el estudiante explique el código línea por línea.

**Riesgos Epistémicos (REp)** detectan problemas en cómo el estudiante está construyendo conocimiento:

La **aceptación acrítica** ocurre cuando el estudiante acepta todo lo que dice la IA sin cuestionar. El sistema detecta esto correlacionando respuestas de IA con críticas o cuestionamientos posteriores del estudiante. Si un estudiante recibe muchas respuestas de IA pero nunca las cuestiona, puede estar desarrollando una confianza excesiva en la autoridad de la IA que es epistemológicamente problemática. La implementación usa **búsqueda binaria optimizada** (O(log n)) para correlacionar timestamps de respuestas de IA con críticas posteriores, en lugar de búsqueda lineal O(n²).

**Riesgos Técnicos (RT)** detectan problemas en la calidad del código:

Las **vulnerabilidades de seguridad** se detectan mediante patrones regex que buscan indicadores de SQL injection (concatenación de strings en queries), hardcoded secrets (passwords en código), uso de `eval`/`exec`, y otros patrones OWASP Top 10. Cuando se detectan, el sistema no solo alerta sino que sugiere las correcciones apropiadas.

Las **violaciones DRY** se detectan mediante fingerprinting MD5 de bloques de código normalizados. Si el estudiante está copiando y pegando código repetidamente en lugar de crear abstracciones, el sistema lo detecta y sugiere refactorizar.

**Riesgos de Gobernanza (RG)** detectan violaciones de políticas institucionales:

Las **sesiones excesivamente largas** (más de 4 horas continuas) pueden indicar fatiga cognitiva que impacta negativamente el aprendizaje, o uso del sistema fuera de horarios supervisados.

La **automatización sospechosa** se detecta cuando los intervalos entre mensajes tienen varianza muy baja (menos de 1 segundo) y promedio muy corto (menos de 5 segundos). Este patrón sugiere el uso de scripts automatizados en lugar de interacción humana genuina.

Cada riesgo detectado genera un registro que incluye el nivel de severidad (bajo, medio, alto, crítico), la evidencia específica (las trazas que dispararon la alerta), la causa raíz probable, recomendaciones de intervención para el docente, y una intervención pedagógica sugerida que el sistema puede ejecutar automáticamente.

### 3.5 GOV-IA: El Agente de Gobernanza

**Ubicación**: [governance.py](agents/governance.py)

El Agente de Gobernanza operacionaliza las políticas institucionales, asegurando que todas las interacciones cumplan con las reglas establecidas por la institución educativa. Este agente es crítico porque permite que diferentes instituciones, programas y cursos configuren el sistema según sus necesidades pedagógicas específicas.

El agente implementa marcos de referencia reconocidos internacionalmente:
- **UNESCO (2021)**: Recomendación sobre la Ética de la Inteligencia Artificial
- **OECD AI Principles (2019)**: Principios para la administración responsable de IA
- **IEEE Ethically Aligned Design (2019)**: Diseño éticamente alineado
- **ISO/IEC 23894:2023**: Gestión de riesgos en IA
- **ISO/IEC 42001:2023**: Sistemas de gestión de IA

El corazón del agente es un **sistema de semáforos** que determina si una acción puede proceder:

**Verde (COMPLIANT)**: La acción cumple completamente con las políticas. Puede proceder sin modificaciones.

**Amarillo (WARNING)**: La acción puede proceder pero presenta advertencias que deben registrarse. Por ejemplo, si un estudiante solicita un nivel de ayuda alto pero no excesivo, el sistema permite la interacción pero registra que el estudiante está rozando los límites.

**Rojo (VIOLATION)**: La acción viola una política y está bloqueada. Por ejemplo, si un estudiante solicita una solución completa y la política `block_complete_solutions` está activa, la solicitud es bloqueada y redirigida hacia una interacción pedagógica apropiada.

Las **políticas son configurables** a múltiples niveles:

```python
policies = {
    "max_ai_assistance_level": 0.7,      # Máximo 70% de asistencia IA
    "require_explicit_ai_usage": True,   # Exigir declaración de uso de IA
    "block_complete_solutions": True,    # Bloquear solicitudes de soluciones completas
    "require_traceability": True,        # Exigir trazabilidad N4 completa
    "enforce_academic_integrity": True,  # Verificar integridad académica
    "max_session_hours": 4,              # Máximo 4 horas por sesión
}
```

Un docente puede configurar que para un trabajo práctico inicial, `max_ai_assistance_level` sea 0.8 para permitir más ayuda mientras los estudiantes se familiarizan con los conceptos. Para el examen final, puede reducirlo a 0.3 para evaluar más rigurosamente la comprensión autónoma.

El agente de gobernanza también actúa como **filtro de privacidad**, detectando y redactando información personal identificable (PII) antes de enviarla al LLM. Los patrones detectados incluyen:
- Emails → `[EMAIL_REDACTED]`
- DNI/documentos de identidad → `[DNI_REDACTED]`
- Números de teléfono → `[PHONE_REDACTED]`
- Números de tarjetas de crédito → `[CARD_REDACTED]`

Esta sanitización es crítica cuando se usan proveedores LLM externos como Gemini u OpenAI, donde los datos del estudiante saldrían de la infraestructura institucional.

### 3.6 TC-N4: El Sistema de Trazabilidad Cognitiva

**Ubicación**: [traceability.py](agents/traceability.py) y [models/trace.py](models/trace.py)

La Trazabilidad Cognitiva N4 es el sistema que captura y organiza toda la evidencia del proceso de aprendizaje. El nombre "N4" se refiere a los cuatro niveles de profundidad de trazabilidad, cada uno capturando información progresivamente más rica:

**Nivel N1 - Superficial**: Solo registra entregas finales y archivos. Este es el nivel de trazabilidad de los sistemas tradicionales de gestión de tareas académicas. Se sabe QUÉ entregó el estudiante, pero no CÓMO llegó a esa entrega.

**Nivel N2 - Técnico**: Captura commits de Git, ejecución de tests, cambios en código. Proporciona una línea temporal de cambios técnicos que permite reconstruir la evolución del código, pero no el razonamiento detrás de los cambios.

**Nivel N3 - Interaccional**: Registra todos los prompts enviados al tutor IA y todas las respuestas recibidas. Permite ver qué preguntó el estudiante y qué obtuvo, pero no necesariamente por qué preguntó lo que preguntó.

**Nivel N4 - Cognitivo**: El nivel más profundo y valioso. Captura el estado cognitivo del estudiante (exploración, planificación, implementación, depuración, validación, reflexión), la intención cognitiva (qué intentaba lograr), la justificación de decisiones (por qué eligió una aproximación), las alternativas consideradas (qué otras opciones evaluó y por qué las descartó), el tipo de estrategia (qué patrón de resolución usó), y el nivel de involucramiento de IA (qué porcentaje del razonamiento fue asistido).

El modelo `CognitiveTrace` captura cada interacción con esta riqueza de información:

```python
class CognitiveTrace(BaseModel):
    id: str                             # Identificador único
    session_id: str                     # Sesión a la que pertenece
    created_at: datetime                # Cuándo ocurrió
    student_id: str                     # Quién la generó
    activity_id: str                    # En qué actividad
    trace_level: TraceLevel             # N1, N2, N3, N4
    interaction_type: InteractionType   # prompt, response, commit, etc.
    content: str                        # Contenido de la interacción
    cognitive_state: Optional[str]      # exploracion, implementacion, etc.
    cognitive_intent: Optional[str]     # Qué intentaba lograr
    decision_justification: Optional[str]  # Por qué tomó esa decisión
    alternatives_considered: List[str]  # Qué otras opciones evaluó
    strategy_type: Optional[str]        # Qué patrón usó
    ai_involvement: float               # 0.0 a 1.0, cuánta IA usó
```

Las trazas individuales se agrupan en `TraceSequence`, que representa un episodio cognitivo completo (una sesión de trabajo en un problema específico). La secuencia incluye métricas agregadas como el "camino de razonamiento" (la secuencia de estados cognitivos por los que pasó el estudiante), los cambios de estrategia, y el score de dependencia de IA calculado como el promedio ponderado de involucramiento de IA en todas las trazas.

Esta riqueza de información permite análisis que serían imposibles con trazabilidad tradicional: ¿Los estudiantes que pasan más tiempo en la fase de exploración tienen mejores resultados? ¿El número de cambios de estrategia correlaciona con la calidad de la solución? ¿Los estudiantes con alta metacognición son mejores en autocorregirse? Estas preguntas de investigación pueden responderse con los datos capturados por TC-N4.

---

## 4. El Entrenador Digital y su Integración con Agentes

**Ubicación**: [api/routers/training/](api/routers/training/), [services/code_evaluator.py](services/code_evaluator.py), y [core/training_*.py](core/)

El Entrenador Digital es el módulo de práctica estructurada del sistema, diseñado para que los estudiantes puedan ejercitar sus habilidades de programación de forma guiada y evaluada. A diferencia del modo Tutor que es conversacional y abierto, el Entrenador Digital presenta ejercicios concretos con estructura definida: consigna, código inicial, tests automatizados, pistas progresivas y evaluación por IA.

### 4.1 Evolución Arquitectónica: Integración con Agentes (Cortez50)

En versiones anteriores del sistema, el Entrenador Digital operaba de manera completamente independiente de los seis agentes de IA. Sin embargo, a partir de **Cortez50**, se implementó una arquitectura de integración opcional que permite al Entrenador Digital aprovechar las capacidades de T-IA-Cog (Tutor Cognitivo), TC-N4 (Trazabilidad) y AR-IA (Análisis de Riesgos) sin perder su característica de rendimiento optimizado para ejercicios estructurados.

Esta integración se materializa a través de tres componentes nuevos y un nuevo modo de estrategia del tutor:

**TrainingGateway** ([training_gateway.py](core/training_gateway.py)): El orquestador central para la integración. Actúa como intermediario entre los endpoints del Entrenador Digital y el ecosistema de agentes, coordinando:
- Captura de trazas N4 durante ejercicios
- Invocación de T-IA-Cog para pistas contextuales
- Monitoreo de riesgos en tiempo real

**TrainingTraceCollector** ([training_traceability.py](core/training_traceability.py)): Colector especializado de trazas N4 para el contexto de ejercicios. Implementa un modelo híbrido de tres estrategias de trazabilidad:
- **Estrategia A (Inferida)**: Deduce el estado cognitivo de señales observables como patrones de código, errores, y cambios entre intentos
- **Estrategia B (Semi-activa)**: Captura voluntaria cuando el estudiante solicita pistas
- **Estrategia C (Activa)**: Reflexión post-ejercicio explícita del estudiante

**TrainingRiskMonitor** ([training_risk_monitor.py](core/training_risk_monitor.py)): Monitor de riesgos en tiempo real especializado para ejercicios, detectando:
- **Copy-paste**: Velocidad de escritura imposible (>50 chars/segundo)
- **Frustración**: Múltiples intentos fallidos consecutivos
- **Dependencia de pistas**: Solicitar pista sin intentar primero
- **Envío rápido**: Código enviado sin tiempo de reflexión

**TrainingHintsStrategy** ([training_hints.py](agents/tutor_modes/training_hints.py)): Nueva estrategia del tutor que extiende `GuidedStrategy` para generar pistas contextuales específicas para ejercicios. Construye "prompts implícitos" a partir de:
- Contexto del ejercicio (título, consigna, conceptos esperados)
- Historial de intentos del estudiante
- Último error encontrado
- Nivel de dificultad del ejercicio

### 4.2 Arquitectura de Integración

La integración sigue un patrón de **envoltura opcional** controlado por feature flags. El flujo es el siguiente:

```
Solicitud → TrainingGateway → [¿Qué necesita?]
                                     │
                     ┌───────────────┼───────────────┐
                     ▼               ▼               ▼
               ¿Trazabilidad?  ¿Análisis de    ¿Pista
                               riesgos?        contextual?
                     │               │               │
                     ▼               ▼               ▼
                TC-N4 Agent    AR-IA Agent    T-IA-Cog
                (TrainingTraceCollector) (TrainingRiskMonitor) (TrainingHintsStrategy)
```

Los **feature flags** que controlan esta integración son:

```python
TRAINING_USE_TUTOR_HINTS = True   # Usar T-IA-Cog para pistas contextuales
TRAINING_N4_TRACING = True        # Capturar trazas N4 durante ejercicios
TRAINING_RISK_MONITOR = True      # Monitorear riesgos en tiempo real
```

Cuando los flags están desactivados, el Entrenador Digital opera en su modo original (pistas estáticas, sin trazabilidad N4, sin análisis de riesgos), garantizando compatibilidad hacia atrás y rendimiento óptimo.

### 4.3 Endpoints Legacy V1 y V2

El Entrenador Digital expone dos conjuntos de endpoints: **V1 (Legacy)** para compatibilidad con frontends existentes, y **V2** para las nuevas capacidades de integración con agentes.

**Endpoints V1 (Legacy)** - Reforzados en Cortez56:

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

Los tres endpoints añadidos en **Cortez56** proporcionan funcionalidad V1 que el frontend necesitaba:

- **`POST /training/submit-ejercicio`**: Envía código para evaluación. Ejecuta tests automatizados y, opcionalmente, invoca al LLM para feedback pedagógico. Devuelve resultados de tests, siguiente ejercicio disponible, o resultados finales si la sesión termina.

- **`POST /training/corregir-ia`**: Solicita al LLM (mentor "Alex") que analice el código del estudiante y sugiera correcciones. Devuelve análisis pedagógico y hasta 4 sugerencias específicas. Si el LLM no está disponible, retorna un mensaje de fallback.

- **`GET /training/sesion/{id}/estado`**: Retorna el estado completo de la sesión incluyendo campos N4 para trazabilidad: `cognitive_state`, `ai_dependency`, y `current_risk_level`.

**Endpoints V2 (Integración con Agentes)** - Cortez50:

```
POST /training/pista/v2           # Pista contextual con T-IA-Cog
POST /training/reflexion          # Capturar reflexión post-ejercicio
GET  /training/sesion/{id}/proceso # Análisis de proceso cognitivo
POST /training/submit/v2          # Envío con trazabilidad extendida
```

El endpoint **`POST /training/pista/v2`** demuestra la diferencia con V1: en lugar de retornar una pista estática de la base de datos, invoca a `TrainingHintsStrategy` que:
1. Construye un prompt con contexto del ejercicio y errores del estudiante
2. Usa T-IA-Cog para generar una pista personalizada
3. Registra la solicitud como traza cognitiva (si N4 habilitado)
4. Aplica los 4 niveles de ayuda (mínimo, bajo, medio, alto)

### 4.4 Estados Cognitivos Inferidos

El `TrainingTraceCollector` infiere estados cognitivos a partir de señales observables:

| Estado | Descripción | Señales |
|--------|-------------|---------|
| `EXPLORACION` | Primer intento del ejercicio | attempt_number == 1 |
| `IMPLEMENTACION` | Desarrollo activo de solución | Cambios moderados en código |
| `DEPURACION` | Corrección de errores | Cambios pequeños (<5 líneas) |
| `CAMBIO_ESTRATEGIA` | Nuevo enfoque | Cambio estructural >50% |
| `BUSQUEDA_AYUDA` | Solicitud de pista | Acción explícita de pedir pista |
| `VALIDACION` | Verificación exitosa | Todos los tests pasan |
| `ATASCADO` | Múltiples fallos | ≥3 intentos fallidos recientes |
| `REFLEXION` | Análisis post-ejercicio | Contenido explícito de reflexión |

Cada inferencia incluye un nivel de confianza (alta, media, baja) y un score numérico (0.0-1.0) junto con el razonamiento que llevó a la inferencia.

### 4.5 Tipos de Riesgo en Entrenamiento

El `TrainingRiskMonitor` detecta cinco tipos de riesgo específicos para ejercicios:

| Tipo | Severidad | Detección |
|------|-----------|-----------|
| `COPY_PASTE` | HIGH/CRITICAL | >50 chars/segundo, >100 chars nuevos |
| `FRUSTRATION` | MEDIUM/HIGH | ≥5 intentos fallidos en 2 minutos |
| `HINT_DEPENDENCY` | MEDIUM/HIGH | Pedir pista cada ≤3 intentos |
| `RAPID_SUBMISSION` | LOW | Envío en <3 segundos |
| `POSSIBLE_ABANDONMENT` | MEDIUM | >10 minutos de inactividad |

Las alertas de severidad HIGH o CRITICAL se persisten en el repositorio y generan notificaciones para el docente.

### 4.6 Comparación: Entrenador Digital con y sin Agentes

| Aspecto | Sin Agentes (Legacy) | Con Agentes (Cortez50+) |
|---------|---------------------|------------------------|
| **Pistas** | Estáticas de BD | Contextuales vía T-IA-Cog |
| **Trazabilidad** | Intentos y resultados | N4 completa (estados cognitivos) |
| **Riesgos** | No detectados | Tiempo real (copy-paste, frustración) |
| **Reflexión** | No capturada | Post-ejercicio con XP bonus |
| **Latencia** | Óptima | Ligeramente mayor (paralelo) |
| **Configuración** | Ninguna | 3 feature flags |

Ambos modos coexisten en el sistema. El modo legacy permanece disponible desactivando los feature flags, útil para:
- Ejercicios donde la velocidad es crítica
- Evaluaciones donde no se desea trazabilidad
- Fallback si el LLM no está disponible

---

## 5. El Motor Cognitivo (CRPE)

**Ubicación**: [cognitive_engine.py](core/cognitive_engine.py)

El Motor Cognitivo, también conocido como CRPE (Cognitive-Reflective Processing Engine), es el cerebro analítico del sistema. Su responsabilidad es clasificar cada interacción del estudiante para determinar cómo debe responder el sistema.

El CRPE analiza tres dimensiones de cada input:

**Intención**: ¿Qué está tratando de hacer el estudiante? Las intenciones incluyen solicitar ayuda conceptual ("no entiendo qué es una cola"), pedir código ("cómo escribo un loop en Python"), verificar comprensión ("¿está bien si uso un arreglo aquí?"), reportar un problema ("mi código da error"), solicitar evaluación ("¿cómo voy hasta ahora?"), o expresar frustración ("esto no tiene sentido").

**Estado Cognitivo**: ¿En qué fase del proceso de resolución de problemas está el estudiante? Los estados incluyen:
- **Exploración**: Entendiendo el problema, investigando qué se pide, explorando opciones
- **Planificación**: Diseñando una aproximación, decidiendo qué estructuras usar, planificando los pasos
- **Implementación**: Escribiendo código, traduciendo el plan a código ejecutable
- **Depuración**: Identificando errores, investigando por qué el código no funciona
- **Validación**: Verificando que la solución cumple los requisitos, probando casos límite
- **Reflexión**: Evaluando el proceso, identificando aprendizajes, considerando alternativas

**Estrategia Pedagógica**: Basándose en la intención y el estado cognitivo, ¿cómo debería responder el sistema? Esto incluye qué modo del tutor activar, qué nivel de pistas proporcionar, y si se debe intervenir con advertencias o redirecciones.

El motor usa una combinación de análisis heurístico (patrones en el texto que indican estados cognitivos específicos) y análisis con LLM (cuando es necesaria comprensión semántica más profunda). Por ejemplo, palabras como "no entiendo", "confundido", "perdido" activan heurísticas de estado de confusión, mientras que análisis más sutiles de intención pueden requerir consulta al LLM.

---

## 6. Integración con Proveedores LLM

**Ubicación**: [llm/](llm/)

El sistema soporta múltiples proveedores de LLM a través de un **patrón Factory** que permite intercambiar proveedores sin modificar el código de los agentes.

**Ollama** ([ollama_provider.py](llm/ollama_provider.py)) es el proveedor recomendado para despliegues donde los datos deben permanecer en infraestructura propia. Ollama permite ejecutar modelos como Phi-3, Llama 2 o Mistral localmente. La configuración incluye control de concurrencia mediante semáforos de asyncio para evitar sobrecargar el servidor Ollama con demasiadas solicitudes simultáneas.

**Gemini** ([gemini_provider.py](llm/gemini_provider.py)) integra la API de Google. El proveedor implementa varias optimizaciones: connection pooling para reutilizar conexiones HTTP y reducir latencia, retry con jitter para manejar errores transitorios sin crear "thundering herds" (cuando muchos clientes reintentan simultáneamente), y selección automática de modelo (Flash para conversaciones rápidas, Pro para análisis de código profundo).

**Mistral** ([mistral_provider.py](llm/mistral_provider.py)) integra la API de Mistral AI, útil para instituciones que prefieren modelos de código abierto con soporte comercial.

**Mock** ([mock.py](llm/mock.py)) es un proveedor simulado para testing que retorna respuestas predefinidas sin hacer llamadas reales a APIs, permitiendo tests rápidos y determinísticos.

El patrón Factory permite crear proveedores de forma uniforme:

```python
from backend.llm.factory import LLMProviderFactory

# Crear desde variables de entorno (lee LLM_PROVIDER, GEMINI_API_KEY, etc.)
provider = LLMProviderFactory.create_from_env()

# O especificar explícitamente
provider = LLMProviderFactory.create("gemini", {
    "api_key": "tu-api-key",
    "model": "gemini-1.5-pro"
})

# Usar el proveedor (idéntico independientemente de cuál sea)
response = await provider.generate(messages, temperature=0.7)
```

---

## 7. Capa de Persistencia

### 7.1 Modelos ORM

**Ubicación**: [database/models/](database/models/)

El sistema define 25 modelos SQLAlchemy organizados por dominio funcional en 14 archivos. Esta organización permite que cada archivo contenga modelos relacionados semánticamente, facilitando la navegación y el mantenimiento.

Los modelos de **sesiones y usuarios** incluyen `SessionDB` para sesiones de aprendizaje (con estado, modo, timestamps), `UserDB` para usuarios con roles (estudiante, docente, administrador), y `StudentProfileDB` para perfiles de estudiantes con métricas de progreso acumuladas.

Los modelos de **trazabilidad** incluyen `CognitiveTraceDB` para las trazas cognitivas N4 individuales, `TraceSequenceDB` para secuencias de trazas que representan episodios cognitivos completos, y `GitTraceDB` para trazas de nivel N2 derivadas de actividad Git.

Los modelos de **evaluación y riesgos** incluyen `EvaluationDB` para evaluaciones de proceso generadas por E-IA-Proc, `RiskDB` para riesgos detectados por AR-IA, y `RiskAlertDB` para alertas de riesgo que requieren atención del docente.

Los modelos de **actividades** incluyen `ActivityDB` para actividades creadas por docentes (con políticas pedagógicas configurables), y `ExerciseDB` junto con modelos relacionados (`HintDB`, `TestDB`, `AttemptDB`, `RubricDB`, `RubricLevelDB`) para ejercicios estructurados con pistas, tests y rúbricas de evaluación.

Los modelos de **simuladores** incluyen `InterviewSessionDB` para sesiones de entrevista técnica, `IncidentSimulationDB` para simulaciones de respuesta a incidentes, y `SimulatorEventDB` para eventos individuales dentro de simulaciones.

### 7.2 Repositorios

**Ubicación**: [database/repositories/](database/repositories/)

Los repositorios implementan el **Repository Pattern** que abstrae el acceso a datos. Cada repositorio encapsula todas las queries relacionadas con un dominio específico, proporcionando una interfaz limpia a las capas superiores.

El principal beneficio de este patrón es que los agentes y routers nunca escriben queries SQL o interactúan directamente con SQLAlchemy. Simplemente llaman métodos del repositorio apropiado. Esto permite cambiar la implementación de persistencia (por ejemplo, de PostgreSQL a otro motor) sin modificar ningún código de negocio.

Los repositorios también implementan **batch loading** para prevenir el problema N+1. Cuando se necesitan trazas para múltiples sesiones, en lugar de hacer N queries (una por sesión), se usa un método como `get_by_session_ids([id1, id2, ...])` que retorna todas las trazas en una sola query y las organiza por sesión.

El sistema incluye **24 repositorios** organizados en 12 módulos:

| Módulo | Repositorios |
|--------|--------------|
| [session_repository.py](database/repositories/session_repository.py) | SessionRepository |
| [trace_repository.py](database/repositories/trace_repository.py) | TraceRepository (trazas cognitivas) |
| [risk_repository.py](database/repositories/risk_repository.py) | RiskRepository |
| [evaluation_repository.py](database/repositories/evaluation_repository.py) | EvaluationRepository |
| [activity_repository.py](database/repositories/activity_repository.py) | ActivityRepository |
| [user_repository.py](database/repositories/user_repository.py) | UserRepository |
| [exercise_repository.py](database/repositories/exercise_repository.py) | ExerciseRepository, HintRepository, TestRepository, AttemptRepository, RubricRepository |
| [git_repository.py](database/repositories/git_repository.py) | GitTraceRepository |
| [institutional_repository.py](database/repositories/institutional_repository.py) | CourseReportRepository, RemediationPlanRepository, RiskAlertRepository |
| [simulator_repository.py](database/repositories/simulator_repository.py) | InterviewSessionRepository, IncidentSimulationRepository, SimulatorEventRepository |
| [lti_repository.py](database/repositories/lti_repository.py) | LTIDeploymentRepository, LTISessionRepository |
| [profile_repository.py](database/repositories/profile_repository.py) | StudentProfileRepository, SubjectRepository, TraceSequenceRepository |

---

## 8. API REST

**Ubicación**: [api/](api/)

### 8.1 Estructura de Routers

La API está organizada en 23+ routers que exponen funcionalidad específica bajo el prefijo `/api/v1`. Esta organización modular permite que cada router tenga un enfoque claro y sea mantenido independientemente.

Los **routers core** manejan la funcionalidad fundamental:
- `/health`: Health checks para balanceadores de carga y monitoreo
- `/sessions`: CRUD de sesiones de aprendizaje
- `/interactions`: El endpoint principal donde el estudiante interactúa con el tutor
- `/traces`: Consultas de trazabilidad N4
- `/risks`: Análisis y consulta de riesgos

Los **routers educativos** manejan funcionalidad específica de aprendizaje:
- `/activities`: Gestión de actividades por docentes
- `/exercises`: Ejercicios con rúbricas
- `/training`: Sesiones de entrenamiento/examen (incluye endpoints V1 legacy y V2)
- `/evaluations`: Evaluaciones de proceso

Los **routers de simuladores** exponen los simuladores profesionales:
- `/simulators`: Lista de simuladores disponibles e interacción
- `/simulators-enhanced`: Versión mejorada con más roles

Los **routers administrativos** manejan configuración y monitoreo:
- `/admin/llm`: Configuración de proveedores LLM
- `/auth`: Autenticación JWT (login, register, refresh)
- `/metrics`: Métricas Prometheus

### 8.2 UTF-8 JSON Response (Cortez54)

A partir de Cortez54, el sistema usa una clase personalizada `UTF8JSONResponse` que asegura que los caracteres UTF-8 (como tildes y caracteres especiales en español) se codifiquen correctamente en las respuestas JSON:

```python
class UTF8JSONResponse(JSONResponse):
    """
    Custom JSONResponse que codifica correctamente caracteres UTF-8.
    Evita que 'ó' aparezca como '\\u00f3' en las respuestas.
    """
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,  # Mantiene caracteres UTF-8 como están
            allow_nan=False,
            default=str,
        ).encode("utf-8")
```

### 8.3 Excepciones Personalizadas

**Ubicación**: [exceptions.py](api/exceptions.py)

El sistema define **50+ excepciones personalizadas** para manejo consistente de errores. En lugar de lanzar `HTTPException` directamente desde los routers, el código lanza excepciones de dominio que luego son convertidas a respuestas HTTP apropiadas por handlers globales.

Las excepciones están organizadas por dominio funcional:

**Excepciones de Sesión**:
- `SessionNotFoundError`: Sesión no encontrada
- `SessionAlreadyActiveError`: Ya existe una sesión activa
- `SessionExpiredError`: Sesión expirada

**Excepciones de Usuario y Autenticación**:
- `UserNotFoundError`: Usuario no encontrado
- `UserInactiveError`: Usuario inactivo
- `RoleRequiredError`: Rol requerido (ej: teacher)
- `InvalidTokenError`: Token JWT inválido
- `AuthenticationError`: Error de autenticación genérico

**Excepciones de Trazabilidad**:
- `TraceNotFoundError`: Traza no encontrada
- `TraceSequenceNotFoundError`: Secuencia de trazas no encontrada
- `InvalidTraceLevelError`: Nivel de traza inválido

**Excepciones de Actividades y Ejercicios**:
- `ActivityNotFoundError`: Actividad no encontrada
- `ExerciseNotFoundError`: Ejercicio no encontrado
- `HintNotFoundError`: Pista no encontrada
- `TestNotFoundError`: Test no encontrado

**Excepciones de Riesgos y Evaluaciones**:
- `RiskNotFoundError`: Riesgo no encontrado
- `RiskAlertNotFoundError`: Alerta de riesgo no encontrada
- `EvaluationNotFoundError`: Evaluación no encontrada

**Excepciones de Entrenamiento (Cortez50)**:
- `TrainingSessionNotFoundError`: Sesión de entrenamiento no encontrada
- `TrainingSessionAccessDeniedError`: Acceso denegado a la sesión
- `TrainingOperationError`: Error en operación de entrenamiento

**Excepciones de Reportes e Institucionales**:
- `ReportNotFoundError`: Reporte no encontrado
- `ReportGenerationError`: Error al generar reporte
- `NoDataFoundError`: Sin datos para el periodo/filtros

Este patrón tiene varias ventajas: los mensajes de error son consistentes en toda la API, las excepciones de dominio son testables independientemente de HTTP, y el código de los routers es más limpio porque no mezcla lógica de negocio con detalles HTTP.

### 8.4 Middleware

El sistema implementa varios middlewares de seguridad y rendimiento:

**CORS** está configurado desde variables de entorno para permitir acceso desde los frontends autorizados, con headers y métodos explícitamente permitidos para mayor seguridad.

**GZip** comprime automáticamente respuestas mayores a 1000 bytes, reduciendo el tráfico de red.

**TrustedHost** previene ataques de Host Header en producción, rechazando solicitudes con hosts no autorizados.

**Rate Limiting** implementado con SlowAPI previene abuso del sistema, con límites configurables por endpoint (100 requests/hora por defecto, 10 interacciones/minuto para el endpoint de IA).

---

## 9. Configuración y Despliegue

### 9.1 Variables de Entorno

El backend se configura completamente mediante variables de entorno, siguiendo el principio de twelve-factor apps. Las variables críticas incluyen:

**Base de Datos**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` configuran la conexión a PostgreSQL.

**Cache**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` configuran la conexión a Redis.

**LLM**: `LLM_PROVIDER` selecciona el proveedor (gemini, ollama, mistral, mock), y variables específicas como `GEMINI_API_KEY` o `OLLAMA_BASE_URL` configuran cada proveedor.

**Seguridad**: `JWT_SECRET_KEY` y `SECRET_KEY` deben ser generados de forma segura (el comando `make generate-secrets` lo hace automáticamente). `METRICS_API_KEY` protege el endpoint de métricas de acceso no autorizado.

**Entrenador Digital (Cortez50)**:
- `TRAINING_USE_TUTOR_HINTS`: Habilita pistas contextuales con T-IA-Cog
- `TRAINING_N4_TRACING`: Habilita captura de trazas N4 en ejercicios
- `TRAINING_RISK_MONITOR`: Habilita monitoreo de riesgos en tiempo real

### 9.2 Docker

El despliegue recomendado es con Docker Compose, que orquesta todos los servicios necesarios:

```bash
docker-compose up -d  # Backend + PostgreSQL + Redis + Frontend
```

Para desarrollo con herramientas de debug:
```bash
docker-compose --profile debug up -d  # + pgAdmin + Redis Commander
```

Para producción con monitoreo:
```bash
docker-compose --profile monitoring up -d  # + Prometheus + Grafana
```

### 9.3 Lifecycle de la Aplicación

Al iniciar, el backend ejecuta una secuencia de inicialización cuidadosamente ordenada:

1. **Validación de configuración**: Verifica que todas las variables de entorno requeridas estén presentes y tengan valores válidos. Si falta algo crítico, el servidor no inicia.

2. **Inicialización de base de datos**: Crea tablas si no existen, ejecuta migraciones pendientes.

3. **Seed de datos**: Si la base de datos está vacía, carga ejercicios iniciales para que los estudiantes tengan material de práctica.

4. **Inicialización de métricas**: Configura los contadores y histogramas de Prometheus.

5. **Inicio de cleanup periódico**: Inicia una tarea en background que limpia cache expirado cada cierto tiempo. Esto incluye la limpieza TTL de `TrainingTraceCollector` y `TrainingRiskMonitor` (añadida en Cortez52).

Al cerrar, el proceso inverso asegura liberación limpia de recursos: detiene el cleanup periódico, cierra conexiones del proveedor LLM, y dispone el pool de conexiones de base de datos.

---

## 10. Testing

### 10.1 Estructura

Los tests están organizados en `tests/` con fixtures compartidos en `conftest.py`. Los tests de agentes verifican la lógica de cada agente individualmente, los tests de gateway verifican la orquestación completa, los tests de repositorios verifican la persistencia, y los tests de API verifican endpoints de extremo a extremo.

### 10.2 Ejecución

```bash
pytest tests/ -v --cov=backend    # Todos los tests con cobertura
pytest tests/ -v -m "unit"        # Solo tests unitarios
pytest tests/ -v -m "integration" # Solo tests de integración
pytest -k "test_tutor" -v         # Tests por patrón
```

### 10.3 Cobertura

Se requiere un mínimo de 70% de cobertura de código. Paths críticos como `ai_gateway.py`, `cognitive_engine.py` y todos los agentes deben tener cobertura de 90% o superior.

---

## 11. Seguridad

### 11.1 Autenticación

El sistema usa JWT (JSON Web Tokens) para autenticación. Al hacer login, el usuario recibe un token firmado que incluye su identidad y rol. Este token debe enviarse en cada solicitud subsiguiente como header `Authorization: Bearer <token>`.

### 11.2 Autorización

Tres roles con diferentes permisos:
- **student**: Acceso a sus propias sesiones, interacciones y ejercicios
- **teacher**: Todo lo anterior más gestión de actividades, reportes y alertas de riesgo
- **admin**: Todo lo anterior más configuración de LLM, exportación de datos y gestión de usuarios

### 11.3 Protecciones

- **Rate Limiting**: Previene abuso del sistema
- **Validación de UUID**: Todos los IDs se validan antes de queries
- **Sanitización de PII**: Información personal se filtra antes de enviar a LLMs externos
- **CORS configurado**: Solo orígenes autorizados pueden acceder a la API

---

## 12. Observabilidad

### 12.1 Logging

El sistema usa logging estructurado con niveles configurables. Los logs incluyen timestamps, nombres de módulos y niveles, facilitando la depuración y el monitoreo. Cortez46 mejoró el logging para usar formato lazy (evitando formateo innecesario cuando el nivel no está activo).

### 12.2 Métricas Prometheus

El endpoint `/metrics` expone métricas para Prometheus incluyendo requests por endpoint, latencia de requests, sesiones activas, uso de LLM, y riesgos detectados por tipo.

### 12.3 Health Checks

El endpoint `/api/v1/health` verifica el estado de todos los servicios dependientes (PostgreSQL, Redis, LLM) y retorna un status agregado que puede ser usado por balanceadores de carga.

---

## 13. Patrones de Diseño

El backend implementa varios patrones de diseño de software reconocidos:

**Factory Pattern** en `LLMProviderFactory`, `SimulatorFactory` y `TutorModeFactory` para crear instancias sin acoplamiento.

**Strategy Pattern** en los modos del tutor ([tutor_modes/](agents/tutor_modes/)) y simuladores ([simulators/](agents/simulators/)), permitiendo intercambiar algoritmos en tiempo de ejecución.

**Repository Pattern** para abstraer el acceso a datos y facilitar testing.

**Singleton con Thread Safety** para instancias únicas que requieren inicialización costosa, usando double-checked locking con locks de threading.

**Gateway Pattern** en `TrainingGateway` para orquestar la integración del Entrenador Digital con los agentes.

---

## 14. Estructura de Directorios

```
backend/
├── __init__.py              # Versión y metadata del paquete
├── __main__.py              # Entry point para `python -m backend`
├── agents/                  # Los 6 agentes de IA
│   ├── tutor.py            # T-IA-Cog: Tutor Cognitivo
│   ├── tutor_modes/        # Estrategias del tutor (6 modos)
│   │   ├── base.py         # TutorModeStrategy ABC
│   │   ├── socratic.py     # Modo socrático
│   │   ├── explicative.py  # Modo explicativo
│   │   ├── guided.py       # Modo guiado (4 niveles)
│   │   ├── metacognitive.py # Modo metacognitivo + clarificación
│   │   ├── training_hints.py # Modo pistas para entrenamiento (Cortez50)
│   │   └── factory.py      # TutorModeFactory
│   ├── evaluator.py        # E-IA-Proc: Evaluador de Procesos
│   ├── risk_analyst.py     # AR-IA: Analista de Riesgos
│   ├── governance.py       # GOV-IA: Gobernanza
│   ├── traceability.py     # TC-N4: Trazabilidad
│   └── simulators/         # S-IA-X: Simuladores (6+ roles)
│       ├── base.py         # BaseSimulator ABC
│       ├── factory.py      # SimulatorFactory
│       ├── product_owner.py
│       ├── scrum_master.py
│       ├── tech_interviewer.py
│       ├── incident_responder.py
│       ├── devsecops.py
│       └── client.py
├── core/                    # Núcleo del sistema
│   ├── ai_gateway.py       # Orquestador central (STATELESS)
│   ├── cognitive_engine.py # CRPE: Motor cognitivo
│   ├── cache.py            # Cache con Redis
│   ├── training_gateway.py      # Orquestador Entrenador + Agentes (Cortez50)
│   ├── training_traceability.py # Colector trazas N4 entrenamiento (Cortez50)
│   ├── training_risk_monitor.py # Monitor riesgos entrenamiento (Cortez50)
│   └── gateway/            # Protocolos y fallbacks
├── models/                  # Modelos Pydantic (domain)
├── database/               # Capa de persistencia
│   ├── models/             # Modelos ORM (14 archivos, 25 clases)
│   └── repositories/       # Repositorios (12 archivos, 24 clases)
├── llm/                    # Integración LLM (5 proveedores)
├── api/                    # Capa REST
│   ├── main.py             # FastAPI app + lifespan + UTF8JSONResponse
│   ├── exceptions.py       # 50+ excepciones personalizadas
│   ├── routers/            # 23+ routers
│   │   ├── training/       # Entrenador Digital
│   │   │   ├── endpoints.py        # Endpoints REST V1 legacy (+ Cortez56)
│   │   │   ├── integration_endpoints.py # Endpoints V2 (Cortez50)
│   │   │   ├── schemas.py          # Modelos Pydantic
│   │   │   ├── session_storage.py  # Almacenamiento Redis/memoria
│   │   │   └── helpers.py          # Utilidades
│   │   └── simulators/     # Routers de simuladores
│   └── middleware/         # Rate limiting, logging, CORS
├── services/               # Servicios de negocio
│   └── code_evaluator.py   # Evaluador de código con IA "Alex"
└── scripts/                # Scripts de utilidad
```

---

## 15. Historial de Auditorías

El backend ha pasado por 60+ auditorías de código que han mejorado progresivamente la arquitectura:

| Auditoría | Foco | Cambios Principales |
|-----------|------|---------------------|
| **Cortez60** | Enero 2026 Update | Actualización general del sistema |
| **Cortez56** | Backend V1 Legacy Endpoints | 3 nuevos endpoints training, fix datetime, fix parameter name |
| **Cortez54** | Backend Endpoint Audit | UTF8JSONResponse, 12 defectos corregidos (métodos faltantes, datetime) |
| **Cortez53** | HTTPException Migration | 51 HTTPExceptions → excepciones personalizadas en 9 archivos |
| **Cortez52** | TTL Cleanup | Limpieza automática de cache en TrainingTraceCollector y TrainingRiskMonitor |
| **Cortez50** | Entrenador Digital + Agentes | TrainingGateway, TrainingHintsStrategy, endpoints V2, trazabilidad N4 |
| **Cortez47** | Backend Deep Audit | Eliminación de 8,544 líneas de archivos legacy redundantes |
| **Cortez46** | Backend Modularization | Repositorios extraídos, routers divididos, 12 nuevas excepciones |
| **Cortez42** | Backend Refactoring | Modularización de models, repositories, simulators |
| **Cortez41** | Backend Optimizations | O(n²)→O(n log n) con bisect, HTTP pooling, retry jitter |

**Correcciones destacadas de Cortez54**:
- `ExerciseRepository`: Añadidos `get_by_language_and_unit()`, `get_by_language()`, `get_languages_with_units()`
- `SimuladorProfesionalAgent`: Siempre pasar `simulator_type` al instanciar
- Manejo de datetime: Helper `_ensure_aware()` para comparar naive vs aware
- Session schemas: Aceptan mode en minúsculas ("tutor" → "TUTOR") vía validadores
- Codificación UTF-8: Clase `UTF8JSONResponse` con `ensure_ascii=False`
- get_current_user: Retorna dict con `user_id`, no objeto User

---

## 16. Comandos de Referencia

```bash
cd activia1-main                          # Navegar al proyecto
docker-compose up -d                      # Iniciar con Docker
docker-compose logs -f api                # Ver logs del backend
pytest tests/ -v --cov=backend            # Ejecutar tests
curl http://localhost:8000/api/v1/health  # Verificar health
make generate-secrets                     # Generar secretos seguros
```

---

## 17. Conclusión

El backend de AI-Native MVP representa una aproximación innovadora a la enseñanza de programación que prioriza el proceso de aprendizaje sobre el producto final. A través de sus seis agentes de IA especializados, el sistema proporciona tutorización adaptativa, evaluación de procesos cognitivos, simulación de contextos profesionales, análisis de riesgos multidimensional, gobernanza institucional automatizada y trazabilidad completa.

La arquitectura stateless del gateway central, combinada con el Repository Pattern para persistencia y el Factory Pattern para integración con LLMs, permite un sistema escalable, mantenible y extensible. La integración del Entrenador Digital con los agentes (Cortez50) demuestra cómo los módulos pueden evolucionar para aprovechar capacidades avanzadas manteniendo compatibilidad hacia atrás.

Las 60+ auditorías de código han refinado tanto la calidad del código como los patrones arquitectónicos empleados, resultando en un sistema robusto con manejo de errores consistente a través de excepciones personalizadas y observabilidad completa.

Este README proporciona una visión completa del sistema para desarrolladores que necesiten entender, mantener o extender el backend. Para información más detallada sobre endpoints específicos, consultar la documentación Swagger en `/docs` cuando el servidor está ejecutándose.

---

*Última actualización: Enero 2026 (Cortez60)*
