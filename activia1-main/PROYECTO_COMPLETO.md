# AI-Native MVP: Sistema Integral de Enseñanza-Aprendizaje con Inteligencia Artificial

## Introduccion

AI-Native MVP representa una innovacion fundamental en la forma de enseñar y aprender programacion. Este proyecto de tesis doctoral aborda uno de los desafios mas significativos de la educacion contemporanea: como integrar la inteligencia artificial generativa en el proceso de aprendizaje sin que esta reemplace el desarrollo genuino de competencias cognitivas en los estudiantes.

El sistema implementa un cambio de paradigma radical. Mientras que las herramientas tradicionales de asistencia por IA se enfocan en generar codigo automaticamente (evaluacion basada en producto), AI-Native evalua el proceso cognitivo que el estudiante atraviesa para resolver problemas. La pregunta fundamental que guia el sistema no es "¿Que codigo produjo el estudiante?" sino "¿Como llego el estudiante a esa solucion?"

Esta distincion es crucial en un momento historico donde herramientas como GitHub Copilot, ChatGPT y similares pueden generar codigo funcional instantaneamente. El verdadero valor educativo no reside en que el estudiante obtenga codigo correcto, sino en que desarrolle las estructuras mentales y habilidades de razonamiento que le permitiran ser un profesional competente a largo plazo.

---

## Arquitectura Multiagente

El corazon de AI-Native es un sistema de seis agentes de inteligencia artificial especializados que trabajan de forma coordinada para proporcionar una experiencia educativa integral.

### T-IA-Cog: El Tutor Cognitivo

El agente T-IA-Cog implementa un tutor que sigue principios pedagogicos estrictos. A diferencia de ChatGPT o Copilot, este agente nunca proporciona codigo completo como respuesta. En su lugar, utiliza cinco estrategias pedagogicas implementadas mediante el patron Strategy:

La **estrategia socratica** guia al estudiante mediante preguntas que lo llevan a descubrir la solucion por si mismo. Cuando un estudiante pregunta "¿Como ordeno una lista?", el tutor no responde con codigo, sino con preguntas como "¿Que significa que una lista este ordenada? ¿Puedes pensar en como un humano ordenaria una baraja de cartas?".

La **estrategia explicativa** proporciona conceptos teoricos cuando el estudiante necesita fundamentacion. Explica principios como recursividad, estructuras de datos o patrones de diseño, siempre separando la explicacion conceptual de la implementacion especifica.

La **estrategia guiada** ofrece pistas progresivas en cuatro niveles de ayuda (MINIMO, BAJO, MEDIO, ALTO). En el nivel minimo, solo ofrece una pregunta orientadora. En el nivel alto, puede proporcionar pseudocodigo o la estructura general de la solucion, pero nunca codigo ejecutable completo.

La **estrategia metacognitiva** ayuda al estudiante a reflexionar sobre su propio proceso de aprendizaje. Hace preguntas como "¿Que te llevo a probar esa aproximacion?" o "¿Que aprendiste de este error?".

La **estrategia de pistas contextuales para entrenamiento** (TrainingHintsStrategy, implementada en Cortez50) es especifica para el Entrenador Digital y proporciona ayuda contextualizada basada en el ejercicio actual, los errores especificos del estudiante y su historial de intentos.

### E-IA-Proc: El Evaluador de Procesos

Este agente representa quizas la contribucion mas innovadora del sistema. E-IA-Proc no evalua si el codigo funciona (eso lo hace cualquier compilador), sino como el estudiante llego a ese codigo.

El evaluador analiza la secuencia de trazas cognitivas capturadas durante la sesion: que problemas enfrento el estudiante, como los abordo, cuantas veces pidio ayuda, si copio codigo de fuentes externas, cuanto tiempo dedico a cada fase del desarrollo.

La evaluacion produce metricas en tres dimensiones: comprension conceptual (¿entiende los fundamentos?), aplicacion practica (¿puede aplicar los conceptos?), y metacognicion (¿reflexiona sobre su proceso?).

### S-IA-X: Los Simuladores Profesionales

El sistema incluye once simuladores que replican situaciones reales del mundo profesional del desarrollo de software. Cada simulador esta implementado como una estrategia independiente:

El **ProductOwnerSimulator** simula reuniones con un cliente que tiene requisitos vagos o cambiantes. El estudiante debe extraer requisitos claros mediante preguntas efectivas.

