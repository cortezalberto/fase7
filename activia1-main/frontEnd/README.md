# AI-Native Student Frontend

## Documentacion Tecnica del Sistema Frontend

**Version**: 2.1.0
**Actualizacion**: Enero 2026 (Cortez63)
**Stack Tecnologico**: React 19 · TypeScript 5.7 · Vite 6 · Zustand 5 · Tailwind CSS 3

---

## Tabla de Contenidos

1. [Vision General del Sistema](#1-vision-general-del-sistema)
2. [Arquitectura de la Aplicacion](#2-arquitectura-de-la-aplicacion)
3. [Estructura de Directorios](#3-estructura-de-directorios)
4. [Punto de Entrada y Enrutamiento](#4-punto-de-entrada-y-enrutamiento)
5. [Sistema de Autenticacion](#5-sistema-de-autenticacion)
6. [Gestion de Estado con Zustand](#6-gestion-de-estado-con-zustand)
7. [Cliente HTTP y Servicios](#7-cliente-http-y-servicios)
8. [Panel del Docente (Teacher Management)](#8-panel-del-docente-teacher-management)
9. [Modulos de Funcionalidades (Features)](#9-modulos-de-funcionalidades-features)
10. [Sistema de Tipos TypeScript](#10-sistema-de-tipos-typescript)
11. [Componentes Compartidos](#11-componentes-compartidos)
12. [Hooks Personalizados](#12-hooks-personalizados)
13. [Patrones de React 19](#13-patrones-de-react-19)
14. [Accesibilidad y Estandares Web](#14-accesibilidad-y-estandares-web)
15. [Rendimiento y Optimizacion](#15-rendimiento-y-optimizacion)
16. [Testing y Calidad](#16-testing-y-calidad)
17. [Configuracion y Desarrollo](#17-configuracion-y-desarrollo)

---

## 1. Vision General del Sistema

El frontend de AI-Native constituye la interfaz principal mediante la cual los estudiantes interactuan con un ecosistema de agentes de inteligencia artificial diseñado para la enseñanza-aprendizaje de programacion. Este sistema forma parte de un proyecto de tesis doctoral cuyo objetivo central radica en la evaluacion basada en procesos cognitivos, en contraposicion a las aproximaciones tradicionales que evaluan unicamente el producto final del codigo.

La arquitectura del frontend se sustenta sobre el concepto de trazabilidad cognitiva N4, un modelo que permite capturar y analizar el recorrido mental del estudiante mientras resuelve problemas de programacion. Esta trazabilidad opera en cuatro niveles: datos crudos de entrada, preprocesamiento, inferencia del modelo de lenguaje, y postprocesamiento para generar respuestas pedagogicamente apropiadas.

El sistema interactua con seis agentes especializados en el backend:

El **T-IA-Cog** (Tutor Cognitivo) actua como mentor personalizado que adapta su estilo pedagogico segun el estado cognitivo del estudiante, operando en cinco modos distintos: socratico para fomentar el pensamiento critico, explicativo para conceptos complejos, guiado con pistas graduales, metacognitivo para la reflexion sobre el aprendizaje, y entrenamiento con ejercicios estructurados.

El **E-IA-Proc** (Evaluador de Procesos) analiza no solo la correccion del codigo sino el proceso de razonamiento que llevo al estudiante a esa solucion, evaluando dimensiones como funcionalidad, calidad del codigo y robustez.

El **S-IA-X** (Simuladores Profesionales) ofrece once escenarios de simulacion que replican situaciones reales del desarrollo de software, desde entrevistas tecnicas hasta gestion de incidentes y ceremonias agiles.

El **AR-IA** (Analizador de Riesgos) monitorea cinco dimensiones de riesgo en el uso de IA educativa: cognitiva, etica, epistemica, tecnica y de gobernanza.

El **GOV-IA** (Gobernanza) supervisa las interacciones mediante un sistema de semaforos que regula el nivel de autonomia del estudiante.

El **TC-N4** (Trazabilidad Cognitiva) registra cada paso del proceso de aprendizaje para analisis posterior y mejora continua del sistema.

---

## 2. Arquitectura de la Aplicacion

La arquitectura del frontend sigue un patron modular basado en caracteristicas (feature-based architecture) que organiza el codigo segun dominios funcionales en lugar de tipos tecnicos. Esta organizacion facilita la escalabilidad del proyecto y permite que equipos trabajen en paralelo sobre diferentes funcionalidades sin generar conflictos.

### Diagrama de Capas

```
+------------------------------------------------------------------+
|                        CAPA DE PRESENTACION                       |
|  +--------------+ +--------------+ +--------------+ +------------+|
|  |   Paginas    | |   Features   | |  Componentes | |  Layouts   ||
|  |   (Routes)   | |  (Dominios)  | |  (Shared UI) | |  (Shells)  ||
|  +--------------+ +--------------+ +--------------+ +------------+|
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                        CAPA DE LOGICA                             |
|  +--------------+ +--------------+ +--------------+ +------------+|
|  |    Hooks     | |   Contextos  | |    Stores    | |   Utils    ||
|  |  (Stateful)  | |    (Auth)    | |   (Zustand)  | |  (Helpers) ||
|  +--------------+ +--------------+ +--------------+ +------------+|
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                       CAPA DE SERVICIOS                           |
|  +--------------+ +--------------+ +--------------+ +------------+|
|  |  HttpClient  | | API Services | |   Circuit    | |  Request   ||
|  |   (Axios)    | |   (Domain)   | |   Breaker    | |   Queue    ||
|  +--------------+ +--------------+ +--------------+ +------------+|
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                      CAPA DE TIPOS                                |
|  +--------------------------------------------------------------+ |
|  |  Domain Types (11 modulos): session, interaction, trace,     | |
|  |  risk, evaluation, activity, simulator, git, enums, etc.     | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Principios Arquitectonicos

El sistema adhiere a principios de diseño que garantizan mantenibilidad y escalabilidad. El principio de responsabilidad unica se manifiesta en la separacion entre componentes de presentacion (sin logica de negocio), hooks personalizados (logica de estado y efectos), y servicios (comunicacion con API). El principio de inversion de dependencias se implementa mediante la inyeccion de servicios a traves de los modulos de configuracion.

La gestion del estado sigue una estrategia hibrida donde Zustand maneja el estado global de la interfaz (tema, sidebar) y el estado de sesion de aprendizaje, mientras que el estado local de los componentes se gestiona con hooks nativos de React. Esta combinacion optimiza el rendimiento al minimizar re-renderizados innecesarios.

---

## 3. Estructura de Directorios

La organizacion del codigo fuente refleja la arquitectura modular del sistema. Cada directorio tiene un proposito especifico y contiene codigo relacionado semanticamente.

```
frontEnd/src/
|-- components/              # Componentes de infraestructura
|   |-- Layout.tsx           # Shell principal con navegacion dual
|   |-- ProtectedRoute.tsx   # Guard de autenticacion
|   |-- ErrorBoundary.tsx    # Captura de errores con navegacion
|   +-- exercises/           # Componentes del evaluador Alex
|
|-- contexts/                # Contextos de React (migrado a Zustand)
|   +-- AuthContext.tsx      # Autenticacion con React 19 use()
|
|-- core/                    # Infraestructura central
|   |-- config/              # Configuracion de rutas y endpoints
|   +-- http/                # Cliente HTTP con resiliencia
|       |-- HttpClient.ts    # Axios + Circuit Breaker + Retry
|       |-- CircuitBreaker.ts
|       |-- HttpMetrics.ts
|       +-- RequestQueue.ts
|
|-- features/                # Modulos por dominio funcional
|   |-- training/            # Entrenador Digital
|   |   |-- components/      # UI especifica de entrenamiento
|   |   +-- hooks/           # useTrainingSession, useTimer
|   |
|   |-- tutor/               # Chat con T-IA-Cog
|   |   |-- components/      # ChatInput, MessageBubble, etc.
|   |   +-- hooks/           # useTutorSession, useRiskAnalysis
|   |
|   |-- simulators/          # S-IA-X Profesionales
|   |   |-- components/      # SimulatorCard, SimulatorGrid
|   |   +-- config/          # Configuracion de 11 simuladores
|   |
|   |-- risks/               # AR-IA Analisis 5D
|   |   +-- components/      # RiskAnalyzer, DimensionCard
|   |
|   +-- traceability/        # TC-N4 Visualizacion
|       +-- components/      # TraceabilityViewer, TraceNodeCard
|
|-- pages/                   # Componentes de ruta (lazy loaded)
|   |-- DashboardPage.tsx    # Panel principal estudiante
|   |-- TutorPage.tsx        # Interfaz de chat tutorizado
|   |-- TrainingPage.tsx     # Selector de ejercicios
|   |-- TrainingExamPage.tsx # Modo examen con temporizador
|   |-- SimulatorsPage.tsx   # Hub de simuladores
|   |-- AnalyticsPage.tsx    # Metricas de progreso
|   |-- TeacherDashboardPage.tsx  # Panel docente
|   |-- ReportsPage.tsx      # Generacion de reportes
|   |-- InstitutionalRisksPage.tsx  # Riesgos institucionales
|   |-- StudentMonitoringPage.tsx   # Monitoreo de estudiantes
|   +-- ActivityManagementPage.tsx  # Gestion de actividades
|
|-- services/api/            # Servicios de comunicacion
|   |-- index.ts             # Exports centralizados
|   |-- base.service.ts      # Clase base con metodos CRUD
|   |-- client.ts            # Instancia configurada de Axios
|   |-- sessions.service.ts  # Gestion de sesiones
|   |-- training.service.ts  # Entrenador Digital (V1 + V2)
|   |-- simulators.service.ts# Simuladores profesionales
|   |-- evaluations.service.ts # Evaluaciones E-IA-Proc
|   |-- risks.service.ts     # Analisis de riesgos AR-IA
|   |-- traces.service.ts    # Trazabilidad TC-N4
|   |-- reports.service.ts   # Reportes docentes
|   +-- institutionalRisks.service.ts # Riesgos institucionales
|
|-- shared/                  # Codigo compartido
|   |-- components/          # Toast, Modal, LoadingSpinner
|   +-- config/              # Labels, colors, constants
|
|-- stores/                  # Estado global Zustand
|   |-- index.ts             # Exports centralizados
|   |-- uiStore.ts           # Tema y sidebar (persistido)
|   +-- sessionStore.ts      # Sesion de aprendizaje activa
|
|-- types/                   # Definiciones TypeScript
|   |-- index.ts             # Tipos del usuario (legacy)
|   +-- domain/              # Tipos modulares por dominio
|       |-- enums.ts         # Enumeraciones centralizadas
|       |-- session.types.ts
|       |-- interaction.types.ts
|       |-- trace.types.ts
|       |-- risk.types.ts
|       |-- evaluation.types.ts
|       |-- activity.types.ts
|       |-- simulator.types.ts
|       |-- git.types.ts
|       +-- api.types.ts     # Wrappers de respuesta API
|
|-- App.tsx                  # Punto de entrada con rutas
+-- main.tsx                 # Bootstrap de React
```

---

## 4. Punto de Entrada y Enrutamiento

El archivo `App.tsx` constituye el nucleo del sistema de navegacion, implementando un esquema de rutas protegidas con lazy loading para optimizar el tiempo de carga inicial.

### Jerarquia de Proveedores

La aplicacion envuelve todos los componentes en una jerarquia de proveedores que proporciona funcionalidades transversales:

```tsx
<ErrorBoundary>           // Captura errores no manejados
  <AuthProvider>          // Estado de autenticacion
    <ToastProvider>       // Sistema de notificaciones
      <BrowserRouter>     // Navegacion cliente
        <Routes>          // Definicion de rutas
```

El `ErrorBoundary` externo captura cualquier error de JavaScript que ocurra en el arbol de componentes, mostrando una interfaz de recuperacion en lugar de una pagina en blanco. El componente `ErrorBoundaryWithNavigation` extiende esta funcionalidad para permitir navegacion mediante React Router cuando ocurre un error.

### Lazy Loading de Paginas

Todas las paginas no criticas se cargan dinamicamente mediante `React.lazy()`, reduciendo el bundle inicial en aproximadamente un 60%:

```tsx
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TutorPage = lazy(() => import('./pages/TutorPage'));
const SimulatorsPage = lazy(() => import('./pages/SimulatorsPage'));
```

Las paginas de autenticacion (`LoginPage`, `RegisterPage`) se cargan de forma sincrona para garantizar una experiencia de primer contacto fluida.

### Sistema de Rutas Dual

El sistema implementa navegacion diferenciada para estudiantes y docentes. Las rutas de estudiante ocupan el espacio raiz:

| Ruta | Componente | Proposito |
|------|------------|-----------|
| `/dashboard` | DashboardPage | Panel principal con metricas |
| `/tutor` | TutorPage | Chat con T-IA-Cog |
| `/training` | TrainingPage | Selector de ejercicios |
| `/training/exam` | TrainingExamPage | Modo examen temporizado |
| `/simulators` | SimulatorsPage | Hub de 11 simuladores |
| `/analytics` | AnalyticsPage | Analisis de progreso |
| `/evaluator` | EvaluatorPage | Evaluacion E-IA-Proc |
| `/risks` | RisksPage | Analisis de riesgos AR-IA |
| `/traceability` | TraceabilityPage | Visualizacion N4 |
| `/git` | GitAnalyticsPage | Metricas de Git |

Las rutas de docente se agrupan bajo el prefijo `/teacher`:

| Ruta | Componente | Historia de Usuario |
|------|------------|---------------------|
| `/teacher/dashboard` | TeacherDashboardPage | HU-DOC-001 |
| `/teacher/monitoring` | StudentMonitoringPage | HU-DOC-003 |
| `/teacher/activities` | ActivityManagementPage | HU-DOC-005 |
| `/teacher/reports` | ReportsPage | HU-DOC-007 |
| `/teacher/risks` | InstitutionalRisksPage | HU-DOC-009 |

---

## 5. Sistema de Autenticacion

La autenticacion se implementa mediante un contexto de React que aprovecha las capacidades del hook `use()` introducido en React 19 para leer valores de contexto de forma mas elegante.

### AuthContext y AuthProvider

El `AuthProvider` encapsula la logica de autenticacion basada en tokens JWT:

```tsx
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const checkAuth = async () => {
      const token = authService.getAccessToken();
      if (token) {
        const cachedUser = authService.getCurrentUser();
        if (isMounted) setUser(toUser(cachedUser));
      }
      if (isMounted) setIsLoading(false);
    };

    checkAuth();
    return () => { isMounted = false; };
  }, []);
```

El patron `isMounted` previene actualizaciones de estado despues del desmontaje del componente, evitando memory leaks que podrian ocurrir si el componente se desmonta durante una operacion asincrona.

### Hook useAuth con React 19

El hook personalizado `useAuth` utiliza el nuevo hook `use()` de React 19 para leer el contexto:

```tsx
export function useAuth(): AuthContextType {
  const context = use(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

Esta aproximacion ofrece mejor manejo de errores y tipos mas precisos comparado con `useContext`.

### Flujo de Autenticacion

1. El usuario ingresa credenciales en `LoginPage`
2. El `authService` envia una solicitud POST a `/auth/login`
3. El backend valida y retorna tokens JWT (access + refresh)
4. Los tokens se almacenan en localStorage
5. El `AuthProvider` actualiza el estado del usuario
6. El `ProtectedRoute` permite acceso a rutas protegidas

---

## 6. Gestion de Estado con Zustand

La migracion de Context API a Zustand (implementada en Cortez31) simplifico significativamente la gestion del estado global. Zustand ofrece una API mas concisa, mejor rendimiento mediante suscripciones selectivas, y persistencia integrada.

### UI Store

El `uiStore` gestiona preferencias de interfaz que persisten entre sesiones:

```tsx
interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarCollapsed: false,
      toggleTheme: () => set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
    }),
    { name: 'ui-storage' }
  )
);
```

El middleware `persist` serializa automaticamente el estado a localStorage, restaurandolo cuando la aplicacion se recarga.

### Session Store

El `sessionStore` mantiene informacion sobre la sesion de aprendizaje activa:

```tsx
interface ActiveSession {
  id: string;
  mode: SessionMode;
  activityId?: string;
  startedAt: Date;
}

export const useSessionStore = create<SessionState>((set) => ({
  currentSession: null,
  setSession: (session) => set({ currentSession: session }),
  clearSession: () => set({ currentSession: null }),
}));
```

### Hooks Selectores

Para optimizar re-renderizados, el sistema exporta hooks selectores que extraen porciones especificas del estado:

```tsx
// Selector especifico - solo re-renderiza cuando cambia el tema
export const useTheme = () => useUIStore((s) => s.theme);

// Selector especifico - solo re-renderiza cuando cambia el sidebar
export const useSidebarCollapsed = () => useUIStore((s) => s.sidebarCollapsed);
```

---

## 7. Cliente HTTP y Servicios

La comunicacion con el backend se centraliza en un cliente HTTP robusto que implementa patrones de resiliencia inspirados en arquitecturas de microservicios.

### HttpClient con Circuit Breaker

El `HttpClient` encapsula Axios con funcionalidades avanzadas:

```tsx
export class HttpClient {
  private circuitBreaker: CircuitBreakerState = {
    failures: 0,
    lastFailure: 0,
    state: 'CLOSED'
  };

  private readonly FAILURE_THRESHOLD = 5;
  private readonly CIRCUIT_RESET_TIME = 60000;
  private readonly RETRY_ATTEMPTS = 3;
```

El patron Circuit Breaker previene cascadas de fallos cuando el backend no esta disponible. Despues de 5 fallos consecutivos, el circuito se "abre" y rechaza inmediatamente las solicitudes durante 60 segundos, permitiendo que el sistema se recupere.

### Retry con Backoff Exponencial

Las solicitudes fallidas se reintentan automaticamente con tiempos de espera crecientes:

```tsx
private calculateBackoff(retryCount: number): number {
  const baseDelay = 1000;
  const exponentialDelay = baseDelay * Math.pow(2, retryCount - 1);
  const jitter = Math.random() * 200;
  return Math.min(exponentialDelay + jitter, 10000);
}
```

El jitter (variacion aleatoria) previene el "thundering herd problem" donde multiples clientes reintentan simultaneamente.

### Servicios de Dominio

Cada dominio del sistema tiene un servicio dedicado que encapsula las operaciones de API:

| Servicio | Responsabilidad |
|----------|-----------------|
| `sessionsService` | Ciclo de vida de sesiones de aprendizaje |
| `interactionsService` | Envio y recepcion de mensajes con IA |
| `tracesService` | Consulta de trazabilidad cognitiva |
| `risksService` | Analisis de riesgos 5D |
| `trainingService` | Entrenador Digital (V1 + V2 con N4) |
| `simulatorsService` | Operaciones de simuladores S-IA-X |
| `evaluationsService` | Evaluaciones E-IA-Proc |
| `reportsService` | Generacion de reportes docentes |
| `institutionalRisksService` | Gestion de alertas y planes de remediacion |
| `teacherTraceabilityService` | Trazabilidad N4 de estudiantes para docentes (Cortez63) |

### Training Service V2 (Cortez55)

El servicio de entrenamiento implementa dos versiones de API para soportar la transicion gradual a trazabilidad N4:

```tsx
// V1: Endpoints originales
solicitarPista(request: SolicitarPistaRequest): Promise<PistaResponse>
submitEjercicio(request: SubmitEjercicioRequest): Promise<SubmitEjercicioResponse>

// V2: Endpoints con trazabilidad N4
solicitarPistaV2(request: SolicitarPistaV2Request): Promise<PistaV2Response>
submitEjercicioV2(request: SubmitEjercicioV2Request): Promise<SubmitEjercicioV2Response>
capturarReflexion(request: ReflexionRequest): Promise<ReflexionResponse>
obtenerProcesoAnalisis(sessionId: string): Promise<ProcesoAnalisis>
```

---

## 8. Panel del Docente (Teacher Management)

El sistema incluye un conjunto completo de funcionalidades para docentes que permiten supervisar el progreso de los estudiantes, gestionar actividades, detectar riesgos y generar reportes. Estas funcionalidades se implementaron en **Cortez60** y estan accesibles bajo el prefijo `/teacher` para usuarios con rol `teacher` o `admin`.

### 8.1 Arquitectura del Panel Docente

Las paginas del docente siguen el mismo patron arquitectonico que el resto del frontend, con componentes aislados, hooks para logica de estado, y servicios para comunicacion con el backend. La navegacion del docente se muestra condicionalmente en el sidebar del `Layout.tsx` basandose en el rol del usuario:

```tsx
const isTeacher = user?.roles?.some(
  (role: string) => role.toLowerCase() === 'teacher' ||
                    role.toLowerCase() === 'docente' ||
                    role.toLowerCase() === 'admin'
);
```

### 8.2 TeacherDashboardPage - Panel Principal

**Ubicacion**: [pages/TeacherDashboardPage.tsx](src/pages/TeacherDashboardPage.tsx)
**Historias de Usuario**: HU-DOC-001 (Dashboard de Supervision), HU-DOC-002 (Monitoreo en Tiempo Real)

El panel principal del docente proporciona una vision consolidada del estado de sus estudiantes y el sistema educativo. Al cargar, realiza tres solicitudes en paralelo usando `Promise.allSettled` para garantizar que la pagina se renderice aunque alguna de ellas falle:

```tsx
const [alertsRes, analyticsRes, riskRes] = await Promise.allSettled([
  apiClient.get<{ data: AlertsResponse }>('/teacher/alerts'),
  reportsService.getLearningAnalytics('month'),
  institutionalRisksService.getDashboard(),
]);
```

**Metricas principales mostradas:**
- Estudiantes activos este mes
- Sesiones totales con duracion promedio
- Alertas activas (con indicador de criticas)
- Riesgos pendientes y resueltos esta semana

**Acciones rapidas:**
- Monitoreo en Vivo: Ver estudiantes activos en tiempo real
- Generar Reportes: Reportes de cohorte y rendimiento
- Gestion de Riesgos: Alertas y planes de remediacion
- Actividades: Gestionar actividades y ejercicios

**Alertas recientes**: Muestra las 5 alertas mas recientes con severidad, razon, actividad y duracion. Cada alerta incluye un enlace para ver el detalle del estudiante en la pagina de monitoreo.

**Uso de Agentes IA**: Grafico de barras mostrando los agentes mas utilizados por los estudiantes (T-IA-Cog, S-IA-X, etc.).

### 8.3 StudentMonitoringPage - Monitoreo en Tiempo Real

**Ubicacion**: [pages/StudentMonitoringPage.tsx](src/pages/StudentMonitoringPage.tsx)
**Historias de Usuario**: HU-DOC-002, HU-DOC-003 (Comparacion de Estudiantes), HU-DOC-004 (Alertas en Tiempo Real)

Esta pagina permite al docente supervisar estudiantes activos y responder a situaciones que requieren intervencion. Implementa tres vistas seleccionables mediante tabs:

**Vista de Alertas**: Lista todas las alertas de estudiantes con filtros por severidad (critical, high, medium). Cada alerta muestra:
- ID del estudiante y severidad
- Razones de la alerta (ej: "Dependencia excesiva de IA", "Sesion muy larga")
- Metricas: duracion, interacciones totales, dependencia de IA
- Sugerencias pedagogicas
- Boton "Atender" para reconocer la alerta

**Vista de Sesiones Activas**: Lista en tiempo real todas las sesiones activas con:
- ID del estudiante
- Modo de sesion (TUTOR, SIMULATOR, TRAINING)
- Actividad en la que trabaja
- Hora de inicio
- Numero de trazas generadas

**Vista de Comparacion**: Permite comparar el rendimiento de multiples estudiantes en una misma actividad. Ingresando un ID de actividad, muestra:
- Estadisticas agregadas (promedio de duracion, interacciones, dependencia IA)
- Tabla detallada por estudiante con estado, duracion, interacciones, dependencia IA, riesgos
- Riesgos mas frecuentes en la cohorte
- Distribucion de estados cognitivos

**Auto-actualizacion**: La pagina incluye un checkbox "Auto-actualizar" que refresca los datos cada 30 segundos cuando esta habilitado.

### 8.4 ActivityManagementPage - Gestion de Actividades

**Ubicacion**: [pages/ActivityManagementPage.tsx](src/pages/ActivityManagementPage.tsx)
**Historias de Usuario**: HU-DOC-006 (Administracion de Actividades), HU-DOC-007 (Configuracion de Ejercicios)

Permite a los docentes crear, editar y administrar actividades de aprendizaje. Las actividades pasan por un ciclo de vida de estados: `draft` → `active` → `archived`.

**Operaciones CRUD completas:**
- **Crear**: Modal con campos para ID, titulo, descripcion, instrucciones, materia, dificultad, duracion estimada y etiquetas
- **Editar**: Mismos campos (excepto ID que es inmutable)
- **Clonar**: Duplica una actividad existente con nuevo ID
- **Publicar**: Cambia estado de `draft` a `active`
- **Archivar**: Cambia estado de `active` a `archived`
- **Eliminar**: Elimina permanentemente (con confirmacion)

**Configuracion de Politicas de IA**: Cada actividad puede configurar restricciones pedagogicas:
```tsx
const defaultPolicies: PolicyConfig = {
  max_help_level: HelpLevel.MEDIO,         // MINIMO, BAJO, MEDIO, ALTO
  block_complete_solutions: true,          // Bloquear solicitudes de codigo completo
  require_justification: true,             // Exigir que estudiante explique decisiones
  allow_code_snippets: true,               // Permitir fragmentos de codigo en respuestas
  risk_thresholds: {
    cognitive_delegation: 0.7,             // Umbral de riesgo de delegacion cognitiva
    ai_dependency: 0.6                     // Umbral de dependencia de IA
  },
};
```

Estas politicas son enviadas al backend y aplicadas por el agente de gobernanza GOV-IA durante las interacciones de los estudiantes.

### 8.5 ReportsPage - Generacion de Reportes

**Ubicacion**: [pages/ReportsPage.tsx](src/pages/ReportsPage.tsx)
**Historias de Usuario**: HU-DOC-003 (Reportes de Cohorte), HU-DOC-004 (Reportes Individuales), HU-DOC-009 (Comparativa entre Cohortes)

Los docentes pueden generar tres tipos de reportes:

**Reporte de Cohorte**: Analiza el desempeño agregado de un grupo de estudiantes en un curso durante un periodo especifico. Parametros:
- ID del curso
- Lista de IDs de estudiantes (opcional)
- Fecha de inicio y fin del periodo
- Formato de exportacion (JSON, PDF, XLSX)

**Dashboard de Riesgos**: Genera un reporte con la distribucion de riesgos detectados, alertas pendientes, y metricas de integridad academica.

**Analiticas de Aprendizaje**: Muestra metricas generales como:
- Total de estudiantes y sesiones
- Duracion promedio de sesiones
- Distribucion de uso por agente de IA
- Tendencias temporales

**Historial de Exportaciones**: Lista las exportaciones previas realizadas por el docente con enlaces para descargar.

### 8.6 InstitutionalRisksPage - Gestion de Riesgos

**Ubicacion**: [pages/InstitutionalRisksPage.tsx](src/pages/InstitutionalRisksPage.tsx)
**Historias de Usuario**: HU-DOC-005 (Gestion de Alertas Institucionales), HU-DOC-010 (Analisis de Efectividad Pedagogica)

Pagina dedicada a la gestion de riesgos a nivel institucional, con tres vistas:

**Dashboard de Riesgos**: Panel con metricas agregadas:
- Alertas pendientes por severidad
- Alertas resueltas esta semana
- Tendencia de riesgos en el tiempo
- Tipos de riesgo mas frecuentes

**Lista de Alertas**: Todas las alertas con filtros avanzados:
- Filtro por severidad: critical, high, medium, low
- Filtro por estado: pending, acknowledged, resolved
- Acciones: Reconocer, Resolver, Ver detalles

**Planes de Remediacion**: Permite crear planes de accion para estudiantes en riesgo:
```tsx
const remediationForm = {
  student_id: '',              // ID del estudiante
  title: '',                   // Titulo del plan
  description: '',             // Descripcion detallada
  plan_type: 'standard',       // Tipo de plan
  start_date: '',              // Fecha de inicio
  target_end_date: '',         // Fecha objetivo de finalizacion
};
```

### 8.7 Servicios del Docente

Los servicios que soportan las funcionalidades del docente estan en `services/api/`:

| Servicio | Responsabilidad |
|----------|-----------------|
| `reportsService` | Generacion de reportes de cohorte, riesgos y analiticas |
| `institutionalRisksService` | Dashboard de riesgos, alertas, planes de remediacion |
| `activitiesService` | CRUD de actividades, publicar, archivar, clonar |

### 8.8 Endpoints del Backend Utilizados

| Endpoint | Metodo | Proposito |
|----------|--------|-----------|
| `/teacher/alerts` | GET | Lista alertas de estudiantes |
| `/teacher/alerts/{id}/acknowledge` | POST | Reconocer una alerta |
| `/teacher/students/compare` | GET | Comparar estudiantes en actividad |
| `/activities` | GET/POST | Listar/Crear actividades |
| `/activities/{id}` | PUT/DELETE | Actualizar/Eliminar actividad |
| `/activities/{id}/publish` | POST | Publicar actividad (draft → active) |
| `/activities/{id}/archive` | POST | Archivar actividad |
| `/reports/cohort` | POST | Generar reporte de cohorte |
| `/reports/analytics` | GET | Analiticas de aprendizaje |
| `/admin/risks/dashboard` | GET | Dashboard de riesgos institucionales |
| `/admin/risks/alerts` | GET | Lista de alertas de riesgo |
| `/admin/risks/scan` | POST | Ejecutar escaneo de riesgos |
| `/admin/risks/remediation` | POST | Crear plan de remediacion |
| `/teacher/students/{id}/traceability` | GET | Trazabilidad N4 de estudiante |
| `/teacher/students/{id}/cognitive-path` | GET | Camino cognitivo de estudiante |
| `/teacher/traceability/summary` | GET | Resumen global de trazabilidad |

### 8.9 Trazabilidad N4 para Docentes (Cortez63)

Una de las capacidades mas distintivas del sistema es la trazabilidad cognitiva de nivel N4, que captura y analiza cada paso del proceso de aprendizaje de los estudiantes. Hasta Cortez62, esta informacion estaba disponible unicamente para los propios estudiantes y el sistema interno. Con Cortez63, los docentes obtienen acceso completo a estos datos para supervision pedagogica y deteccion temprana de patrones de riesgo.

#### Nuevo Servicio: teacherTraceabilityService

El servicio `teacherTraceabilityService` ubicado en [services/api/teacherTraceability.service.ts](src/services/api/teacherTraceability.service.ts) proporciona tres operaciones fundamentales para acceder a la trazabilidad de estudiantes:

```tsx
export const teacherTraceabilityService = {
  // Obtiene trazas N4 detalladas de un estudiante especifico
  async getStudentTraceability(
    studentId: string,
    params?: { activity_id?: string; limit?: number; offset?: number }
  ): Promise<StudentTraceabilityResponse>;

  // Reconstruye el camino cognitivo de un estudiante
  async getStudentCognitivePath(
    studentId: string,
    params?: { session_id?: string }
  ): Promise<StudentCognitivePathResponse>;

  // Obtiene metricas agregadas de todos los estudiantes
  async getTraceabilitySummary(
    params?: { activity_id?: string }
  ): Promise<TraceabilitySummaryResponse>;
};
```

El servicio define tipos TypeScript completos para representar la informacion de trazabilidad:

- **TraceLevel**: Los cuatro niveles de procesamiento (`'N1' | 'N2' | 'N3' | 'N4'`)
- **CognitiveState**: Los ocho estados cognitivos posibles (`INICIO`, `EXPLORACION`, `IMPLEMENTACION`, `DEPURACION`, `CAMBIO_ESTRATEGIA`, `VALIDACION`, `ESTANCAMIENTO`, `REFLEXION`)
- **TraceData**: Datos de una traza individual incluyendo sesion, actividad, nivel, tipo de interaccion, estado cognitivo, intencionalidad, justificacion de decisiones, tipo de estrategia e involucramiento de IA
- **TraceabilitySummary**: Resumen con distribuciones de estados cognitivos, niveles de traza, tipos de interaccion, y promedio de involucramiento de IA
- **AIDependencyDistribution**: Clasificacion de estudiantes por nivel de dependencia de IA (`high > 70%`, `medium 40-70%`, `low < 40%`)
- **TraceabilityAlert**: Alertas automaticas por alta dependencia de IA o estancamiento prolongado

#### Componente: StudentTraceabilityViewer

El componente [StudentTraceabilityViewer](src/components/teacher/StudentTraceabilityViewer.tsx) permite a los docentes examinar en profundidad la trazabilidad de un estudiante individual. Se organiza en tres pestañas:

**Pestaña Resumen (Overview)**: Muestra una vision consolidada del estudiante con cuatro metricas clave:
- Total de trazas N4 generadas
- Promedio de involucramiento de IA (porcentaje)
- Numero de estados cognitivos unicos alcanzados
- Distribucion grafica de estados cognitivos (grafico de barras horizontal)
- Distribucion de niveles de traza (N1-N4) como porcentajes
- Distribucion de tipos de interaccion

**Pestaña Trazas**: Lista paginada de todas las trazas del estudiante con detalles expandibles:
- Nivel de traza (N1-N4) con codigo de color
- Estado cognitivo actual
- Tipo de interaccion
- Marca temporal
- Contenido de la traza
- Intencionalidad cognitiva
- Justificacion de decisiones (cuando esta disponible)

**Pestaña Camino Cognitivo**: Visualiza la secuencia temporal de estados cognitivos:
- Timeline vertical de transiciones entre estados
- Tiempo acumulado en cada estado
- Insights automaticos sobre patrones de comportamiento
- Estados unicos alcanzados durante la sesion

#### Integracion en StudentMonitoringPage

La pagina de monitoreo de estudiantes [StudentMonitoringPage](src/pages/StudentMonitoringPage.tsx) incorpora una nueva pestaña "Trazabilidad N4" que proporciona:

**Panel de estadisticas globales:**
- Total de estudiantes monitoreados
- Total de trazas N4 capturadas
- Porcentaje de estudiantes con alta dependencia de IA

**Distribucion de estados cognitivos**: Grafico de barras mostrando cuantos estudiantes se encuentran en cada estado cognitivo, permitiendo identificar patrones globales como exceso de estudiantes en estado ESTANCAMIENTO.

**Sistema de alertas**: Las alertas automaticas se muestran con severidad codificada por color:
- Alertas criticas (rojo) para patrones que requieren intervencion inmediata
- Alertas de advertencia (amarillo) para patrones que merecen atencion

**Clasificacion por dependencia de IA**: Los estudiantes se agrupan en tres categorias:
- Alta dependencia (>70%): Estudiantes que delegan excesivamente en la IA
- Dependencia media (40-70%): Uso equilibrado de asistencia
- Baja dependencia (<40%): Trabajo predominantemente autonomo

Cada estudiante en la lista puede expandirse para acceder al `StudentTraceabilityViewer` completo sin navegar a otra pagina.

#### Integracion en TeacherDashboardPage

El panel principal del docente [TeacherDashboardPage](src/pages/TeacherDashboardPage.tsx) se enriquece con metricas de trazabilidad:

**Nueva tarjeta de estadisticas**: "Trazas N4" muestra el total de trazas capturadas con tendencia de crecimiento e icono distintivo.

**Nueva accion rapida**: "Trazabilidad N4" permite navegar directamente a la pestaña de trazabilidad en la pagina de monitoreo con un click.

**Seccion de Trazabilidad Cognitiva N4**: Panel dedicado al final del dashboard que incluye:
- Grafico de distribucion de estados cognitivos globales usando barras horizontales con colores diferenciados para cada estado
- Grafico de distribucion de dependencia de IA mostrando el porcentaje de estudiantes en cada categoria (alta, media, baja)
- Indicadores numericos con el total de estudiantes en cada nivel de dependencia

Esta integracion permite a los docentes obtener una vista rapida del estado cognitivo general de su cohorte sin necesidad de navegar a paginas de detalle, facilitando la deteccion temprana de problemas pedagogicos a nivel grupal.

#### Resumen de la Implementacion

**Backend** (3 nuevos endpoints en [teacher_tools.py](../backend/api/routers/teacher_tools.py)):

| Endpoint | Proposito | Capacidades |
|----------|-----------|-------------|
| `GET /teacher/students/{student_id}/traceability` | Trazabilidad completa de un estudiante | Muestra todas las trazas N4 con filtros por actividad. Incluye distribucion de estados cognitivos, niveles de traza, tipos de interaccion. Calcula promedio de dependencia de IA. Soporta paginacion. |
| `GET /teacher/students/{student_id}/cognitive-path` | Camino cognitivo del estudiante | Visualiza la evolucion cognitiva a traves de transiciones de estado. Calcula tiempo en cada estado. Genera insights automaticos (alertas de estancamiento, patrones). |
| `GET /teacher/traceability/summary` | Resumen global de trazabilidad | Distribucion de estados cognitivos de todos los estudiantes. Clasificacion por dependencia de IA (alta/media/baja). Alertas de trazabilidad (alta dependencia, estancamiento frecuente). |

**Frontend** (nuevos archivos y modificaciones):

| Archivo | Tipo | Descripcion |
|---------|------|-------------|
| [teacherTraceability.service.ts](src/services/api/teacherTraceability.service.ts) | Nuevo | Servicio con tipos TypeScript y metodos para los 3 endpoints |
| [StudentTraceabilityViewer.tsx](src/components/teacher/StudentTraceabilityViewer.tsx) | Nuevo | Componente con 3 tabs (Resumen, Trazas, Camino Cognitivo) |
| [StudentMonitoringPage.tsx](src/pages/StudentMonitoringPage.tsx) | Modificado | Nueva pestaña "Trazabilidad N4" con estadisticas y alertas |
| [TeacherDashboardPage.tsx](src/pages/TeacherDashboardPage.tsx) | Modificado | Nueva tarjeta de stats, accion rapida, seccion de graficos |
| [services/api/index.ts](src/services/api/index.ts) | Modificado | Export del nuevo servicio y tipos |

---

## 9. Modulos de Funcionalidades (Features)

Cada modulo de `features/` encapsula una funcionalidad completa con sus propios componentes, hooks y configuracion.

### Modulo Training (Entrenador Digital)

El Entrenador Digital guia a los estudiantes a traves de ejercicios estructurados con evaluacion automatica y feedback pedagogico.

**Componentes principales:**
- `ExercisePanel`: Muestra el enunciado, ejemplos y casos de prueba
- `CodeEditorPanel`: Editor Monaco con syntax highlighting
- `HintDisplay`: Pistas estaticas y correcciones de IA
- `HintV2Display`: Pistas contextuales con niveles de ayuda (Cortez55)
- `CognitiveStateDisplay`: Estado cognitivo inferido (Cortez55)
- `RiskIndicator`: Alertas de riesgo activas (Cortez55)
- `ReflexionModal`: Captura de reflexion post-ejercicio (Cortez55)
- `ExerciseResultBanner`: Resultado con puntuacion y siguiente ejercicio
- `FinalResults`: Resumen de sesion completada

**Hooks:**
- `useTrainingSession`: Gestion completa del ciclo de vida del entrenamiento
- `useTimer`: Temporizador para modo examen

El hook `useTrainingSession` (actualizado en Cortez55/56) soporta ambas versiones de API:

```tsx
export function useTrainingSession(params: TrainingSessionParams): UseTrainingSessionReturn {
  const { language, unit_number, exercise_id, useV2 = false } = params;

  // Estado V1
  const [currentHint, setCurrentHint] = useState<PistaResponse | null>(null);

  // Estado V2 (Cortez55)
  const [currentHintV2, setCurrentHintV2] = useState<PistaV2Response | null>(null);
  const [cognitiveState, setCognitiveState] = useState<CognitiveStateEnum | null>(null);
  const [activeRisks, setActiveRisks] = useState<RiskFlag[]>([]);

  // Correccion IA (Cortez56)
  const [correccionIA, setCorreccionIA] = useState<CorreccionIAResponse | null>(null);
```

### Modulo Tutor (Chat con T-IA-Cog)

La interfaz de chat permite conversaciones naturales con el tutor cognitivo, adaptando su estilo pedagogico segun el contexto.

**Componentes:**
- `TutorHeader`: Informacion de sesion y modo activo
- `ChatMessageBubble`: Mensajes con soporte Markdown
- `ChatInput`: Campo de entrada con historial
- `SuggestedQuestions`: Preguntas sugeridas contextuales
- `TypingIndicator`: Indicador de respuesta en progreso

**Hooks:**
- `useTutorSession`: Gestion de la sesion de tutoria
- `useRiskAnalysis`: Monitoreo de riesgos en tiempo real
- `useTraceability`: Consulta de trazabilidad cognitiva

### Modulo Simulators (S-IA-X)

Los simuladores profesionales ofrecen escenarios inmersivos que replican situaciones reales del desarrollo de software.

**Configuracion de 11 simuladores:**

```tsx
const SIMULATOR_CONFIG = {
  product_owner: { icon: '(clipboard)', color: '#10b981', name: 'Product Owner' },
  scrum_master: { icon: '(target)', color: '#f59e0b', name: 'Scrum Master' },
  tech_interviewer: { icon: '(briefcase)', color: '#3b82f6', name: 'Entrevistador Tecnico' },
  incident_responder: { icon: '(alert)', color: '#ef4444', name: 'Incident Response' },
  devsecops: { icon: '(lock)', color: '#8b5cf6', name: 'DevSecOps' },
  client: { icon: '(handshake)', color: '#ec4899', name: 'Cliente' },
  code_reviewer: { icon: '(eye)', color: '#14b8a6', name: 'Code Reviewer' },
  architect: { icon: '(building)', color: '#6366f1', name: 'Arquitecto' },
  qa_engineer: { icon: '(flask)', color: '#84cc16', name: 'QA Engineer' },
  mentor: { icon: '(teacher)', color: '#f97316', name: 'Mentor Senior' },
  stakeholder: { icon: '(chart)', color: '#06b6d4', name: 'Stakeholder' },
};
```

### Modulo Risks (AR-IA 5D)

El analizador de riesgos evalua cinco dimensiones de riesgo en el uso de IA educativa:

1. **Cognitiva**: Perdida de habilidades de pensamiento critico
2. **Etica**: Plagio, falta de atribucion, sesgos algoritmicos
3. **Epistemica**: Erosion de fundamentos teoricos
4. **Tecnica**: Dependencia de herramientas, falta de debugging manual
5. **Gobernanza**: Ausencia de politicas y auditoria

**Componentes:**
- `RiskAnalyzer`: Panel principal de analisis
- `DimensionCard`: Visualizacion de cada dimension con indicadores

### Modulo Traceability (TC-N4)

La visualizacion de trazabilidad muestra el recorrido de los datos a traves de los cuatro niveles de procesamiento:

| Nivel | Nombre | Descripcion |
|-------|--------|-------------|
| N1 | Raw Data | Datos crudos del usuario (input original) |
| N2 | Preprocessed | Validacion, limpieza, tokenizacion |
| N3 | LLM Processing | Inferencia del modelo de lenguaje |
| N4 | Postprocessed | Formateo, enriquecimiento, output final |

**Componentes:**
- `TraceabilityViewer`: Panel principal con seleccion de sesiones
- `TraceNodeCard`: Visualizacion expandible de cada nodo
- `Timeline`: Secuencia temporal de eventos

---

## 9. Sistema de Tipos TypeScript

La refactorizacion de tipos (Cortez43) dividio el archivo monolitico `api.types.ts` (893 lineas) en 11 modulos especializados.

### Enumeraciones Centralizadas

El archivo `enums.ts` contiene todas las enumeraciones del sistema:

```tsx
export enum SessionMode {
  TUTOR = 'TUTOR',
  EVALUATOR = 'EVALUATOR',
  SIMULATOR = 'SIMULATOR',
  AUTONOMOUS = 'AUTONOMOUS',
  TRAINING = 'TRAINING',
}

export enum CognitiveState {
  INICIO = 'INICIO',
  EXPLORACION = 'EXPLORACION',
  IMPLEMENTACION = 'IMPLEMENTACION',
  DEPURACION = 'DEPURACION',
  CAMBIO_ESTRATEGIA = 'CAMBIO_ESTRATEGIA',
  VALIDACION = 'VALIDACION',
  ESTANCAMIENTO = 'ESTANCAMIENTO',
  REFLEXION = 'REFLEXION',
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
  INFO = 'info',
}
```

### Tipos por Dominio

Cada dominio tiene su archivo de tipos dedicado:

- **session.types.ts**: Interfaces para crear, actualizar y responder sesiones
- **interaction.types.ts**: Mensajes de chat y respuestas de interaccion
- **trace.types.ts**: Trazabilidad cognitiva, fases y transiciones
- **risk.types.ts**: Analisis de riesgos y puntuaciones por dimension
- **evaluation.types.ts**: Evaluaciones de proceso y errores conceptuales
- **activity.types.ts**: Configuracion de actividades y politicas
- **simulator.types.ts**: Solicitudes y respuestas de simuladores
- **git.types.ts**: Metricas de commits, contribuidores y tendencias
- **api.types.ts**: Wrappers genericos de respuesta API

### Importacion Centralizada

El archivo `index.ts` re-exporta todos los tipos para simplificar las importaciones:

```tsx
import {
  SessionMode,
  CognitiveState,
  RiskLevel,
  type SessionResponse,
  type InteractionCreate,
  type CognitiveTrace,
} from '@/types/domain';
```

---

## 10. Componentes Compartidos

El directorio `shared/components/` contiene componentes reutilizables de proposito general.

### Toast (Notificaciones)

El sistema de notificaciones implementa un contexto con hook personalizado:

```tsx
const { showToast } = useToast();

// Tipos de toast: 'success', 'error', 'warning', 'info'
showToast('Operacion completada', 'success');
showToast('Error de conexion', 'error', 10000); // duracion personalizada
```

Las notificaciones aparecen en la esquina superior derecha con animaciones de entrada/salida y auto-dismissal configurable.

### Modal (Dialogos)

El componente Modal proporciona una base accesible para dialogos:

```tsx
<Modal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  title="Confirmar accion"
>
  <p>Esta seguro de continuar?</p>
  <div className="flex gap-2 mt-4">
    <Button onClick={handleConfirm}>Confirmar</Button>
    <Button variant="outline" onClick={() => setShowModal(false)}>
      Cancelar
    </Button>
  </div>
</Modal>
```

### LoadingSpinner

Indicador de carga consistente en todo el sistema:

```tsx
<LoadingSpinner size="sm" />  // 16px
<LoadingSpinner size="md" />  // 24px (default)
<LoadingSpinner size="lg" />  // 32px
```

### Configuracion Compartida

Los archivos en `shared/config/` centralizan valores constantes:

**labels.config.ts**: Etiquetas de UI para enumeraciones
```tsx
export const RiskTypeLabels: Record<RiskType, string> = {
  [RiskType.COPY_PASTE]: 'Copia y Pega',
  [RiskType.OVER_RELIANCE]: 'Sobre-dependencia',
  // ...
};
```

**colors.config.ts**: Esquemas de colores y gradientes
**constants.config.ts**: Constantes de aplicacion (timeouts, limites)

---

## 11. Hooks Personalizados

Los hooks personalizados encapsulan logica reutilizable y patrones comunes.

### useTrainingSession

El hook mas complejo del sistema, gestionando todo el ciclo de vida del entrenamiento digital con soporte para ambas versiones de API:

```tsx
const {
  session,
  currentExercise,
  code,
  loading,
  submitting,
  error,
  completedExercises,
  finalResult,

  // V1 Hints
  currentHint,
  requestHint,

  // V2 Features (Cortez55)
  currentHintV2,
  cognitiveState,
  activeRisks,
  requestHintV2,
  submitReflexion,

  // Cortez56 Features
  correccionIA,
  requestCorreccionIA,
  refreshSessionState,

  // Actions
  setCode,
  initSession,
  submitExercise,
  resetSession,
} = useTrainingSession({
  language: 'python',
  unit_number: 1,
  useV2: true,
});
```

### useFetchSessions

Hook para recuperar sesiones con manejo de estado:

```tsx
const { sessions, loading, error, refetch } = useFetchSessions({
  limit: 10,
  offset: 0,
  mode: SessionMode.TUTOR,
});
```

### useTimer

Temporizador para modo examen:

```tsx
const { timeRemaining, isRunning, start, pause, reset } = useTimer({
  initialSeconds: 3600, // 1 hora
  onComplete: () => handleTimeUp(),
});
```

### Patron de Cleanup en useEffect

Todos los hooks que realizan operaciones asincronas implementan cleanup adecuado:

```tsx
useEffect(() => {
  const abortController = new AbortController();

  const fetchData = async () => {
    try {
      const data = await service.getData({ signal: abortController.signal });
      if (!abortController.signal.aborted) {
        setData(data);
      }
    } catch (error) {
      if (!abortController.signal.aborted) {
        setError(error);
      }
    }
  };

  fetchData();
  return () => abortController.abort();
}, [dependency]);
```

---

## 12. Patrones de React 19

El proyecto aprovecha las nuevas caracteristicas de React 19 para codigo mas limpio y mejor rendimiento.

### Hook use() para Contextos

React 19 introduce el hook `use()` que puede leer contextos de forma mas elegante:

```tsx
// Antes (React 18)
const context = useContext(AuthContext);

// Despues (React 19)
const context = use(AuthContext);
```

Todos los contextos del proyecto utilizan este patron a traves de hooks personalizados que agregan validacion:

```tsx
export function useAuth(): AuthContextType {
  const context = use(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Function Components (No React.FC)

El proyecto abandono `React.FC` a favor de componentes de funcion tipados directamente (migracion completada en Cortez48):

```tsx
// Evitado
const MyComponent: React.FC<Props> = ({ prop }) => { ... };

// Preferido
function MyComponent({ prop }: Props) { ... }
// o
const MyComponent = ({ prop }: Props) => { ... };
```

Esta aproximacion ofrece mejor inferencia de tipos y evita la inyeccion implicita de `children`.

### Suspense y Lazy Loading

Los componentes pesados se cargan de forma diferida:

```tsx
const DashboardPage = lazy(() => import('./pages/DashboardPage'));

// En el router
<Suspense fallback={<PageLoadingFallback />}>
  <DashboardPage />
</Suspense>
```

---

## 13. Accesibilidad y Estandares Web

El proyecto implementa estandares de accesibilidad WCAG 2.1 nivel AA (mejoras aplicadas en Cortez60).

### Elementos Interactivos Accesibles

Los elementos div clickeables incluyen atributos de accesibilidad:

```tsx
<div
  role="button"
  tabIndex={0}
  aria-expanded={expanded}
  aria-label={`${node.level} - ${config.name}. Click para ${expanded ? 'colapsar' : 'expandir'} detalles`}
  onClick={() => setExpanded(!expanded)}
  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setExpanded(!expanded)}
>
```

### Navegacion por Teclado

El menu de usuario se cierra con la tecla Escape:

```tsx
const handleKeyDown = useCallback((event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    setUserMenuOpen(false);
  }
}, []);

useEffect(() => {
  if (userMenuOpen) {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }
}, [userMenuOpen, handleKeyDown]);
```

### Etiquetas ARIA

Los botones de iconos incluyen etiquetas descriptivas:

```tsx
<button
  aria-label="Notificaciones"
  className="..."
>
  <Bell className="w-5 h-5" aria-hidden="true" />
  <span className="..." aria-label="Hay notificaciones sin leer"></span>
</button>
```

### Keys Unicas en Listas

Todas las listas dinamicas utilizan keys unicos en lugar de indices (correccion Cortez60):

```tsx
// Evitado
{items.map((item, index) => <Item key={index} />)}

// Implementado
{items.map((item) => <Item key={item.id} />)}
// o cuando no hay ID
{items.map((item) => <Item key={`${node.id}-transform-${item.name}`} />)}
```

---

## 14. Rendimiento y Optimizacion

### Vite Build Optimization

El archivo `vite.config.ts` configura optimizaciones de produccion:

```tsx
build: {
  minify: 'terser',
  terserOptions: {
    compress: {
      drop_console: true,
      drop_debugger: true,
    },
  },
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom', 'react-router-dom'],
        ui: ['lucide-react', '@radix-ui/react-dialog'],
        charts: ['recharts'],
        editor: ['@monaco-editor/react'],
      },
    },
  },
},
```

### Memorizacion Estrategica

Los componentes que realizan calculos costosos utilizan `useMemo`:

```tsx
const sortedRisks = useMemo(() => {
  return [...risks].sort((a, b) => severityOrder[b.severity] - severityOrder[a.severity]);
}, [risks]);

const progressPercentage = useMemo(() => {
  return exercises.length > 0
    ? Math.round((completed / exercises.length) * 100)
    : 0;
}, [completed, exercises.length]);
```

### useCallback para Callbacks Estables

Los callbacks pasados a componentes hijos se memorizan:

```tsx
const handleSubmit = useCallback(async () => {
  setSubmitting(true);
  try {
    await submitExercise();
  } finally {
    setSubmitting(false);
  }
}, [submitExercise]);
```

### Carga Diferida de Paginas

El lazy loading reduce el bundle inicial de ~500KB a ~200KB, mejorando significativamente el Time to Interactive.

---

## 15. Testing y Calidad

### Stack de Testing

| Herramienta | Proposito |
|-------------|-----------|
| Vitest | Unit testing con API compatible con Jest |
| Testing Library | Testing de componentes React |
| Playwright | E2E testing cross-browser |

### Scripts de Testing

```bash
npm test              # Ejecutar tests en modo watch
npm run test:ui       # UI interactiva de Vitest
npm run test:coverage # Reporte de cobertura
npm run e2e           # Tests end-to-end
npm run e2e:ui        # Playwright UI mode
```

### ESLint Configuration

El proyecto usa ESLint 9 con flat config:

```bash
npm run lint          # Verificar con --max-warnings 0
```

La configuracion incluye:
- `eslint-plugin-react-hooks` para verificar reglas de hooks
- `eslint-plugin-react-refresh` para compatibilidad con HMR
- Reglas TypeScript estrictas via `typescript-eslint`

### Type Checking

```bash
npm run type-check    # tsc --noEmit
```

El proyecto requiere cero errores de tipo para pasar CI.

---

## 16. Configuracion y Desarrollo

### Variables de Entorno

Crear `.env` basado en `.env.example`:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_OLLAMA_URL=http://localhost:11434
VITE_ENABLE_DEV_TOOLS=true
```

### Comandos de Desarrollo

```bash
# Instalacion
npm install

# Desarrollo con HMR
npm run dev

# Build de produccion
npm run build

# Preview del build
npm run preview

# Verificacion completa
npm run lint && npm run type-check && npm test
```

### Estructura del Build

El build de produccion genera:

```
dist/
|-- index.html
+-- assets/
    |-- index-[hash].js     # Bundle principal (~200KB gzip)
    |-- vendor-[hash].js    # React, Router (~50KB gzip)
    |-- ui-[hash].js        # Lucide, Radix (~30KB gzip)
    |-- charts-[hash].js    # Recharts (~40KB gzip)
    +-- editor-[hash].js    # Monaco (lazy loaded)
```

### Integracion con Backend

El frontend espera el backend en `http://localhost:8000`. Para desarrollo:

```bash
# Terminal 1: Backend
cd backend
python -m backend

# Terminal 2: Frontend
cd frontEnd
npm run dev
```

### Docker Development

```bash
# Desde raiz del proyecto
docker-compose up -d

# Solo frontend
docker-compose up -d frontend
```

---

## Historial de Auditorias

| Auditoria | Fecha | Cambios Principales |
|-----------|-------|---------------------|
| Cortez63 | Enero 2026 | Trazabilidad N4 para Docentes: 3 endpoints backend, teacherTraceabilityService, StudentTraceabilityViewer, integracion en Dashboard y Monitoring |
| Cortez60 | Enero 2026 | Accesibilidad (role/aria), keys unicos, limpieza ESLint |
| Cortez55 | Enero 2026 | V2 Training con N4, 4 nuevos componentes |
| Cortez48 | Diciembre 2025 | 28 React.FC -> function, ErrorBoundaryWithNavigation |
| Cortez43 | Diciembre 2025 | Modularizacion de tipos y features |
| Cortez40 | Diciembre 2025 | Lazy loading, useMemo/useCallback |
| Cortez31 | Noviembre 2025 | Migracion Context -> Zustand |
| Cortez28 | Noviembre 2025 | Migracion React 18 -> React 19 |

---

## Contacto y Contribucion

Este proyecto forma parte de una tesis doctoral sobre evaluacion basada en procesos cognitivos en la enseñanza de programacion con IA generativa.

Para reportar issues o sugerir mejoras, consultar el archivo `CONTRIBUTING.md` en la raiz del repositorio.