El **ScrumMasterSimulator** coloca al estudiante como parte de un equipo agil, enfrentando dailies, retrospectivas y situaciones de conflicto de equipo.

El **TechInterviewerSimulator** simula una entrevista tecnica realista, haciendo preguntas sobre algoritmos, estructuras de datos y problemas de diseño.

El **IncidentResponderSimulator** presenta emergencias de produccion donde el estudiante debe diagnosticar y resolver problemas bajo presion de tiempo.

El **DevSecOpsSimulator** simula auditorias de seguridad, vulnerabilidades y problemas de configuracion de infraestructura.

El **ClientSimulator** representa diferentes tipos de clientes con diversas personalidades y niveles de conocimiento tecnico.

Ademas existen simuladores para Code Reviewer, Architect, Tech Lead, Junior Developer y Legacy Code Expert.

### AR-IA: El Analista de Riesgos Cognitivos

Este agente monitorea constantemente la sesion del estudiante buscando señales de alarma que indiquen practicas de aprendizaje deficientes.

AR-IA detecta cinco dimensiones de riesgo:

1. **Riesgos epistemicos**: relacionados con el conocimiento y la comprension genuina.
2. **Riesgos tecnicos**: problemas en la calidad del codigo o practicas de desarrollo.
3. **Riesgos de autonomia**: dependencia excesiva de la IA o de fuentes externas.
4. **Riesgos de progreso**: estancamiento, frustacion o abandono.
5. **Riesgos de integridad**: posible plagio o uso no autorizado de codigo.

El sistema utiliza 16 tipos especificos de riesgo, incluyendo COPY_PASTE (deteccion de codigo pegado desde fuentes externas), HINT_DEPENDENCY (solicitud excesiva de pistas), RAPID_SUBMISSION (envio de codigo sin tiempo suficiente para haberlo desarrollado), y FRUSTRATION (patrones que indican frustracion del estudiante).

### GOV-IA: El Agente de Gobernanza

GOV-IA actua como coordinador central que decide que agente debe intervenir en cada momento y con que parametros. Implementa un sistema de semaforos (verde, amarillo, rojo) que controla el nivel de asistencia disponible para el estudiante basandose en su historial y comportamiento actual.

### TC-N4: El Agente de Trazabilidad

TC-N4 implementa un sistema de trazabilidad cognitiva con cuatro niveles de profundidad (N1 a N4):

- **N1 (Superficial)**: Registra acciones basicas como envios de codigo y solicitudes de ayuda.
- **N2 (Tecnico)**: Captura informacion sobre errores, tiempo dedicado y recursos utilizados.
- **N3 (Interaccional)**: Analiza patrones de interaccion con el sistema y los agentes.
- **N4 (Cognitivo Completo)**: Infiere estados cognitivos, cambios de estrategia, momentos de insight y frustracion.

---

## El Entrenador Digital (Digital Trainer)

El Entrenador Digital es un subsistema especializado que proporciona practica estructurada con ejercicios de programacion. A diferencia del modo Tutor (que es conversacional y abierto), el Entrenador guia al estudiante a traves de ejercicios especificos con objetivos claros.

### Flujo del Entrenador

El estudiante selecciona un lenguaje de programacion (Python, JavaScript, Java, etc.), una unidad tematica y una leccion especifica. El sistema presenta ejercicios ordenados por dificultad dentro de cada leccion.

Para cada ejercicio, el estudiante recibe:
- Una descripcion del problema
- Codigo inicial (plantilla)
- Casos de prueba que debe satisfacer
- Acceso a pistas estaticas o contextuales

El estudiante escribe su solucion en un editor de codigo integrado y la envia para evaluacion. El sistema ejecuta los casos de prueba y proporciona retroalimentacion inmediata.

### Integracion con Agentes (Cortez50)

En la version V2 del Entrenador (implementada en Cortez50), existe integracion profunda con los agentes del sistema:

El **TrainingGateway** actua como orquestador central que conecta las operaciones del Entrenador con los agentes apropiados.

El **TrainingTraceCollector** captura trazas cognitivas durante los ejercicios, infiriendo estados como EXPLORACION (el estudiante esta entendiendo el problema), IMPLEMENTACION (esta escribiendo codigo), DEPURACION (esta corrigiendo errores), o ESTANCAMIENTO (no hace progreso).

El **TrainingRiskMonitor** detecta riesgos en tiempo real durante los ejercicios, como copiar-pegar codigo externo o solicitar demasiadas pistas.

### Endpoints V1 y V2

El Entrenador expone dos versiones de endpoints:

**Version V1** (endpoints legacy para compatibilidad):
- `GET /training/lenguajes` - Obtiene la estructura jerarquica de contenido
- `POST /training/iniciar` - Inicia una sesion de entrenamiento
- `POST /training/submit-ejercicio` - Envia codigo para evaluacion
- `POST /training/corregir-ia` - Solicita correccion asistida por IA
- `POST /training/pista` - Solicita una pista estatica
- `GET /training/sesion/{id}/estado` - Obtiene estado con campos N4

**Version V2** (endpoints con integracion de agentes):
- `POST /training/pista/v2` - Pistas contextuales usando T-IA-Cog
- `POST /training/reflexion` - Captura reflexiones del estudiante
- `GET /training/sesion/{id}/proceso` - Analisis de proceso con metricas cognitivas
- `POST /training/submit/v2` - Envio extendido con trazabilidad N4

---

## Funcionalidades para Docentes

El analisis del proyecto revela un panorama asimetrico respecto a las funcionalidades para docentes. El backend esta practicamente completo, pero el frontend carece de las interfaces necesarias.

### Historias de Usuario del Docente

El proyecto define diez historias de usuario para docentes (HU-DOC-001 a HU-DOC-010):

**HU-DOC-001: Dashboard de Supervision**
El docente necesita ver un resumen ejecutivo de todos sus estudiantes: quienes estan activos, quienes tienen dificultades, alertas de riesgo pendientes.

**HU-DOC-002: Monitoreo en Tiempo Real**
Durante una clase o laboratorio, el docente quiere ver que estan haciendo los estudiantes en ese momento: quien esta trabajando, quien esta estancado, quien ha completado los ejercicios.

**HU-DOC-003: Reportes de Cohorte**
El docente necesita generar reportes agregados de una clase completa: distribucion de notas, temas donde hay mas dificultad, estudiantes en riesgo academico.

**HU-DOC-004: Reportes Individuales**
Para tutoria o evaluacion individual, el docente necesita ver el historial completo de un estudiante: sesiones, ejercicios completados, riesgos detectados, patron de uso de ayuda.

**HU-DOC-005: Gestion de Alertas Institucionales**
Cuando el sistema detecta situaciones serias (posible plagio, estudiante sin actividad prolongada, patron de frustracion severo), el docente debe recibir alertas y poder actuar.

**HU-DOC-006: Administracion de Actividades**
El docente necesita crear, modificar y asignar actividades a sus cursos: trabajos practicos, ejercicios, simulaciones.

**HU-DOC-007: Configuracion de Ejercicios**
El docente debe poder crear nuevos ejercicios con sus casos de prueba, pistas y rubricas de evaluacion.

**HU-DOC-008: Exportacion de Datos**
Para investigacion o reportes institucionales, el docente necesita exportar datos anonimizados de las sesiones.

**HU-DOC-009: Comparativa entre Cohortes**
El docente quiere comparar el rendimiento de diferentes años o secciones para identificar mejoras o problemas.

**HU-DOC-010: Analisis de Efectividad Pedagogica**
El docente necesita metricas sobre que estrategias del tutor son mas efectivas, que tipos de ejercicios generan mas aprendizaje.

### Estado de Implementacion Backend

El backend proporciona todos los servicios necesarios para estas funcionalidades:

El **TeacherToolsService** (`backend/services/teacher_tools_service.py`) implementa:
- `get_active_students()` - Estudiantes actualmente trabajando
- `get_students_at_risk()` - Estudiantes con alertas de riesgo
- `get_completion_summary()` - Resumen de actividades completadas
- `get_live_activity_feed()` - Feed de actividad en tiempo real

El **ReportsService** (`backend/services/reports_service.py`) genera:
- Reportes de cohorte con metricas agregadas
- Reportes individuales con historial completo
- Analisis de riesgo por grupo
- Exportacion anonimizada

El **InstitutionalRisksService** (`backend/services/institutional_risks_service.py`) gestiona:
- Alertas de riesgo institucional
- Planes de remediacion
- Seguimiento de intervenciones

Los **routers** correspondientes estan implementados:
- `/api/v1/teacher-tools/*` - Herramientas docentes
- `/api/v1/reports/*` - Generacion de reportes
- `/api/v1/activities/*` - Gestion de actividades

### Estado de Implementacion Frontend

El frontend tiene los servicios API definidos pero sin interfaces que los consuman:

El archivo `frontEnd/src/services/api/institutionalRisks.service.ts` define metodos para:
- Obtener alertas de riesgo
- Crear planes de remediacion
- Actualizar estado de alertas

El archivo `frontEnd/src/services/api/reports.service.ts` define metodos para:
- Generar reportes de cohorte
- Obtener reportes individuales
- Exportar datos

**Sin embargo, no existen las paginas correspondientes:**

Las siguientes paginas estan ausentes del frontend:
- `TeacherDashboardPage` - Dashboard principal del docente
- `ReportsPage` - Interfaz para generar y ver reportes
- `InstitutionalRisksPage` - Gestion de alertas y riesgos
- `StudentMonitoringPage` - Monitoreo en tiempo real
- `ActivityManagementPage` - Gestion de actividades

---

## Stack Tecnologico

### Backend

El backend esta construido con Python 3.11 y FastAPI, utilizando una arquitectura limpia con separacion clara entre capas:

- **Capa de API** (`backend/api/`): Routers, schemas Pydantic, middleware
- **Capa de Servicios** (`backend/services/`): Logica de negocio
- **Capa de Core** (`backend/core/`): Orquestadores y motor cognitivo
- **Capa de Agentes** (`backend/agents/`): Implementacion de los 6 agentes
- **Capa de Datos** (`backend/database/`): Modelos ORM, repositorios, migraciones
- **Capa de LLM** (`backend/llm/`): Abstraccion de proveedores de IA

Los proveedores de LLM soportados son:
- **Ollama** con Phi-3 (local, gratuito)
- **Google Gemini** (API cloud)
- **OpenAI** (API cloud)
- **Mistral** (API cloud)
- **Mock** (para desarrollo y testing)

La persistencia utiliza PostgreSQL para produccion con SQLAlchemy como ORM, y Redis para cache y rate limiting.

### Frontend

El frontend utiliza React 19 con TypeScript, construido con Vite. La arquitectura sigue patrones modernos:

- **Feature-based structure** (`src/features/`): Cada funcionalidad mayor tiene su carpeta
- **Domain types** (`src/types/domain/`): Tipos TypeScript alineados con el backend
- **Core HTTP** (`src/core/http/`): Cliente HTTP con circuit breaker y metricas
- **Shared config** (`src/shared/config/`): Configuraciones y constantes compartidas

El estado se gestiona con Zustand para estado global (UI, sesion) y hooks locales para estado de componentes.

### Infraestructura

El proyecto incluye infraestructura completa para desarrollo y produccion:

- **Docker Compose** modular con perfiles para desarrollo, debug, monitoring
- **Kubernetes** manifests para staging y produccion
- **GitHub Actions** CI/CD con 14 stages de pipeline
- **Prometheus + Grafana** para monitoring
- **OWASP ZAP, Trivy, TruffleHog** para security scanning

---

## Trazabilidad Cognitiva N4

El sistema de trazabilidad es uno de los aportes mas significativos del proyecto. Cada accion del estudiante genera trazas que son procesadas para inferir su estado cognitivo.

### Modelo Hibrido

El sistema utiliza un modelo hibrido de captura de trazas:

1. **Trazas inferidas (pasivas)**: El sistema deduce automaticamente el estado cognitivo basandose en las acciones. Por ejemplo, multiples intentos fallidos seguidos de un cambio significativo en el codigo sugieren un "cambio de estrategia".

2. **Trazas opcionales (semi-activas)**: El estudiante puede opcionalmente proporcionar informacion adicional, como marcar que tipo de ayuda necesita.

3. **Trazas de reflexion (activas)**: Al finalizar un ejercicio, el sistema invita al estudiante a reflexionar sobre su proceso, generando trazas de alto valor cognitivo.

### Estados Cognitivos

El sistema reconoce nueve estados cognitivos:

- **INICIO**: Comenzando a entender el problema
- **EXPLORACION**: Analizando opciones y enfoques
- **IMPLEMENTACION**: Escribiendo codigo activamente
- **DEPURACION**: Corrigiendo errores
- **CAMBIO_ESTRATEGIA**: Abandonando un enfoque por otro
- **VALIDACION**: Verificando la solucion
- **ESTANCAMIENTO**: Sin progreso significativo
- **REFLEXION**: Pensando sobre el proceso
- **FINALIZACION**: Completando la tarea

### Dimensiones de Riesgo

Las trazas alimentan el analisis de riesgo en cinco dimensiones:

1. **Autonomia**: ¿El estudiante resuelve problemas independientemente o depende excesivamente de ayuda?
2. **Comprension**: ¿Las acciones reflejan comprension genuina o copia mecanica?
3. **Progreso**: ¿Hay avance constante o estancamiento?
4. **Integridad**: ¿El trabajo es original o hay indicios de plagio?
5. **Engagement**: ¿El estudiante esta comprometido o desmotivado?

---

## Pipeline CI/CD

El proyecto cuenta con un pipeline de integracion y despliegue continuo de 14 etapas:

1. **Lint** - Analisis estatico de Python y TypeScript
2. **Backend Tests** - Tests unitarios e integracion con PostgreSQL y Redis
3. **Frontend Tests** - Tests con Vitest
4. **Security Scan** - Bandit, Trivy, TruffleHog
5. **Database Migrations** - Validacion de migraciones
6. **Exercise Validation** - Validacion del catalogo de ejercicios
7. **LLM Health Check** - Verificacion de proveedores LLM
8. **API Contract Testing** - Validacion OpenAPI y breaking changes
9. **Performance Testing** - Tests de carga con k6
10. **E2E Training Flow** - Tests end-to-end del Entrenador
11. **Build Backend Image** - Construccion de imagen Docker
12. **Build Frontend Image** - Construccion de imagen Docker
13. **Deploy Staging** - Despliegue automatico a staging
14. **Deploy Production** - Despliegue a produccion (solo main)

---

## Metricas y Logros

El proyecto ha alcanzado metricas significativas:

- **73% cobertura de tests** (objetivo: 70%)
- **0 vulnerabilidades criticas** en security audit
- **94% SLA compliance** en tests de carga
- **SUS Score 72.5** en usabilidad
- **NPS 60** en satisfaccion de usuarios
- **57,500+ lineas** de codigo y documentacion
- **60+ auditorias** de codigo realizadas

---

## Trabajo Pendiente

### Prioridad Alta: Frontend Docente

La implementacion de las interfaces de docente es el trabajo mas critico pendiente:

1. **TeacherDashboardPage**: Crear pagina principal con resumen de estudiantes, alertas pendientes y accesos rapidos.

2. **StudentMonitoringPage**: Implementar vista de monitoreo en tiempo real con WebSocket para actualizaciones.

3. **ReportsPage**: Desarrollar interfaz para generacion y visualizacion de reportes.

4. **InstitutionalRisksPage**: Crear sistema de gestion de alertas con workflow de resolucion.

### Prioridad Media: Mejoras de UX

- Mejorar la experiencia del editor de codigo en el Entrenador
- Agregar visualizaciones de progreso mas detalladas
- Implementar notificaciones push para alertas

### Prioridad Baja: Optimizaciones

- Migrar estilos inline a Tailwind CSS
- Resolver patrones `key={index}` restantes en listas dinamicas
- Completar extraccion de coordinadores en AIGateway

---

## Conclusion

AI-Native MVP representa un avance significativo en la educacion de programacion. El sistema demuestra que es posible utilizar inteligencia artificial como un aliado pedagogico que potencia el aprendizaje genuino en lugar de reemplazarlo.

El proyecto tiene un backend robusto y completo, un frontend funcional para estudiantes, y una arquitectura escalable preparada para produccion. El trabajo pendiente mas significativo es completar las interfaces de docente para habilitar la supervision y gestion academica.

Con sus seis agentes especializados, su sistema de trazabilidad cognitiva N4, y su enfoque en evaluacion de procesos, AI-Native ofrece una alternativa viable al uso indiscriminado de herramientas de generacion de codigo en entornos educativos.

---

*Documento generado como parte del analisis del proyecto AI-Native MVP - Enero 2026*
