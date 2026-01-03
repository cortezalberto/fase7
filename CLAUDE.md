# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Location

The actual project is located in `activia1-main/` subdirectory. **All commands should be run from there.**

```bash
cd activia1-main
```

## Project Overview

AI-Native MVP for teaching-learning programming with generative AI. Doctoral thesis project implementing **process-based evaluation** (not product-based) with N4-level cognitive traceability.

**Tech Stack**: Python 3.11+/FastAPI backend, React 19/TypeScript/Vite frontend, PostgreSQL, Redis, Ollama/Phi-3 for LLM.

**Key Concept**: The system evaluates HOW students solve problems (cognitive process), not just the final code output. This is achieved through 6 AI agents and N4-level cognitive traceability.

**Last Updated**: Cortez71 Frontend Audit (January 2026):
- **Objective**: Complete frontend codebase audit with 27 issues identified and ALL FIXED
- **All Issues Fixed** (27/27 = 100%):
  - ✅ CRIT-001: Demo credentials now DEV-only (`import.meta.env.DEV` conditional)
  - ✅ CRIT-002: Removed credential logging from LoginPage, useTrainingSession, StudentMonitoringPage
  - ✅ HIGH-001 to HIGH-005: Fixed `key={index}` anti-patterns, AbortController, stable keys
  - ✅ MED-001 to MED-008: Type aliases deprecated, useMemo dependencies, feature flags centralized
  - ✅ LOW-001 to LOW-012: Dynamic styles utility, date formatting, ESLint disable justifications
- **New Files Created**:
  - `shared/utils/errorUtils.ts` - Centralized error handling
  - `shared/config/featureFlags.config.ts` - Feature flag system with env var overrides
  - `shared/utils/dateUtils.ts` - Standardized date formatting (es-ES locale)
  - `shared/styles/dynamicStyles.ts` - Dynamic CSS utilities
- **Frontend Health Score**: 7.5/10 → 9.2/10
- **Full Report**: `docs/audits/CORTEZ71_FRONTEND_AUDIT.md`

**Previous - Cortez70**: Backend Concurrency & Security Audit - 14 CRITICAL fixed: thread locks, DB locking, sandbox exec, N+1→batch, Health Score 8.2→8.8

**Previous - Cortez69**: Backend Inconsistency Audit - 238 issues (14 CRIT), auth + prompt injection fixes, score 6.8→8.2

**Previous - Cortez68**: Backend Audit - 113 issues, 8 CRITICAL + 22 HIGH fixed, score 7.5→9.0

**Previous - Cortez66**: Backend Architecture Audit - 5 phases: coordinator extraction, tutor consolidation, schema consolidation, repository standards

**Previous - Cortez65.2**: Academic Context without LTI (January 2026):
- **Purpose**: Enable student course/commission display during testing phase without Moodle integration
- **Backend Changes**:
  - `UserDB` model: Added `course_name` (VARCHAR 255) and `commission` (VARCHAR 100) fields
  - `UserRepository`: 3 new methods: `update_academic_context()`, `get_by_commission()`, `get_students_by_course()`
  - Auth schemas: `UserResponse` and `UserResponseSchema` include new fields
  - Auth router: `_user_to_response()` maps new fields to login response
  - Migration: `add_user_academic_context.py` adds columns + index
- **Frontend Changes**:
  - `User` type: Added `course_name?` and `commission?` optional fields
  - `TutorHeader`: Displays academic context badges when available
  - `TutorPage`: Passes user context to header component
- **Run migration**: `python -m backend.database.migrations.add_user_academic_context`

**Previous - Cortez65.1**: LTI 1.3 + Activity-Moodle Linking (NOT ENABLED) (January 2026):
- **HU-SYS-010**: Moodle integration via LTI 1.3 protocol
- **Backend**: `backend/api/routers/lti.py` (~750 lines) - Complete router with:
  - `POST /login` - OIDC login initiation (Step 1)
  - `POST /launch` - LTI launch callback with JWT verification + **automatic activity matching** (Step 2)
  - `GET /jwks` - Public key endpoint (for AGS)
  - `POST /deployments` - Create LTI deployment (admin)
  - `GET /deployments` - List deployments (admin)
  - `DELETE /deployments/{id}` - Deactivate deployment (admin)
  - `POST /activities/link` - **NEW** Link AI-Native activity to Moodle course/resource (Cortez65.1)
  - `DELETE /activities/{id}/link` - **NEW** Unlink activity from Moodle (Cortez65.1)
  - `GET /activities/linked` - **NEW** List all Moodle-linked activities (Cortez65.1)
- **ActivityDB Moodle Fields** (Cortez65.1): 4 new fields for automatic activity matching:
  - `moodle_course_id` - context_id from Moodle (indexed)
  - `moodle_course_name` - context_title (course name for display)
  - `moodle_course_label` - context_label (commission code like "PROG1-A")
  - `moodle_resource_name` - resource_link_title (activity name in Moodle, indexed)
  - Composite index: `idx_activity_moodle_match` for efficient lookups
- **ActivityRepository** (Cortez65.1): 5 new methods for Moodle integration:
  - `get_by_moodle_context()` - Find activity by course_id + resource_name
  - `get_by_moodle_resource_name()` - Fallback: find by resource_name only
  - `link_to_moodle()` - Link activity to Moodle course
  - `unlink_from_moodle()` - Remove Moodle link
  - `get_moodle_linked_activities()` - List linked activities (optionally by teacher)
- **Automatic Activity Matching**: LTI launch now automatically finds AI-Native activity:
  - Strategy 1: Match by `moodle_course_id` + `moodle_resource_name` (most specific)
  - Strategy 2: Fallback match by `moodle_resource_name` only
  - Returns `activity_id`, `activity_title`, `activity_matched` in launch response
- **Config**: `backend/api/config.py` - LTI configuration section:
  - `LTI_ENABLED=false` (master switch)
  - `LTI_FRONTEND_URL`, `LTI_STATE_EXPIRATION_MINUTES`, etc.
- **Frontend**: `lti.service.ts` + `LTIContainer.tsx`
  - LTI context detection from URL params (now includes `resourceLinkTitle`)
  - Embedded mode support for iframe
  - Session storage for LTI context
- **Documentation**: `docs/moodle.md` v3.3 (~2,000 lines) with:
  - Complete admin guide for Moodle configuration (17 subsections)
  - Step-by-step LTI tool registration
  - Credential exchange between Moodle and AI-Native
  - **Section 11.5**: Activity-Moodle linking (teacher workflow, API endpoints)
  - Activity creation and testing procedures
- **Migrations** (Cortez65.1):
  - `add_resource_link_title.py` - Add `resource_link_title` to `lti_sessions`
  - `add_moodle_fields_to_activities.py` - Add 4 Moodle fields + indexes to `activities`
- **Status**: 90% infrastructure done, router ready but NOT registered in main.py

**Previous - Cortez64**: CRPE Signal Expansion + New Response Types (January 2026):
- **cognitive_engine.py**: Expanded prompt classification from ~15 to ~137 signals
  - 10 detection categories: delegation, frustration, validation, confusion, examples, metacognition, questions, explanations, optimization, comparison
  - New flags: `is_frustrated`, `is_confused`, `requests_validation`, `requests_example`, `is_metacognitive`, `requests_optimization`, `requests_comparison`
- **ai_gateway.py**: 4 new response type handlers + 4 fallbacks
  - `_generate_empathetic_support()` - For frustrated students (empathy + direct hints)
  - `_generate_metacognitive_guidance()` - For "how do I think about this" questions
  - `_generate_example_based()` - Provides analogous examples, not direct solutions
  - `_generate_clarification_request()` - Updated to async with LLM
- **Response types**: 4 → 7 (added: empathetic_support, metacognitive_guidance, example_based)
- **Coverage**: Student prompt classification improved from ~35% to ~90%

**Previous - Cortez63**: N4 Traceability for Teachers + Frontend Improvements (January 2026):
- **Teacher N4 Traceability**: 3 new endpoints in `teacher_tools.py` for student cognitive monitoring
  - `GET /teacher/students/{id}/traceability` - Full N4 traces with cognitive state distribution
  - `GET /teacher/students/{id}/cognitive-path` - Cognitive evolution timeline with insights
  - `GET /teacher/traceability/summary` - Global traceability metrics and AI dependency classification
- **teacherTraceability.service.ts**: New frontend service with TypeScript types
- **StudentTraceabilityViewer.tsx**: 3-tab component (Overview, Traces, Cognitive Path)
- **StudentMonitoringPage**: New "Trazabilidad N4" tab with stats, alerts, dependency grouping
- **TeacherDashboardPage**: New stats card, quick action, cognitive charts section
- **TeacherLayout**: New layout component for `/teacher/*` routes with dedicated sidebar
- **ActivityManagementPage**: Maestro-Detalle (Master-Detail) pattern for activity creation
- **LoginPage**: Browser autocomplete prevention with hidden fields and unique names
- **Error handling**: Fixed API error message extraction from interceptor-transformed errors

**Previous - Cortez62**: Technology Stack Proposal (January 2026):
- **stack.md**: Complete technology stack recommendation (900+ lines)
  - Vector database: PostgreSQL + pgvector ($0, unified infrastructure)
  - Embeddings: Ollama + nomic-embed-text (384 dimensions, $0)
  - LLM strategy: Mistral Small API + phi3 local fallback (~$5-20/month)
  - Cost analysis: $10/month (thesis) → $65/month (30 students) → $575/month (200 students)
  - 5-phase implementation plan with Docker Compose updates

**Previous - Cortez61**: Multi-Agent Architecture Proposal - ImplementacionAgentes.md rewritten (1,115 lines), 6 agents specification

**Previous - Cortez60**: Frontend Senior Audit - All findings corrected, ESLint 48→0

**Previous - Cortez59+**: GitHub CI/CD Complete - 6 new workflows, 14-stage pipeline

**Previous - Cortez59**: GitHub CI/CD Enhancement - Documentation rewrite, gap analysis, 2 initial workflows

**Previous - Cortez58**: Backend Obsolete Code Cleanup - 964 lines removed, 4 error handlers added

**Previous - Cortez57**: Frontend Obsolete Code Cleanup - ExerciseDetailPage.tsx deleted (347 lines), User type consolidated

**Previous - Cortez56**: Backend V1 Legacy Endpoints - 3 new training endpoints, datetime fixes

**Previous - Cortez55**: Frontend Digital Trainer V2 Integration - 4 new components, V2 hooks, training.service.ts refactored

**Previous - Cortez54**: Backend Endpoint Audit - 12 defects fixed (missing methods, datetime, encoding)

**Previous - Cortez53**: HTTPException Migration Complete - 51 HTTPExceptions → custom exceptions, 14 new exception classes

**Previous - Cortez52**: Backend Architect Audit - 26 findings, N+1 queries fixed, TTL cleanup added

**Previous - Cortez51**: Backend Deep Audit - 33 findings, 5 critical fixed (silenced exceptions, HTTPException migration)

**Previous - Cortez50**: Digital Trainer Integration with T-IA-Cog and N4 traceability (10 files, ~2,500 lines)

**Previous - Cortez49**: Backend + Frontend READMEs with comprehensive prose explanations (700+ and 1,350+ lines)

**Previous - Cortez48**: Frontend Senior Audit - 57 issues found, all critical/high FIXED
- ✅ Demo credentials conditional to DEV mode (`LoginPage.tsx`)
- ✅ `ErrorBoundaryWithNavigation` wrapper uses React Router (`ErrorBoundary.tsx`)
- ✅ AbortController added to GitAnalytics useEffect (`GitAnalytics.tsx`)
- ✅ 28 React.FC patterns replaced with function components (18 files)
- Full report: `docs/audits/CORTEZ48_FRONTEND_AUDIT.md`

**Previous**: Cortez47 (Backend Deep Audit), Cortez46 (Backend Modularization), Cortez45 (GitHub), Cortez44 (DevOps), Cortez43 (Frontend) - All modularization audits.

## Quick Commands

```bash
# Navigate to project directory first
cd activia1-main

# Start everything with Docker
docker-compose up -d

# Run backend tests
pytest tests/ -v --cov=backend

# Run frontend dev server
cd frontEnd && npm run dev

# Check API health
curl http://localhost:8000/api/v1/health
```

## Common Development Commands

### Docker (Recommended)
```bash
docker-compose up -d                    # Start full stack
docker-compose logs -f api              # View API logs
docker-compose down                     # Stop services
docker-compose --profile debug up -d    # Includes pgAdmin + Redis Commander
docker-compose --profile monitoring up -d # Includes Prometheus + Grafana
```

### Backend (Local Development)
```bash
pip install -r requirements.txt
python -m backend                       # Runs uvicorn on :8000

# Run database migrations
python -m backend.database.migrations.add_n4_dimensions
python -m backend.database.migrations.add_cortez_audit_fixes
python -m backend.database.migrations.add_resource_link_title          # Cortez65.1: LTI sessions
python -m backend.database.migrations.add_moodle_fields_to_activities  # Cortez65.1: Activity-Moodle linking
python -m backend.database.migrations.add_user_academic_context        # Cortez65.2: User course/commission
```

### Backend Testing
```bash
pytest tests/ -v --cov=backend          # All tests (70% min coverage required)
pytest tests/ -v -m "unit"              # Unit tests only
pytest tests/ -v -m "integration"       # Integration tests
pytest tests/test_agents.py -v          # Single file
pytest tests/test_agents.py::test_tutor_mode -v  # Single test function
pytest -k "test_tutor" -v               # Pattern matching (runs all tests containing "test_tutor")
```

Test markers: `unit`, `integration`, `cognitive`, `agents`, `models`, `gateway`, `slow`, `asyncio`

### Frontend
```bash
cd frontEnd
npm install && npm run dev              # Dev server
npm run build                           # Production build
npm run lint                            # ESLint
npm run type-check                      # TypeScript check
npm test                                # Vitest tests
npm run e2e                             # Playwright E2E tests
```

### Make Commands (WSL/Git Bash on Windows)
```bash
make dev                    # Start full stack
make test                   # All tests with coverage
make lint                   # pylint + flake8
make format                 # black formatting
make health-check           # Verify all services
make db-shell               # Open PostgreSQL shell
make db-backup              # Create database backup
make redis-cli              # Open Redis CLI
make generate-secrets       # Generate JWT_SECRET_KEY and CACHE_SALT

# Production commands
make prod-up                # Start production stack
make prod-monitoring        # Production with Prometheus + Grafana
make prod-down              # Stop production stack

# CI/CD commands
make ci-test                # Run tests in CI mode
make ci-lint                # Linting for CI
make ci-security            # Security scanning
make ci-build               # Build Docker images
```

### Windows PowerShell (without Make)
```powershell
# Health check
Invoke-RestMethod http://localhost:8000/api/v1/health

# Docker commands work directly
docker-compose up -d
docker-compose logs -f api

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture

### Request Flow
```
Client -> FastAPI Router -> AIGateway (STATELESS) -> CRPE -> Governance Agent
    -> Target Agent -> LLM Provider -> Response Generator -> TC-N4 Traceability
    -> Risk Analyzer -> Repositories (PostgreSQL) -> Response
```

### 6 AI Agents (`backend/agents/`)
| Agent | File | Purpose |
|-------|------|---------|
| T-IA-Cog | `tutor.py` + `tutor_modes/` (Cortez46/50) | Cognitive Tutor - Strategy Pattern (5 modes: Socratic, Explicative, Guided, Metacognitive, TrainingHints) |
| E-IA-Proc | `evaluator.py` | Process Evaluator |
| S-IA-X | `simulators/` (Cortez42) | Professional Role Simulators - Strategy Pattern (11 roles) |
| AR-IA | `risk_analyst.py` | Risk Analyst (5 dimensions) |
| GOV-IA | `governance.py` | Governance & Delegation |
| TC-N4 | `traceability.py` | N4-level Traceability |

### Digital Trainer (Entrenador Digital)
| Component | Path | Purpose |
|-----------|------|---------|
| Training Router | `backend/api/routers/training/` | Structured practice with exercises |
| Integration Router (Cortez50) | `backend/api/routers/training/integration_endpoints.py` | V2 endpoints with agent integration |
| Code Evaluator | `backend/services/code_evaluator.py` | AI mentor "Alex" for code evaluation |
| Exercise Models | `backend/database/models/exercise.py` | Exercise, Hint, Test, Attempt models |
| TrainingGateway (Cortez50) | `backend/core/training_gateway.py` | Central orchestrator for agent integration |
| TrainingTraceCollector (Cortez50) | `backend/core/training_traceability.py` | N4 trace capture with cognitive inference |
| TrainingRiskMonitor (Cortez50) | `backend/core/training_risk_monitor.py` | Real-time risk detection |
| TrainingHintsStrategy (Cortez50) | `backend/agents/tutor_modes/training_hints.py` | T-IA-Cog contextual hints for exercises |

**Flow**: Student selects Language → Lesson → Exercise → Writes code → Gets automated tests + AI feedback

**Endpoints (V1 - Original + Cortez56)**:
- `GET /training/lenguajes` - Hierarchical structure: Language → Lessons → Exercises
- `POST /training/iniciar` - Start training session
- `POST /training/submit-ejercicio` - Submit code for evaluation (tests + AI) *(Cortez56)*
- `POST /training/corregir-ia` - AI-assisted code correction *(Cortez56)*
- `GET /training/sesion/{id}/estado` - Session state with N4 fields *(Cortez56)*
- `POST /training/pista` - Request static hint (with score penalty)

**Endpoints (V2 - Cortez50 Integration)**:
- `POST /training/pista/v2` - Contextual hints using T-IA-Cog (4 help levels)
- `POST /training/reflexion` - Post-exercise reflection capture (active traceability)
- `GET /training/sesion/{id}/proceso` - Process analysis with cognitive metrics
- `POST /training/submit/v2` - Extended submission with traceability

**Feature Flags** (in `.env`):
- `TRAINING_USE_TUTOR_HINTS=true` - Enable T-IA-Cog contextual hints
- `TRAINING_N4_TRACING=true` - Enable N4 cognitive traceability
- `TRAINING_RISK_MONITOR=true` - Enable real-time risk detection

### Teacher Management (`/teacher/*` routes)

**Layout**: `TeacherLayout.tsx` - Dedicated layout for teacher routes with:
- Purple/violet gradient branding (distinct from student blue theme)
- Sidebar with: Dashboard, Monitoreo, Actividades, Reportes, Riesgos
- User menu with logout
- `<Outlet />` for nested routes

| Page | File | Purpose |
|------|------|---------|
| TeacherDashboardPage | `pages/TeacherDashboardPage.tsx` | HU-DOC-001/002 - Dashboard with alerts, analytics |
| StudentMonitoringPage | `pages/StudentMonitoringPage.tsx` | HU-DOC-002/003/004 - Real-time monitoring, 30s auto-refresh |
| ActivityManagementPage | `pages/ActivityManagementPage.tsx` | HU-DOC-006/007 - CRUD + PolicyConfig + **Maestro-Detalle** |
| ReportsPage | `pages/ReportsPage.tsx` | HU-DOC-003/004/009 - Cohort reports, export (JSON/PDF/XLSX) |
| InstitutionalRisksPage | `pages/InstitutionalRisksPage.tsx` | HU-DOC-005/010 - Risk management, remediation plans |

**Maestro-Detalle Pattern** (ActivityManagementPage - Cortez63):
```typescript
// Activity header (Maestro) + Exercises list (Detalle)
interface ExerciseDetail {
  id: string;       // Unique ID for React keys
  numero: number;   // Auto-incremented exercise number
  enunciado: string; // Exercise statement text
}

// State management
const [exercises, setExercises] = useState<ExerciseDetail[]>([]);

// CRUD operations with auto-renumbering
const addExercise = () => {
  setExercises([...exercises, {
    id: `ex_${Date.now()}`,
    numero: exercises.length + 1,
    enunciado: '',
  }]);
};

const removeExercise = (id: string) => {
  const updated = exercises.filter(ex => ex.id !== id);
  setExercises(updated.map((ex, idx) => ({ ...ex, numero: idx + 1 })));
};
```

**Teacher Endpoints**:
- `GET /teacher/alerts`, `POST /teacher/alerts/{id}/acknowledge` - Alert management
- `GET /teacher/students/compare` - Student comparison by activity
- `GET /teacher/students/{id}/traceability` - N4 traces with cognitive state distribution (Cortez63)
- `GET /teacher/students/{id}/cognitive-path` - Cognitive evolution timeline (Cortez63)
- `GET /teacher/traceability/summary` - Global traceability metrics (Cortez63)
- `GET/POST /activities`, `PUT/DELETE /activities/{id}` - Activity CRUD
- `POST /activities/{id}/publish`, `POST /activities/{id}/archive` - Lifecycle
- `POST /reports/cohort`, `GET /reports/analytics` - Report generation
- `GET /admin/risks/dashboard`, `GET /admin/risks/alerts` - Institutional risks
- `POST /admin/risks/scan`, `POST /admin/risks/remediation` - Risk actions

### Key Files
| Component | Path |
|-----------|------|
| AI Gateway (orchestrator) | `backend/core/ai_gateway.py` |
| Gateway Protocols (Cortez42) | `backend/core/gateway/protocols.py` |
| Gateway Fallbacks (Cortez42) | `backend/core/gateway/fallback_responses.py` |
| Response Generators (Cortez66) | `backend/core/gateway/response_generators.py` (7 generators + 4 fallbacks) |
| Trace Coordinator (Cortez66) | `backend/core/gateway/trace_coordinator.py` (N4 traceability management) |
| Risk Coordinator (Cortez66) | `backend/core/gateway/risk_coordinator.py` (risk analysis) |
| Cognitive Engine (CRPE) | `backend/core/cognitive_engine.py` |
| LLM Factory | `backend/llm/factory.py` |
| ORM Models (Cortez42) | `backend/database/models/` (14 domain files) |
| Repositories (Cortez42/46) | `backend/database/repositories/` (12 domain files) |
| Simulators Agents (Cortez42) | `backend/agents/simulators/` (9 strategy files) |
| Tutor Agent (Cortez66) | `backend/agents/tutor/` (agent, rules, governance, metadata, prompts) |
| Tutor Modes (Cortez46/50) | `backend/agents/tutor_modes/` (base, socratic, explicative, guided, metacognitive, training_hints, factory) |
| Simulators Router (Cortez46) | `backend/api/routers/simulators/` (core, interview, incident, advanced) |
| Training Router (Cortez46) | `backend/api/routers/training/` (session_storage, helpers, endpoints) |
| Training Schemas (Cortez66) | `backend/api/schemas/training.py` (centralized location) |
| API Main | `backend/api/main.py` |
| Custom Exceptions (Cortez53) | `backend/api/exceptions.py` (50+ exception classes) |
| Frontend API Services | `frontEnd/src/services/api/` |
| Frontend Types (Cortez43) | `frontEnd/src/types/domain/` (11 domain files) |
| Frontend Features (Cortez43) | `frontEnd/src/features/` (training, tutor, simulators) |
| Frontend HTTP (Cortez43) | `frontEnd/src/core/http/` (CircuitBreaker, Metrics, Queue) |
| Frontend Shared Config (Cortez43/71) | `frontEnd/src/shared/config/` (labels, colors, constants, featureFlags) |
| Frontend Shared Utils (Cortez71) | `frontEnd/src/shared/utils/` (errorUtils, dateUtils) |
| Frontend Dynamic Styles (Cortez71) | `frontEnd/src/shared/styles/dynamicStyles.ts` |
| Teacher Traceability Service (Cortez63) | `frontEnd/src/services/api/teacherTraceability.service.ts` |
| Student Traceability Viewer (Cortez63) | `frontEnd/src/components/teacher/StudentTraceabilityViewer.tsx` |
| Teacher Layout (Cortez63) | `frontEnd/src/components/TeacherLayout.tsx` |
| LTI Router (Cortez65 - NOT ENABLED) | `backend/api/routers/lti.py` |
| LTI Service (Cortez65) | `frontEnd/src/services/api/lti.service.ts` |
| LTI Container (Cortez65) | `frontEnd/src/components/LTIContainer.tsx` |

### Cognitive State & Trace Types (Critical for N4 Traceability)

The system uses 8 cognitive states and 4 trace levels for N4 traceability:

```typescript
// Cognitive States - used throughout the system
type CognitiveState =
  | 'INICIO'            // Starting state
  | 'EXPLORACION'       // Exploring problem/solution
  | 'IMPLEMENTACION'    // Writing code
  | 'DEPURACION'        // Debugging
  | 'CAMBIO_ESTRATEGIA' // Changing approach
  | 'VALIDACION'        // Validating solution
  | 'ESTANCAMIENTO'     // Stuck (risk indicator)
  | 'REFLEXION';        // Reflecting on process

// Trace Levels - N4 is the highest synthesis level
type TraceLevel = 'N1' | 'N2' | 'N3' | 'N4';
// N1: Raw data, N2: Preprocessed, N3: LLM processed, N4: Synthesized

// AI Dependency Classification
// high: >70% - Students delegating too much to AI
// medium: 40-70% - Balanced use
// low: <40% - Predominantly autonomous work
```

## Critical Development Rules

### ORM vs Pydantic Field Mappings
```python
# Enum storage - always lowercase strings in DB:
session.status = "active"        # NOT "ACTIVE"
risk.risk_level = "critical"     # NOT "CRITICAL"

# Score scales:
evaluation.overall_score         # 0-10 scale
session_summary.overall_score    # 0-1 normalized
risk_analysis.overall_score      # 0-100 percentage
```

### Frontend-Backend Type Alignment
```typescript
// InteractionCreate - MUST use 'prompt' not 'student_input'
const interaction = { session_id: "...", prompt: "user message", context: {} };

// SessionMode - use enum, not string literal
import { SessionMode } from '../types';
const session = { mode: SessionMode.TUTOR };  // CORRECT
```

### React 19 Context Pattern
```typescript
// Use React 19's use() hook for context - NOT useContext()
import { createContext, use, type ReactNode } from 'react';

const MyContext = createContext<MyType | null>(null);

export function useMyContext(): MyType {
  const context = use(MyContext);  // React 19 pattern
  if (context === null) {
    throw new Error('useMyContext must be used within Provider');
  }
  return context;
}
```

### Zustand State Management (FIX Cortez31)
```typescript
// Use Zustand for UI state - simpler than Context
import { useUIStore, useSessionStore } from '@/stores';

// In components:
const { theme, toggleTheme, sidebarCollapsed, toggleSidebar } = useUIStore();
const currentSession = useSessionStore(state => state.currentSession);

// Stores are in src/stores/:
// - uiStore.ts: Theme and sidebar (persisted to localStorage)
// - sessionStore.ts: Current learning session
```

### React 19 Component Pattern (FIX Cortez32)
```typescript
// DON'T use React.FC (deprecated in React 19)
const MyComponent: React.FC<Props> = ({ prop }) => { ... };  // INCORRECT

// DO use function component with typed props
const MyComponent = ({ prop }: Props) => { ... };  // CORRECT
function MyComponent({ prop }: Props) { ... }      // ALSO CORRECT
```

### AIGateway is STATELESS
- All state persists to PostgreSQL via repositories
- No in-memory sessions/traces/risks
- Supports horizontal scaling

### Thread Safety (Required for Singletons)
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

### Batch Loading for N+1 Prevention
```python
# CORRECT - single query for all sessions
traces_by_session = trace_repo.get_by_session_ids(session_ids)

# INCORRECT - N+1 queries
for session_id in session_ids:
    traces = trace_repo.get_by_session(session_id)  # DON'T loop
```

### LLM Provider Methods are ASYNC
```python
response = await provider.generate(messages, temperature=0.7)  # CORRECT
```

### Async Semaphore Initialization (FIX Cortez70)
```python
# CORRECT - Double-checked locking for asyncio.Semaphore
async def _get_semaphore(self) -> asyncio.Semaphore:
    if self._semaphore is None:
        async with self._semaphore_lock:  # asyncio.Lock
            if self._semaphore is None:
                self._semaphore = asyncio.Semaphore(self._max_concurrent)
    return self._semaphore

# Usage - always await the getter
semaphore = await self._get_semaphore()
async with semaphore:
    response = await self._call_llm()
```

### Database Pessimistic Locking (FIX Cortez70)
```python
# CORRECT - Use SELECT FOR UPDATE for concurrent updates
from sqlalchemy import select

def update_with_lock(self, entity_id: str, **kwargs):
    try:
        stmt = select(EntityDB).where(EntityDB.id == entity_id).with_for_update()
        entity = self.db.execute(stmt).scalar_one_or_none()
        if entity:
            # Update fields...
            self.db.commit()
        return entity
    except Exception as e:
        self.db.rollback()
        raise
```

### Student Code Execution Security (FIX Cortez70)
```python
# NEVER use exec/eval directly in server process
exec(student_code, exec_globals)  # DANGEROUS - can escape sandbox

# ALWAYS use the sandbox utility
from backend.utils.sandbox import execute_python_code

stdout, stderr, exec_time = execute_python_code(
    code=student_code,
    test_input="",
    timeout_seconds=30
)
```

### Authentication Required
Most endpoints require authentication after cortez audits:
- Sessions, interactions, evaluations, traces, risks endpoints
- Teacher role required for activities management and reports

### Custom Exceptions (FIX Cortez33/53)
```python
# Use custom exceptions for consistent error handling (50+ classes available)
from ..exceptions import (
    SessionNotFoundError, TraceNotFoundError, ActivityNotFoundError,
    ReportNotFoundError, ReportGenerationError, ValidationError,
    NoDataFoundError, StudentIdsRequiredError, InvalidPeriodError,
)

# CORRECT - custom exception
if not session:
    raise SessionNotFoundError(session_id)

# CORRECT - re-raise custom exceptions in try/except blocks
try:
    do_something()
except AINativeAPIException:
    raise  # Re-raise custom exceptions
except Exception as e:
    raise ReportGenerationError("cohort report", str(e))

# INCORRECT - direct HTTPException
raise HTTPException(status_code=404, detail="...")  # DON'T
```

### UUID Validation (FIX Cortez33)
```python
from ..schemas.common import validate_uuid_format

# Always validate UUIDs before DB access
session_id = validate_uuid_format(session_id, "session_id")
db_session = session_repo.get_by_id(session_id)
```

### Database Commit Error Handling (FIX Cortez58)
```python
from ..exceptions import DatabaseOperationError

# CORRECT - wrap db.commit() in try-catch with rollback
try:
    db.add(entity)
    db.commit()
    db.refresh(entity)
except Exception as e:
    db.rollback()
    logger.error("Failed to create entity: %s", str(e))
    raise DatabaseOperationError(operation="create_entity", details=str(e))

# INCORRECT - bare commit without error handling
db.add(entity)
db.commit()  # DON'T - no rollback on failure
```

### get_current_user Returns Dict (FIX Cortez54)
```python
# CORRECT - access user_id from dict
async def my_endpoint(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")  # NOT current_user.id

# INCORRECT - treating as User object
async def my_endpoint(current_user: User = Depends(get_current_user)):
    user_id = current_user.id  # AttributeError!
```

### Datetime Naive vs Aware (FIX Cortez54/68)
```python
from datetime import datetime, timezone

# FIX Cortez68: NEVER use datetime.utcnow() - it's deprecated and returns naive datetime
# WRONG
timestamp = datetime.utcnow()  # Naive datetime - DON'T USE

# CORRECT - Always use timezone-aware datetime
timestamp = datetime.now(timezone.utc)  # Aware datetime with UTC timezone

def _ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware (UTC) for comparison."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)  # Assume UTC for DB values
    return dt

# Use when comparing datetimes from different sources
start_aware = _ensure_aware(db_session.start_time)
end_aware = _ensure_aware(db_session.end_time)
duration = (end_aware - start_aware).total_seconds()  # Safe comparison
```

### Session Mode Case Insensitivity (FIX Cortez54)
```python
# API now accepts both lowercase and uppercase mode values
# Model validators normalize to uppercase before enum validation

# Both of these now work:
{"mode": "TUTOR"}  # Original format
{"mode": "tutor"}  # Now also accepted (FIX Cortez54)
```

### LLM Concurrency Control (FIX Cortez34)
```python
# OllamaProvider now has configurable concurrency limiting
provider = LLMProviderFactory.create("ollama", {
    "max_concurrent": 10,  # Limit concurrent LLM requests (default: 10)
    "timeout": 60.0,       # Request timeout in seconds
})

# Internally uses asyncio.Semaphore to prevent overwhelming the LLM server
```

### LLM Call Timeouts (FIX Cortez68)
```python
# All LLM calls in AIGateway now have 30s timeouts to prevent indefinite hangs
import asyncio

LLM_TIMEOUT_SECONDS = 30.0
response = await asyncio.wait_for(
    self.llm.generate(messages, max_tokens=300, temperature=0.7),
    timeout=LLM_TIMEOUT_SECONDS
)
# TimeoutError is caught and triggers fallback response
```

### Token Validation Errors (FIX Cortez68)
```python
from backend.core.security import TokenExpiredError, TokenInvalidError, decode_access_token

# Use raise_on_error=True for specific error handling
try:
    payload = decode_access_token(token, raise_on_error=True)
except TokenExpiredError:
    # Token has expired - user should re-login
    raise HTTPException(status_code=401, detail="Token has expired. Please login again.")
except TokenInvalidError:
    # Token is malformed or has invalid signature
    raise HTTPException(status_code=401, detail="Invalid token.")
```

### Background Task Error Handling (FIX Cortez34)
```python
# Background tasks now have error callbacks for observability
task = asyncio.create_task(async_task())
task.add_done_callback(lambda t: log_task_errors(t))  # Errors are logged

# Always add done callbacks to fire-and-forget tasks
```

### LLM Provider HTTP Client (Cortez41)
```python
# GeminiProvider uses persistent HTTP client with connection pooling
# DO NOT create new client per request
client = await self._get_client()  # Returns pooled client

# Retry with jitter to prevent thundering herd
delay = self._calculate_retry_delay(attempt)  # Includes random jitter
```

### Algorithm Optimizations (Cortez41)
```python
# Use bisect for O(n log n) range queries instead of O(n²) nested loops
from bisect import bisect_right
sorted_timestamps = sorted([t.timestamp for t in traces if condition])
idx = bisect_right(sorted_timestamps, target_timestamp)

# Use fingerprinting for O(n) duplicate detection
from hashlib import md5
fp = md5(normalized_content.encode()).hexdigest()
```

### Frontend Error Handling Pattern
```typescript
// CORRECT: Use try-catch for localStorage parsing
getCurrentUser(): User | null {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch {
    return null;  // Handle corrupted localStorage
  }
}

// CORRECT: Use React Router for navigation, NOT window.location
import { useNavigate } from 'react-router-dom';
const navigate = useNavigate();
navigate('/dashboard');  // NOT window.location.href = '/dashboard'
```

### useEffect Cleanup Pattern
```typescript
// CORRECT: Always use AbortController for async operations
useEffect(() => {
  const abortController = new AbortController();

  const fetchData = async () => {
    try {
      const data = await service.getData();
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

### Browser Autocomplete Prevention (FIX Cortez63)
```typescript
// LoginPage: Browser autocomplete can override React state values
// causing login failures with incorrect credentials

// CORRECT: Use multiple techniques to disable autocomplete
<form onSubmit={handleSubmit} autoComplete="off">
  {/* Hidden fields to trick browser autocomplete */}
  <input type="text" name="prevent_autofill" style={{ display: 'none' }} />
  <input type="password" name="password_fake" style={{ display: 'none' }} />

  <input
    type="text"
    id="activia_user_field"           // Unique ID not matching typical patterns
    name="activia_user_field"         // Unique name
    value={username}
    onChange={(e) => setUsername(e.target.value)}
    autoComplete="off"
    autoCorrect="off"
    autoCapitalize="off"
    spellCheck="false"
    data-form-type="other"            // Tell browsers it's not a login form
    data-lpignore="true"              // Ignore by password managers
  />
</form>
```

### API Error Handling with Interceptors (FIX Cortez63)
```typescript
// The axios interceptor in client.ts transforms errors:
// - Server errors: returns { success: false, error: { message, error_code } }
// - Network errors: returns { success: false, error: { error_code: 'NETWORK_ERROR' } }
// These are NOT AxiosError instances anymore!

// CORRECT: Check for transformed error object first
} catch (err: unknown) {
  const apiError = err as { success?: boolean; error?: { message?: string } };

  if (apiError?.error?.message) {
    // Interceptor-transformed error
    setError(apiError.error.message);
  } else if (axios.isAxiosError(err)) {
    // Fallback for non-transformed errors
    setError(err.response?.data?.error?.message || 'Error');
  } else {
    setError('Error desconocido');
  }
}

// INCORRECT: Only checking axios.isAxiosError() first
if (axios.isAxiosError(err)) {  // Will be false for interceptor errors!
  setError(err.response?.data?.error?.message);
}
```

### Feature Flags (FIX Cortez71)
```typescript
// Use centralized feature flags instead of passing useV2 to hooks
import { featureFlags, isFeatureEnabled } from '@/shared/config/featureFlags.config';

// Check feature status
if (featureFlags.useV2TrainingEndpoints) {
  // Use V2 endpoints
}

// Or use helper function
if (isFeatureEnabled('enableN4Tracing')) {
  // Enable N4 traceability
}

// Available flags (with env var overrides):
// - useV2TrainingEndpoints (VITE_FEATURE_V2_TRAINING)
// - enableN4Tracing (VITE_FEATURE_N4_TRACING)
// - enableRiskMonitor (VITE_FEATURE_RISK_MONITOR)
// - enableLTIIntegration (VITE_FEATURE_LTI_INTEGRATION)
// - showDevFeatures (import.meta.env.DEV)
// - enableApiLogging (import.meta.env.DEV)
```

### Centralized Error Handling (FIX Cortez71)
```typescript
// Use errorUtils for consistent error message extraction
import { getApiErrorMessage, isNetworkError } from '@/shared/utils/errorUtils';

try {
  await apiCall();
} catch (err) {
  const message = getApiErrorMessage(err, 'Error al procesar la solicitud');

  if (isNetworkError(err)) {
    setError('Sin conexión a internet');
  } else {
    setError(message);
  }
}
```

## DevOps Infrastructure (Cortez37-39)

### CI/CD Pipeline (`.github/workflows/`)
- **ci.yml**: Original pipeline (415 lines) - preserved for compatibility
- **ci-modular.yml (Cortez45/59+)**: Modular 14-stage pipeline using reusable workflows
- **security.yml**: Original security scans (247 lines) - preserved for compatibility
- **security-modular.yml (Cortez45)**: Optimized security (removed pip-audit/Gitleaks redundancy)
- **Reusable Workflows (12 total)**:
  - Core: `reusable-lint.yml`, `reusable-test-backend.yml`, `reusable-test-frontend.yml`
  - Security: `reusable-security.yml`
  - Validation (Cortez59): `reusable-migrations.yml`, `reusable-exercises.yml`
  - Quality (Cortez59+): `reusable-llm-health.yml`, `reusable-api-contract.yml`, `reusable-performance.yml`, `reusable-e2e-training.yml`
  - Build/Deploy: `reusable-build.yml`, `reusable-deploy.yml`

### GitHub Automation (Cortez45 - `.github/`)
- **Issue Templates**: bug_report.yml, feature_request.yml, documentation.yml, question.yml
- **PR Template**: pull_request_template.md (code quality, security, testing checklist)
- **Automation**: stale.yml (60d issues, 30d PRs), release.yml (auto changelog), labeler.yml (auto-labels)
- **Configuration**: CODEOWNERS (auto-reviewers), SECURITY.md, dependabot.yml, FUNDING.yml

### Production Stack (`docker-compose.prod.yml`)
- No exposed database ports (PostgreSQL, Redis internal only)
- Internal networks for isolation
- Read-only containers where possible
- Resource limits enforced
- Redis dangerous commands disabled

### Modular Docker Compose (Cortez44 - `infra/docker/compose/`)
```bash
# Core stack only
docker-compose -f docker-compose.base.yml up -d

# With monitoring
docker-compose -f docker-compose.base.yml -f docker-compose.monitoring.yml up -d

# With debug tools
docker-compose -f docker-compose.base.yml -f docker-compose.debug.yml up -d

# With local Ollama (GPU)
docker-compose -f docker-compose.base.yml -f docker-compose.ollama.yml up -d
```

### Kubernetes (`devops/kubernetes/staging/`)
- **06-backend.yaml**: RBAC (Role + RoleBinding), separate Redis env vars (Cortez39)
- **05-redis.yaml**: TCP probes instead of exec (security - no password in process list)
- **07-frontend.yaml**: imagePullPolicy=IfNotPresent, memory 256Mi
- **09-network-policies.yaml**: Pod-to-pod traffic isolation, exporter support
- **10-pod-disruption-budgets.yaml**: Minimum 2 backend pods available
- **sql/ (Cortez44)**: Modular SQL files (00-extensions.sql through 10-sample-data.sql)
- **init-database-v2.sh (Cortez44)**: Modular database initialization script

### Monitoring (`devops/monitoring/`)
- **prometheus-alerts.yml**: Comprehensive alert rules (API, PostgreSQL, Redis, Infrastructure)
- **alertmanager/alertmanager.yml**: Alert routing by severity (critical → email + Slack)
- **grafana/provisioning/**: Datasources and dashboard provisioning
- **PostgreSQL Exporter**: Metrics for database
- **Redis Exporter**: Metrics for cache (requires REDIS_PASSWORD)

### Security Audit (`devops/security-audit/` - Cortez44)
- **analyzers/**: Modular security analyzers (ZAP, Trivy, Kubesec, TruffleHog)
- **analyze_security_v2.py**: Orchestrates all analyzers with OWASP Top 10 mapping

### Shell Scripts (Portable - Cortez39)
All scripts in `devops/` now work on GNU/Linux and macOS:
- **deploy.sh**: Image validation for CI/CD, storage class check, configurable DOMAIN
- **setup-ingress.sh**: Configurable LETSENCRYPT_EMAIL and DOMAIN via env vars
- **verify.sh**: jq is optional (graceful degradation)
- **rollback.sh**: Deployment existence check before rollback
- **run-load-test.sh**: Portable sed (works on BSD/GNU)
- **run-security-scan.sh**: Portable sed, jq checks throughout

### Security Headers (Nginx)
```nginx
# All OWASP recommended headers in frontEnd/nginx.conf
Content-Security-Policy, X-Frame-Options, X-Content-Type-Options,
Referrer-Policy, Permissions-Policy
```

## Environment Configuration

Key `.env` variables (see `.env.example` for full template):

**Required:**
- `POSTGRES_PASSWORD`, `REDIS_PASSWORD` - Database credentials
- `JWT_SECRET_KEY`, `SECRET_KEY` - Generate with `make generate-secrets`

**LLM:**
- `LLM_PROVIDER`: `gemini` (recommended) | `ollama` | `mock` | `openai` | `mistral`
- `OLLAMA_BASE_URL`: `http://localhost:11434` (local) or `http://ollama:11434` (Docker)
- `OLLAMA_MODEL`: `phi3` (recommended)
- `GEMINI_API_KEY`: Required if using Gemini provider

**Metrics Security (FIX Cortez34):**
- `METRICS_API_KEY`: Required for remote access to `/metrics` endpoint (local IPs exempt)

**Training Integration (Cortez50):**
- `TRAINING_USE_TUTOR_HINTS`: Enable T-IA-Cog contextual hints (default: false)
- `TRAINING_N4_TRACING`: Enable N4 cognitive traceability (default: false)
- `TRAINING_RISK_MONITOR`: Enable real-time risk detection (default: false)

**LTI 1.3 Integration (Cortez65 - NOT ENABLED by default):**
- `LTI_ENABLED`: Master switch for LTI router (default: false)
- `LTI_FRONTEND_URL`: Frontend URL for redirects after launch (default: http://localhost:3000)
- `LTI_STATE_EXPIRATION_MINUTES`: OIDC state TTL (default: 10)
- `LTI_NONCE_EXPIRATION_HOURS`: Replay protection window (default: 1)
- `LTI_JWKS_CACHE_TTL_SECONDS`: Platform JWKS cache (default: 3600)
- To enable: Set `LTI_ENABLED=true` and add router to `main.py`

**CI/CD (GitHub Actions):**
- `KUBE_CONFIG_STAGING`: Base64 kubeconfig for staging
- `KUBE_CONFIG_PRODUCTION`: Base64 kubeconfig for production

## Documentation

**Entry Points (Cortez49/50/53 - Comprehensive prose explanations):**
- `backend/README.md` - Backend architecture with 17 sections (924 lines) - Updated Cortez53 with full Trainer+Agents integration
- `frontEnd/README.md` - Frontend architecture with 15 sections (1,350+ lines)
- `backend/agents/README.md` - AI agents documentation with Section 10 on Trainer distinction

**Architecture Proposals:**
- `backend/ImplementacionAgentes.md` - **Multi-Agent Active-IA technical proposal** (1,115 lines)
  - 6 agents specification: CognitiveGatekeeper, KnowledgeRetrievalAgent (RAG), T-IA-Cog, FallbackPedagogico, Safety&Governance, ScaffoldingAgent
  - Gap analysis: Knowledge-Retrieval missing, CRPE needs routing capabilities, Scaffolding fragmentado
  - RAG integration options: ChromaDB (MVP) or PostgreSQL+pgvector (production)
  - 5-phase migration plan with feature flags for gradual rollout
- `stack.md` - **Technology Stack Recommendation** (900+ lines)
  - pgvector over Pinecone/Weaviate: $0 vs $70/month, ACID transactions, hybrid SQL+vector queries
  - nomic-embed-text: 384 dimensions, 62.3 MTEB score, comparable to OpenAI at $0
  - LLM tiered strategy: Gatekeeper/Safety/Scaffolding use phi3 local, only Tutor uses Mistral API
  - Cost projections: thesis ($10/month), pilot course ($65/month), multi-course ($575/month)
  - Docker Compose updates, pgvector migration, 5-phase implementation
- `backend/docs/entrenador.md` - C4 proposal for Digital Trainer integration with agents (1,100+ lines)
- `backend/docs/entrenador1.md` - Prose implementation guide (466 lines, 4 phases)
- `docs/factiblerag.md` - **RAG Integration Feasibility Analysis** (January 2026)
  - Analysis of `rag1.txt` proposal (~2,800 lines of proposed refactoring)
  - Verdict: FEASIBLE with conditions (integration, not replacement)
  - 6-phase implementation plan (~11 weeks): pgvector, academic catalog, HU+CA, RAG+AIGateway, event sourcing, MinIO
  - Risk analysis: technical, business, and project risks with mitigations
  - Recommendation: Adopt pgvector+RAG while preserving 6 AI agents and N4 traceability
- `docs/Factiblerag1.md` - **RAG Implementation Guide** (~2,072 lines, January 2026)
  - **Part I**: Fundamentos Arquitectónicos - Deep analysis of current system (6 agents, N4 traceability, AIGateway)
  - **Part II**: Estrategia de Integración RAG - 6-phase implementation with complete code examples:
    - Phase 1: pgvector infrastructure (ContentChunkDB, RAGRepository, EmbeddingService)
    - Phase 2: Extended academic catalog (MateriaDB, UnidadDB with embeddings)
    - Phase 3: HU+CA pattern for exercises (non-destructive EjercicioDB extensions)
    - Phase 4: RAG + AIGateway integration (RAGCoordinator following coordinator pattern)
    - Phase 5: Complementary event sourcing (AIEventDB for audit trail)
    - Phase 6: MinIO storage (StorageProvider abstraction for local/cloud)
  - **Part III**: Verificación y Mantenimiento - Integration tests and checklists per phase
  - Key patterns: Feature flags (`RAG_ENABLED`), abstract interfaces, non-destructive migrations

**Essential Reading:**
- `docs/Misagentes/integrador.md` - Complete multi-agent system documentation
- `docs/api/README_API.md` - REST API reference
- `docs/llm/OLLAMA_QUICKSTART.md` - LLM setup guide
- `docs/moodle.md` - **LTI 1.3 Moodle Integration** (v3.3) - Complete admin guide with 17 subsections for configuring Moodle as LTI platform + Activity-Moodle linking (Section 11.5)

**User Guides:**
- `GUIA_ESTUDIANTE.md`, `GUIA_DOCENTE.md`, `GUIA_ADMINISTRADOR.md`

## Audit History

71+ audits have been performed on this codebase. Key audits with documentation:

| Audit | Focus | Issues | Docs |
|-------|-------|--------|------|
| Cortez71 | Frontend Audit | 27/27 fixed (100%): demo credentials, key={index}, AbortController, feature flags, Health Score 7.5→9.2 | `docs/audits/CORTEZ71_FRONTEND_AUDIT.md` |
| Cortez70 | Backend Concurrency & Security Audit | 14 CRITICAL fixed: thread locks, DB locking, sandbox exec, N+1→batch, Health Score 8.2→8.8 | This CLAUDE.md |
| Cortez69 | Backend Inconsistency Audit | 238 issues (14 CRIT), auth + prompt injection, score 6.8→8.2 | `docs/audits/CORTEZ69_COMPREHENSIVE_BACKEND_AUDIT.md` |
| Cortez68 | Comprehensive Backend Audit + Full Remediation | 113 issues (8 CRIT, 22 HIGH, 50 MED, 33 LOW) - **All CRIT+HIGH fixed**, Health Score 7.5→9.0 | `docs/audits/CORTEZ68_COMPREHENSIVE_BACKEND_AUDIT.md` |
| Cortez67 | Memory & Concurrency Audit | 8 issues fixed: bounded caches, TTL cleanup, async session storage | `docs/audits/CORTEZ67_MEMORY_CONCURRENCY_AUDIT.md` |
| Cortez66 | Backend Architecture Audit | 5 phases: coordinator extraction, tutor consolidation, schema consolidation, repository standards | This CLAUDE.md |
| Cortez65.2 | Academic Context without LTI | UserDB 2 new fields, UserRepository 3 methods, auth schemas updated, TutorHeader badges, 1 migration | This CLAUDE.md |
| Cortez65.1 | LTI Activity-Moodle Linking | 3 new endpoints, ActivityDB 4 Moodle fields, ActivityRepository 5 methods, automatic matching, 2 migrations | `backend/api/routers/lti.py`, `docs/moodle.md` v3.3 |
| Cortez65 | LTI 1.3 Implementation (NOT ENABLED) | Router (~650 lines), config, frontend service, LTIContainer, **Moodle Admin Guide v3.1** (17 subsections) | `backend/api/routers/lti.py`, `docs/moodle.md` |
| Cortez64 | CRPE Signal Expansion + New Response Types | ~137 signals, 7 response types, 4 new handlers, 4 fallbacks | This CLAUDE.md |
| Cortez63 | N4 Traceability for Teachers + Frontend | 3 backend endpoints, teacherTraceability.service.ts, StudentTraceabilityViewer, TeacherLayout, Maestro-Detalle, autocomplete fix | This CLAUDE.md, `frontEnd/README.md` |
| Cortez62 | Technology Stack Proposal | stack.md (900+ lines): pgvector, nomic-embed-text, Mistral+phi3, cost analysis | `stack.md` |
| Cortez61 | Multi-Agent Architecture Proposal | ImplementacionAgentes.md rewritten (1,115 lines), frontend README Section 8 added | `backend/ImplementacionAgentes.md` |
| Cortez59+ | GitHub CI/CD Complete | 6 new workflows, 14-stage pipeline, all gaps implemented | `.github/README.md` |
| Cortez59 | GitHub CI/CD Enhancement | Gap analysis, documentation rewrite, initial 2 workflows | `.github/README.md` |
| Cortez58 | Backend Obsolete Code Cleanup | 964 lines removed, 4 error handlers added | `docs/audits/CORTEZ58_BACKEND_OBSOLETE_AUDIT.md` |
| Cortez57 | Frontend Obsolete Code Cleanup | 347 lines removed, types consolidated | `docs/audits/CORTEZ57_FRONTEND_OBSOLETE_AUDIT.md` |
| Cortez56 | Backend V1 Legacy Endpoints | 3 new endpoints, datetime fix, parameter fix | This CLAUDE.md |
| Cortez55 | Frontend Digital Trainer V2 | V2 endpoints, hooks, 4 new components | This CLAUDE.md |
| Cortez54 | Backend Endpoint Audit | 12 defects fixed (missing methods, datetime, encoding) | `docs/audits/CORTEZ54_BACKEND_ENDPOINT_AUDIT.md` |
| Cortez53 | HTTPException Migration | 51 HTTPExceptions → custom exceptions, 14 new exception classes | This CLAUDE.md |
| Cortez52 | Backend Architect Audit | 26 findings, N+1 fixed, TTL cleanup | This CLAUDE.md |
| Cortez51 | Backend Deep Audit | 33 findings, 5 critical fixed, custom exceptions migrated | This CLAUDE.md |
| Cortez50 | Digital Trainer Integration | **IMPLEMENTED**: T-IA-Cog + N4 traceability (10 files, ~2,500 lines) | `backend/core/training_*.py`, `integration_endpoints.py` |
| Cortez49 | Documentation Complete | Backend + Frontend READMEs with prose explanations | `backend/README.md`, `frontEnd/README.md` |
| Cortez48 | Frontend Senior Audit | 57 issues found, **all critical/high FIXED** | `docs/audits/CORTEZ48_FRONTEND_AUDIT.md` |
| Cortez47 | Backend Deep Audit | 8,544 lines removed (3 monolithic files deleted) | This CLAUDE.md |
| Cortez46 | Backend Modularization | Repos extracted, routers split, 12 new exceptions | `backend/api/routers/training/`, `simulators/` |
| Cortez45 | GitHub Folder Audit | ci.yml + security.yml modularized, templates added | `.github/README.md` |
| Cortez44 | DevOps Refactoring | 4 monolithic files → modular | `devops/security-audit/analyzers/`, `.github/workflows/reusable-*.yml` |
| Cortez43 | Frontend Refactoring | 5 monolithic files → modular | `frontEnd/src/features/`, `src/types/domain/` |
| Cortez42 | Backend Refactoring | 4 monolithic files → modular | `docs/audits/CORTEZ42_REPOSITORY_REFACTORING.md` |
| Cortez41 | Backend Optimizations | 10 optimizations | `docs/audits/CORTEZ41_BACKEND_OPTIMIZATIONS_APPLIED.md` |
| Cortez40 | Frontend & DevOps Optimization | 17 FE + 32 DevOps optimizations | `frontEnd/FRONTEND_OPTIMIZATIONS_APPLIED.md`, `devops/OPTIMIZATIONS_APPLIED.md` |
| Cortez39 | DevOps Infrastructure Audit | 45+ fixed: Redis URL bug, portable scripts, monitoring | `docs/audits/` |
| Cortez38 | DevOps Senior Architect | 30 defects, SecurityContext, secrets validation | `docs/audits/` |
| Cortez37 | DevOps Complete Audit | CI/CD, Production hardening, K8s policies | `docs/audits/` |
| Cortez36 | Code Anomalies & Inconsistencies | 77 identified, 17 fixed | `docs/audits/CORTEZ36_CODE_ANOMALIES_AUDIT.md` |
| Cortez35 | Memory Leaks & Concurrency | 52 identified, 6 fixed | `docs/audits/CORTEZ35_MEMORY_CONCURRENCY_AUDIT.md` |
| Cortez34 | Senior Backend Audit | 115 identified, 9 fixed | `docs/audits/CORTEZ34_BACKEND_SENIOR_AUDIT.md` |
| Cortez33 | Backend Architecture | 67 identified, 40+ fixed | `docs/audits/CORTEZ33_BACKEND_ARCHITECT_AUDIT.md` |
| Cortez32 | Frontend Senior Review | 31 fixed | `docs/audits/CORTEZ32_FRONTEND_SENIOR_AUDIT.md` |
| Cortez31 | Zustand Migration | 76 identified | `docs/audits/CORTEZ31_*.md` |
| Cortez30 | Memory Leaks | 33 fixed | `docs/audits/CORTEZ30_MEMORY_LEAKS_AUDIT.md` |
| Cortez28 | React 19 Migration | - | React 19 + ESLint 9 flat config |
| Cortez25 | Backend Startup | 4 | JSONB/SQLite compat, User model |

**Key patterns established by audits:**
- React 19: Use `use()` hook for context, function components (not `React.FC`)
- Zustand: `uiStore.ts` (theme/sidebar), `sessionStore.ts` (session state)
- Memory leaks: Always use `isMounted` checks or `AbortController` in async useEffect
- Backend: Custom exceptions, UUID validation, thread-safe singletons
- LLM: Semaphore-based concurrency control (`max_concurrent`), background task error callbacks
- DevOps: CI/CD via GitHub Actions, production hardening, Kubernetes network policies
- DevOps (Cortez39): Portable scripts (BSD/GNU), monitoring infrastructure complete, RBAC for backend pods
- Frontend (Cortez40): Lazy loading pages, useMemo/useCallback for expensive calculations, `useFetchSessions` hook, reusable Modal component
- Backend (Cortez41): O(n²)→O(n log n) with bisect, HTTP connection pooling, retry jitter, periodic cache cleanup
- Backend (Cortez42): Modular architecture - repositories (12 files), models (14 files), simulators (9 files with Strategy Pattern)
- Frontend (Cortez43): Feature-based architecture - types (11 domain files), features (training, tutor, simulators), HTTP utilities (CircuitBreaker, Metrics, Queue)
- DevOps (Cortez44): Modular security analyzers, reusable GitHub workflows, SQL modules for database init, composable docker-compose files
- GitHub (Cortez45): Modular CI/CD (`ci-modular.yml`), optimized security scans (`security-modular.yml`), issue/PR templates, dependabot configuration
- Backend (Cortez46): Complete repository extraction, router modularization (training/, simulators/), tutor_modes Strategy Pattern, 12 new custom exceptions, lazy logging
- Backend (Cortez47): Final cleanup - deleted 8,544 lines of shadowed monolithic files (models.py, repositories.py, simulators.py), verified import resolution
- Frontend (Cortez48): Senior audit found 57 issues, **all critical/high FIXED**:
  - ✅ Demo credentials conditional to `import.meta.env.DEV`
  - ✅ `ErrorBoundaryWithNavigation` wrapper for React Router navigation
  - ✅ AbortController in GitAnalytics.tsx
  - ✅ 28 React.FC → function components (18 files)
  - ✅ Critical key={index} fixed (use email/date as keys)
- Architecture (Cortez50): Digital Trainer integration **IMPLEMENTED**:
  - TrainingGateway: Central orchestrator connecting Trainer to agents
  - TrainingHintsStrategy: Extends GuidedStrategy for exercise-specific contextual hints
  - TrainingTraceCollector: N4 trace capture with cognitive state inference (Strategy A)
  - TrainingRiskMonitor: Real-time detection of copy-paste, frustration, hint dependency
  - Hybrid N4 traceability model: Inferred (passive) + Optional (semi-active) + Reflection (active)
  - Feature flags for gradual rollout: `TRAINING_USE_TUTOR_HINTS`, `TRAINING_N4_TRACING`, `TRAINING_RISK_MONITOR`
  - New V2 endpoints: `/pista/v2`, `/reflexion`, `/sesion/{id}/proceso`, `/submit/v2`
- Backend (Cortez51): Deep audit with exception handling remediation:
  - ✅ Silenced exceptions fixed: Always log or re-raise, never `except: pass`
  - ✅ HTTPException migration: Use custom exceptions (`SessionNotFoundError`, `AuthenticationError`, etc.)
  - ✅ Specific exception types: `except (ValueError, base64.binascii.Error)` instead of broad `except Exception`
  - ✅ Optional authentication pattern: `OAuth2PasswordBearer(auto_error=False)` + `get_optional_current_user()`
  - ✅ Lazy logging: Use `logger.debug("msg: %s", var)` not f-strings
  - ✅ Clean imports: Remove unused `func`, `select`, `Response` from routers
- Backend (Cortez53): Complete HTTPException migration across all routers:
  - ✅ 51 HTTPExceptions migrated to domain-specific custom exceptions
  - ✅ 14 new exception classes: `NoDataFoundError`, `ReportGenerationError`, `RiskScanError`, etc.
  - ✅ Pattern: `except AINativeAPIException: raise` before `except Exception` for proper propagation
  - ✅ All routers now use custom exceptions - no `raise HTTPException` in routers (only in `deps.py`)
  - ✅ Exception classes provide structured error responses with `error_code` and `extra` metadata
- Backend (Cortez54): Comprehensive endpoint audit with 12 defects fixed:
  - ✅ ExerciseRepository: Added `get_by_language_and_unit()`, `get_by_language()`, `get_languages_with_units()`
  - ✅ SimuladorProfesionalAgent: Always pass `simulator_type` argument when instantiating
  - ✅ Datetime handling: Use `_ensure_aware()` helper to handle naive vs aware comparison
  - ✅ Session schemas: Accept lowercase mode values via model validators ("tutor" → "TUTOR")
  - ✅ UTF-8 encoding: Custom `UTF8JSONResponse` class with `ensure_ascii=False` as default
  - ✅ User dict: `get_current_user()` returns dict with `user_id` key, not User object with `.id` attribute
  - ✅ Emoji removal: Don't use emoji in log messages (Windows cp1252 encoding issues)
- Frontend (Cortez63): Teacher routes and login improvements:
  - ✅ TeacherLayout: Dedicated layout for `/teacher/*` routes with purple/violet theme
  - ✅ ActivityManagementPage: Maestro-Detalle pattern for activity + exercises
  - ✅ LoginPage: Browser autocomplete prevention (hidden fields, unique names, data attributes)
  - ✅ Error handling: Fixed API error extraction from interceptor-transformed errors
  - ✅ App.tsx: Routes restructured with TeacherLayout for teacher section
- LTI (Cortez65.1): Activity-Moodle linking for automatic activity detection:
  - ✅ ActivityDB: 4 new Moodle fields (`moodle_course_id`, `moodle_course_name`, `moodle_course_label`, `moodle_resource_name`)
  - ✅ ActivityRepository: 5 new methods for Moodle integration
- Backend (Cortez66): Architecture audit with 5 phases of remediation:
  - ✅ Gateway coordinators extracted: `response_generators.py`, `trace_coordinator.py`, `risk_coordinator.py`
  - ✅ Tutor agent consolidated: `agents/tutor/` package (agent, rules, governance, metadata, prompts)
  - ✅ Training schemas centralized: `api/schemas/training.py` (357 lines)
  - ✅ Repository standards: Documented naming conventions in BaseRepository
  - ✅ All backward-compatible wrappers in original locations
  - ✅ LTI Launch: Automatic activity matching (Strategy 1: course+resource, Strategy 2: resource only)
  - ✅ 3 new endpoints: `POST /lti/activities/link`, `DELETE /lti/activities/{id}/link`, `GET /lti/activities/linked`
  - ✅ LTISessionDB: Added `resource_link_title` column
  - ✅ 2 migrations: `add_resource_link_title.py`, `add_moodle_fields_to_activities.py`
  - ✅ Documentation: `docs/moodle.md` updated to v3.3 with Section 11.5
- Academic Context (Cortez65.2): Student course/commission display without LTI:
  - ✅ UserDB: 2 new fields (`course_name`, `commission`) for testing phase
  - ✅ UserRepository: 3 new methods (`update_academic_context()`, `get_by_commission()`, `get_students_by_course()`)
  - ✅ Auth schemas: `UserResponse` includes `course_name` and `commission`
  - ✅ TutorHeader: Displays academic context badges (BookOpen + Users icons)
  - ✅ 1 migration: `add_user_academic_context.py` with commission index
- Backend (Cortez70): Concurrency & Security audit with 14 CRITICAL fixes:
  - ✅ Thread Safety: Use `threading.Lock()` for shared in-memory state (`_session_states`, `_attempt_cache`)
  - ✅ Async Concurrency: Double-checked locking pattern for `asyncio.Semaphore` initialization
  - ✅ Database Locking: Use `with_for_update()` for pessimistic locking on concurrent updates
  - ✅ Code Execution: Never use `exec()/eval()` directly - use `execute_python_code()` sandbox
  - ✅ N+1 Queries: Batch load data upfront, process in memory (5 queries vs 5N-10N)
  - ✅ Timezone Handling: Always use `datetime.now(timezone.utc)` and `replace(tzinfo=timezone.utc)`
  - ✅ Dead Code: Remove unused methods after refactoring (240 lines removed)

## Detailed Documentation

For comprehensive guidance including all critical rules, field mappings, and detailed architecture, see:

**`activia1-main/docs/CLAUDE.md`** (700+ lines of detailed guidance)

This file contains:
- Complete ORM vs Pydantic field mappings
- All 102 API routes across 22 categories
- N4 Traceability levels and cognitive dimensions
- Governance semaphore system (verde/amarillo/rojo)
- Tutor pedagogical rules (4 unbreakable rules)
- Risk dimensions (5D) and risk types (16 types)

## Known Issues

| Issue | Location | Priority | Notes |
|-------|----------|----------|-------|
| key={index} anti-pattern | Multiple files | Medium | Static lists OK, dynamic lists need unique IDs (30→improved in Cortez71) |
| Inline styles in JSX | GitAnalytics.tsx, TraceabilityDisplay.tsx | Low | `dynamicStyles.ts` utility created (Cortez71) |
| CSS legacy files | GitAnalytics.css, TutorChat.css | Low | Documented for future Tailwind migration (Cortez71) |
| AIGateway needs more extraction | `ai_gateway.py` | Low | Phase 1 done, coordinators pending |

**Fixed in Cortez71 (Frontend Audit - 27/27 = 100%):**
- ✅ CRIT-001: Demo credentials DEV-only conditional
- ✅ CRIT-002: Removed all credential/sensitive console logging
- ✅ HIGH-001 to HIGH-005: key={index} patterns, AbortController, stable keys
- ✅ MED-001 to MED-008: Type aliases deprecated, useMemo fixed, feature flags centralized
- ✅ LOW-001 to LOW-012: Dynamic styles, date formatting, ESLint disable justifications
- New utilities: `errorUtils.ts`, `featureFlags.config.ts`, `dateUtils.ts`, `dynamicStyles.ts`
- Full report: `docs/audits/CORTEZ71_FRONTEND_AUDIT.md`

**Fixed in Cortez48 (Frontend Senior Audit):**
- ✅ 3 critical issues: Demo credentials, window.location, AbortController
- ✅ 28 React.FC patterns → function components
- ✅ Critical key={index} patterns (contributors, trends)
- Full report: `docs/audits/CORTEZ48_FRONTEND_AUDIT.md`

**Cleaned in Cortez47:**
- ✅ `models.py` (1,772 lines) - DELETED (shadowed by `backend/database/models/` package)
- ✅ `repositories.py` (5,134 lines) - DELETED (shadowed by `backend/database/repositories/` package)
- ✅ `simulators.py` (1,638 lines) - DELETED (shadowed by `backend/agents/simulators/` package)

**Cleaned in Cortez46:**
- ✅ `training_legacy.py`, `simulators_legacy.py` - Removed (modular packages active, no dependencies)
- ✅ Windows `nul` artifacts (2 files) - Removed

**Fixed in Cortez34:**
- ✅ `time.sleep()` in async code → `asyncio.sleep()` (`auth_new.py`)
- ✅ Background tasks without error handling → `add_done_callback()` (`ai_gateway.py`)
- ✅ `/metrics` endpoint unprotected → IP + API key auth (`metrics.py`)
- ✅ LLM unbounded concurrency → Semaphore limiting (`ollama_provider.py`)

**Added in Cortez37-39 (DevOps):**
- ✅ CI/CD pipeline with GitHub Actions (`.github/workflows/ci.yml`)
- ✅ Security scanning workflow (`.github/workflows/security.yml`)
- ✅ Production docker-compose (`docker-compose.prod.yml`)
- ✅ Nginx security headers (CSP, HSTS, Permissions-Policy)
- ✅ Alertmanager configuration (`devops/monitoring/alertmanager/`)
- ✅ Prometheus alerts (`devops/monitoring/alerts/prometheus-alerts.yml`)
- ✅ Grafana provisioning (`devops/monitoring/grafana/provisioning/`)
- ✅ PostgreSQL & Redis exporters for Prometheus
- ✅ Kubernetes NetworkPolicies and PodDisruptionBudgets
- ✅ RBAC for backend pods (`devops/kubernetes/staging/06-backend.yaml`)
- ✅ TCP probes for Redis (security - no password in process list)
- ✅ Portable shell scripts (BSD/GNU compatible)
- ✅ CI/CD image validation in deploy.sh
- ✅ Configurable DOMAIN/LETSENCRYPT_EMAIL via env vars

**Added in Cortez40 (Frontend & DevOps Optimization):**
- ✅ Vite build optimizations: terser, manual chunks (`vite.config.ts`)
- ✅ Lazy loading for all pages (~60% bundle reduction) (`App.tsx`)
- ✅ useMemo/useCallback in DashboardPage, AnalyticsPage
- ✅ Accessibility: Escape key handler, ARIA labels (`Layout.tsx`)
- ✅ `useFetchSessions` custom hook (`hooks/useFetchSessions.ts`)
- ✅ Reusable Modal component (`shared/components/Modal/`)
- ✅ DevOps shared library (`devops/common/` - colors, logging, k8s-utils, shell-utils)
- ✅ Parallel deployment option (`PARALLEL_DEPLOY=true`)
- ✅ Resource limits 2:1 ratio (was 4:1)

**Added in Cortez41 (Backend Optimizations):**
- ✅ O(n²) → O(n log n) using bisect (`risk_analyst.py:_analyze_epistemic_risks`)
- ✅ O(n²) → O(n) fingerprinting for duplicates (`risk_analyst.py:_analyze_technical_risks`)
- ✅ frozenset for O(1) delegation signal lookup (`risk_analyst.py`)
- ✅ Persistent HTTP client with connection pooling (`gemini_provider.py`)
- ✅ Retry with jitter to prevent thundering herd (`gemini_provider.py`)
- ✅ Periodic cache cleanup background task (`cache.py`, `main.py`)
- ✅ Module constants for configurable thresholds (`risk_analyst.py`)

**Added in Cortez42 (Backend Refactoring):**
- ✅ **Repositories**: `repositories.py` (5,134 lines) → 9 modules in `backend/database/repositories/`
  - SessionRepository, TraceRepository, RiskRepository, EvaluationRepository
  - ActivityRepository, UserRepository
  - ExerciseRepository, HintRepository, TestRepository, AttemptRepository, RubricRepository
- ✅ **Models**: `models.py` (1,772 lines) → 14 modules in `backend/database/models/`
  - SessionDB, CognitiveTraceDB, TraceSequenceDB, RiskDB, EvaluationDB
  - UserDB, ActivityDB, StudentProfileDB, GitTraceDB
  - CourseReportDB, RemediationPlanDB, RiskAlertDB
  - InterviewSessionDB, IncidentSimulationDB, SimulatorEventDB
  - LTIDeploymentDB, LTISessionDB, SubjectDB
  - ExerciseDB and 5 related models
- ✅ **Simulators**: `simulators.py` (1,638 lines) → 9 modules in `backend/agents/simulators/`
  - Strategy Pattern: BaseSimulator abstract class + SimulatorFactory
  - ProductOwnerSimulator, ScrumMasterSimulator, TechInterviewerSimulator
  - IncidentResponderSimulator, DevSecOpsSimulator, ClientSimulator
  - SimuladorProfesionalAgent wrapper for backward compatibility
- ✅ **Gateway**: Protocols and fallback responses extracted to `backend/core/gateway/`
- ✅ All modules have backward-compatible `__init__.py` with re-exports

**Added in Cortez43 (Frontend Refactoring):**
- ✅ **Types**: `api.types.ts` (893 lines) → 11 modules in `frontEnd/src/types/domain/`
  - enums.ts, labels.ts, session.types.ts, interaction.types.ts, trace.types.ts
  - risk.types.ts, evaluation.types.ts, activity.types.ts, simulator.types.ts
  - git.types.ts, api.types.ts (wrappers), index.ts (barrel export)
- ✅ **Training Feature**: `TrainingExamPage.tsx` (638 lines) → `frontEnd/src/features/training/`
  - Hooks: useTimer, useTrainingSession
  - Components: LoadingState, ErrorState, FinalResults, ProgressBar, ExerciseResultBanner, ExercisePanel, CodeEditorPanel, SessionHeader
- ✅ **Tutor Feature**: `TutorPage.tsx` (605 lines) → `frontEnd/src/features/tutor/`
  - Hooks: useTutorSession, useRiskAnalysis, useTraceability
  - Components: TutorHeader, ChatMessageBubble, ChatInput, SuggestedQuestions, TypingIndicator, Modal
- ✅ **Simulators Feature**: `SimulatorsPage.tsx` (514 lines) → `frontEnd/src/features/simulators/`
  - Hook: useSimulatorSession
  - Components: SimulatorCard, SimulatorChatView, SimulatorGrid
  - Config: simulatorConfig.ts (icons, colors, welcome messages)
- ✅ **HTTP Utilities**: `HttpClient.ts` → modular in `frontEnd/src/core/http/`
  - CircuitBreaker.ts, HttpMetrics.ts, RequestQueue.ts, retryUtils.ts
- ✅ **Shared Config**: `frontEnd/src/shared/config/`
  - labels.config.ts (UI labels for enums)
  - colors.config.ts (color schemes and gradients)
  - constants.config.ts (application constants)

**Added in Cortez44 (DevOps Refactoring):**
- ✅ **Security Analyzers**: `analyze-security.py` (494 lines) → 6 modules in `devops/security-audit/analyzers/`
  - base.py: BaseAnalyzer class, SecurityFindings dataclass
  - zap_analyzer.py: OWASP ZAP report analysis
  - trivy_analyzer.py: Trivy vulnerability analysis
  - kubesec_analyzer.py: Kubernetes security analysis
  - trufflehog_analyzer.py: Secrets detection analysis
  - report_generator.py: OWASP Top 10 mapping, compliance reports
- ✅ **Reusable Workflows**: `ci.yml` (416 lines) → 5 reusable workflows in `.github/workflows/`
  - reusable-lint.yml: Python + Frontend linting
  - reusable-test-backend.yml: Backend tests with services
  - reusable-security.yml: Security scanning (Bandit, Trivy, TruffleHog)
  - reusable-build.yml: Docker build with Trivy scanning
  - reusable-deploy.yml: Kubernetes deployment
- ✅ **SQL Modules**: `init-database.sh` (402 lines) → 10 SQL files in `devops/kubernetes/staging/sql/`
  - 00-extensions.sql through 09-triggers.sql
  - 10-sample-data.sql (optional)
  - init-database-v2.sh: Modular version that executes SQL files
- ✅ **Docker Compose Modular**: `docker-compose.yml` (606 lines) → 5 files in `infra/docker/compose/`
  - docker-compose.base.yml: Core services (API, Frontend, PostgreSQL, Redis)
  - docker-compose.llm.yml: LLM provider configuration
  - docker-compose.debug.yml: Debug tools (pgAdmin, Redis Commander)
  - docker-compose.monitoring.yml: Prometheus + Grafana
  - docker-compose.ollama.yml: Local Ollama with GPU support
- ✅ All original files kept for backward compatibility

**Added in Cortez45 (GitHub Folder Audit - Complete):**
- ✅ **Modular CI/CD**: `ci-modular.yml` - Uses reusable workflows, reduced from 415 to ~150 lines
  - Calls: reusable-lint.yml, reusable-test-backend.yml, reusable-test-frontend.yml
  - Calls: reusable-security.yml, reusable-build.yml, reusable-deploy.yml
- ✅ **Optimized Security**: `security-modular.yml` - Removed redundant tools
  - Removed pip-audit (redundant with Safety)
  - Removed Gitleaks (redundant with TruffleHog)
  - Added job summary report
- ✅ **Issue Templates**: `.github/ISSUE_TEMPLATE/`
  - bug_report.yml: Severity dropdown, component selection, environment details
  - feature_request.yml: Priority levels, user type benefit
  - documentation.yml: Documentation improvements and corrections
  - question.yml: Questions about the project
  - config.yml: Template configuration
- ✅ **PR Template**: `.github/pull_request_template.md`
  - Code quality checklist
  - Security considerations
  - Testing requirements
  - Documentation updates
- ✅ **Dependabot**: `.github/dependabot.yml`
  - pip: Weekly Monday, minor/patch grouped
  - npm: Weekly Monday, React and build tools grouped
  - docker: Weekly Tuesday
  - github-actions: Weekly Wednesday
- ✅ **Automation Workflows**:
  - stale.yml: Auto-mark/close stale issues (60d) and PRs (30d)
  - release.yml: Automated releases on version tags (v*.*.*) with changelog
  - labeler.yml: Auto-label PRs based on changed files
- ✅ **Project Configuration**:
  - CODEOWNERS: Automatic PR reviewer assignment by file path
  - SECURITY.md: Security policy and vulnerability reporting
  - FUNDING.yml: Sponsorship configuration
  - labeler.yml: PR labeling rules (backend, frontend, devops, security, etc.)
- ✅ **Documentation**: `.github/README.md` - Complete guide for .github folder

**Added in Cortez46 (Backend Modularization - Complete):**
- ✅ **Repository Extraction**: Completed extraction of 12 remaining repositories from monolithic file
  - git_repository.py: GitTraceRepository
  - institutional_repository.py: CourseReportRepository, RemediationPlanRepository, RiskAlertRepository
  - simulator_repository.py: InterviewSessionRepository, IncidentSimulationRepository, SimulatorEventRepository
  - lti_repository.py: LTIDeploymentRepository, LTISessionRepository
  - profile_repository.py: StudentProfileRepository, SubjectRepository, TraceSequenceRepository
- ✅ **Training Router**: `training.py` (1,620 lines) → `backend/api/routers/training/` package
  - `__init__.py`: Package entry point with router export
  - `schemas.py`: Pydantic models (EjercicioInfo, LeccionInfo, LenguajeInfo, etc.)
  - `session_storage.py`: Redis/memory session management
  - `helpers.py`: Utility functions and constants
  - `endpoints.py`: API route handlers
- ✅ **Simulators Router**: `simulators.py` (1,589 lines) → `backend/api/routers/simulators/` package
  - `core.py`: List, interact, get_simulator_info + sub-router mounting
  - `interview.py`: IT-IA Technical Interview endpoints (start, respond, complete, get)
  - `incident.py`: IR-IA Incident Response endpoints (start, diagnose, resolve, get)
  - `sprint6.py`: SM-IA Daily Standup, CX-IA Client, DSO-IA Security Audit
- ✅ **Custom Exceptions**: 12 new exception classes in `exceptions.py`
  - UserNotFoundError, UserInactiveError, RoleRequiredError, InvalidTokenError
  - ReportNotFoundError, RiskAlertNotFoundError, SimulationNotFoundError
  - ValidationError, ExportError, LLMServiceError, SubjectNotFoundError, EvaluationNotFoundError
- ✅ **HTTPException Migration**: 9 instances migrated to custom exceptions in sessions.py
- ✅ **Import Fixes**: time_utils → backend.core.constants, ExerciseRubricLevelDB → RubricLevelDB
- ✅ **Tutor Modes Strategy Pattern**: `tutor.py` modes → `backend/agents/tutor_modes/` package (1,554 lines)
  - `base.py`: TutorModeStrategy ABC, TutorModeContext, TutorResponse dataclasses
  - `socratic.py`: SocraticStrategy - Socratic questioning mode
  - `explicative.py`: ExplicativeStrategy - Conceptual explanation mode
  - `guided.py`: GuidedStrategy - Graduated hints with scaffolding (4 levels)
  - `metacognitive.py`: MetacognitiveStrategy + ClarificationStrategy
  - `factory.py`: TutorModeFactory - Strategy creation, caching, and legacy response_type mapping
- ✅ **Logging Patterns**: 13 f-string logs converted to lazy formatting in main.py
- ✅ **Legacy Files**: Original monolithic files renamed to `*_legacy.py` for reference

**Added in Cortez47 (Backend Deep Audit - Complete):**
- ✅ **Legacy File Deletion**: Removed 3 monolithic files totaling 8,544 lines
  - `backend/database/repositories.py` (5,134 lines) - DELETED, package takes precedence
  - `backend/database/models.py` (1,772 lines) - DELETED, package takes precedence
  - `backend/agents/simulators.py` (1,638 lines) - DELETED, package takes precedence
- ✅ **Import Verification**: Confirmed Python import resolution uses packages over .py files
  - `SessionDB.__module__` resolves to `backend.database.models.session`, not `models.py`
  - `SessionRepository.__module__` resolves to `backend.database.repositories.session_repository`
- ✅ **Exception Handling Audit**: Verified no swallowed exceptions (`except...: pass`) remain
- ✅ **Backward Compatibility**: All `__init__.py` files re-export classes for existing imports
- ✅ **Final Module Count**:
  - `backend/database/repositories/`: 12 modules, 24 repository classes
  - `backend/database/models/`: 14 modules, 25 model classes
  - `backend/agents/simulators/`: 9 modules, 11 simulator strategies
  - `backend/agents/tutor_modes/`: 6 modules, 5 pedagogical strategies

**Fixed in Cortez48 (Frontend Senior Audit Remediation):**
- ✅ **FE-CRIT-001**: Demo credentials now conditional to `import.meta.env.DEV` (`LoginPage.tsx:8-10`)
- ✅ **FE-CRIT-002**: Created `ErrorBoundaryWithNavigation` wrapper using `useNavigate()` hook (`ErrorBoundary.tsx`)
  - App.tsx updated to use `ErrorBoundaryWithNavigation` for all protected routes
- ✅ **FE-CRIT-003**: Added AbortController with cleanup to `loadAnalytics` function (`GitAnalytics.tsx:71-105`)
- ✅ **FE-HIGH-001**: Replaced 28 `React.FC` patterns with function components across 18 files:
  - GitAnalytics.tsx (3), ProcessEvaluator.tsx (1), RiskAnalyzer.tsx (2), Dashboard.tsx (3)
  - TraceabilityViewer.tsx (2), TraceabilityDisplay.tsx (2), MainLayout.tsx (1), TutorChat.tsx (1)
  - ChatMessage.tsx (3), LoadingSpinner.tsx (3), ErrorAlert.tsx (3), ExerciseWorkspace.tsx (1)
  - ExercisesPage.tsx (1), ExercisesPageNew.tsx (1), TrainingPage.tsx (1), CodeEditor.tsx (1)
  - EvaluationResultView.tsx (1), SimulatorsHub.tsx (1)
- ✅ **FE-HIGH-002**: Fixed critical `key={index}` patterns:
  - `GitAnalytics.tsx`: Contributors now use `key={contributor.email}`, trends use `key={trend.date}`
- ✅ **FE-HIGH-005**: Verified useEffect cleanup patterns - all hooks use `isMountedRef` pattern

**Implemented in Cortez50 (Digital Trainer Integration):**
- ✅ **TrainingGateway** (`backend/core/training_gateway.py` - ~500 lines)
  - Central orchestrator for Digital Trainer + Agent integration
  - Methods: `process_session_start`, `process_code_submission`, `process_hint_request`, `process_reflection`, `get_session_process_analysis`
  - Configurable via `TrainingGatewayConfig` dataclass
- ✅ **TrainingTraceCollector** (`backend/core/training_traceability.py` - ~450 lines)
  - N4 cognitive trace capture using inference (Strategy A)
  - Cognitive states: INICIO, EXPLORACION, IMPLEMENTACION, DEPURACION, CAMBIO_ESTRATEGIA, VALIDACION, ESTANCAMIENTO, REFLEXION
  - Methods: `trace_code_attempt`, `trace_hint_request`, `trace_reflection`, `get_process_analysis`
- ✅ **TrainingRiskMonitor** (`backend/core/training_risk_monitor.py` - ~400 lines)
  - Real-time risk detection: COPY_PASTE, FRUSTRATION, HINT_DEPENDENCY, RAPID_SUBMISSION
  - Methods: `analyze_attempt`, `record_hint_request`, `get_session_summary`
- ✅ **TrainingHintsStrategy** (`backend/agents/tutor_modes/training_hints.py` - ~600 lines)
  - Extends `GuidedStrategy` for exercise-specific contextual hints
  - 4 help levels: MINIMO (Socratic), BAJO (conceptual), MEDIO (pseudocode), ALTO (strategy)
  - Builds "implicit prompts" from exercise context + attempt history
- ✅ **Training Hints Prompt** (`backend/prompts/training_hints_prompt.md`)
  - LLM prompt template with level-specific instructions
  - Error connection patterns, cognitive state adaptation
- ✅ **Extended Schemas** (`backend/api/routers/training/schemas.py`)
  - V2 schemas: `SolicitarPistaV2Request`, `PistaV2Response`, `ReflexionRequest`, `ProcesoAnalisis`
  - Enums: `CognitiveStateEnum`, `HelpLevelEnum`, `RiskTypeEnum`, `RiskSeverityEnum`
- ✅ **Integration Endpoints** (`backend/api/routers/training/integration_endpoints.py`)
  - `POST /pista/v2`: T-IA-Cog contextual hints
  - `POST /reflexion`: Post-exercise reflection capture
  - `GET /sesion/{id}/proceso`: Process analysis with metrics
  - `POST /submit/v2`: Extended submission with traceability
- ✅ **Feature Flags** (`backend/api/config.py`, `.env.example`)
  - `TRAINING_USE_TUTOR_HINTS`, `TRAINING_N4_TRACING`, `TRAINING_RISK_MONITOR`
  - All default to `false` for gradual rollout

**Fixed in Cortez51 (Backend Deep Audit):**
- ✅ **5 Critical Silenced Exceptions**:
  - `session.py:38-39`: Removed unnecessary try-catch around `str()` call
  - `interaction.py:149-152`: Specific exceptions `(ValueError, base64.binascii.Error)` for base64 decode
  - `exercises.py:190-193`: Added `logger.warning()` for invalid unit format
  - `git_analytics.py:218-224`: Added `logger.debug()` for unparseable git stat lines
  - `risk_analysis.py:166-170`: Removed redundant `pass` after logging
- ✅ **HTTPException → Custom Exceptions Migration**:
  - `auth_new.py`: 12 instances → `AuthenticationError`, `ValidationError`, `UserInactiveError`, `UserNotFoundError`, `InvalidTokenError`, `DatabaseOperationError`
  - `training/endpoints.py`: 11 instances → `SessionNotFoundError`, `AuthorizationError`, `ValidationError`, `DatabaseOperationError`, `ExerciseNotFoundError`
- ✅ **Unused Imports Cleaned**:
  - `reports.py`: Removed `Response`, `func`
  - `teacher_tools.py`: Removed `func`, `PaginationParams`
  - `activities.py`: Removed `func`, `select`
- ✅ **TODO Resolved** (`exercises.py:54-93, 210-268`):
  - Implemented `get_optional_current_user()` for optional authentication
  - Implemented `get_completed_exercise_ids()` to query user's completed exercises
  - Updated `/json/list` endpoint to return `is_completed=true` for completed exercises

**Implemented in Cortez55 (Frontend Digital Trainer V2 Integration):**
- ✅ **training.service.ts** - Refactored with V2 support (~480 lines)
  - 4 enums: `CognitiveStateEnum`, `HelpLevelEnum`, `RiskTypeEnum`, `RiskSeverityEnum`
  - 12 V2 types: `PistaV2Response`, `ReflexionRequest`, `ProcesoAnalisis`, `RiskFlag`, etc.
  - 5 V2 endpoint methods: `solicitarPistaV2()`, `capturarReflexion()`, `obtenerProcesoAnalisis()`, `submitEjercicioV2()`, `obtenerEstadoSesion()`
- ✅ **useTrainingSession hook** - Extended with V2 support (~515 lines)
  - New `useV2` parameter to enable N4 traceability endpoints
  - Copy-paste detection: tracks code length changes > 50 chars
  - Timing tracking: `lastSubmitTimeRef` for time between submissions
  - V2 state: `currentHintV2`, `cognitiveState`, `activeRisks`, `lastTraceId`, `procesoAnalisis`
  - V2 actions: `requestHintV2()`, `submitReflexion()`, `loadProcesoAnalisis()`, `openReflexionModal()`
- ✅ **ReflexionModal.tsx** (~220 lines)
  - Post-exercise reflection capture with 3 required fields + 2 optional
  - Success display with dimension cognitiva and XP bonus
  - Validation: minimum 10 characters per required field
- ✅ **RiskIndicator.tsx** (~120 lines)
  - Active risks display with severity colors and icons
  - `RiskBadge` compact version for header/sidebar
  - Sorted by severity (critical → low)
- ✅ **CognitiveStateDisplay.tsx** (~90 lines)
  - Inferred cognitive state visualization with icons
  - `CognitiveStateBadge` compact version
  - 9 states with unique colors and descriptions
- ✅ **HintV2Display.tsx** (~130 lines)
  - Contextual hints with help level indicator (4 levels)
  - Progress bar for hint usage (1-4)
  - Follow-up question display
  - Reflection prompt button when `requiere_reflexion=true`
- ✅ **Exports updated**:
  - `components/index.ts`: Exports 4 new components
  - `api/index.ts`: Exports V2 types and enums

**Implemented in Cortez56 (Backend V1 Legacy Endpoints):**
- ✅ **3 New Training Endpoints** (`backend/api/routers/training/endpoints.py`):
  - `POST /training/submit-ejercicio`: V1 legacy code submission
    - Validates session and exercise
    - Runs tests using CodeEvaluator
    - Returns test results, next exercise, or final results
  - `POST /training/corregir-ia`: AI-assisted code correction
    - Uses LLM for pedagogical analysis
    - Returns analysis and suggestions (max 4)
    - Fallback if LLM unavailable
  - `GET /training/sesion/{id}/estado`: Session state with N4 fields
    - Returns exercise, progress, and N4 traceability info
    - Fields: `cognitive_state`, `ai_dependency`, `current_risk_level`
- ✅ **FIX cognitive_path.py**: Applied `_ensure_aware()` to all timestamps
  - Line 113: Transition timestamps
  - Lines 130-131: Phase start_time/end_time
  - Line 198: AI dependency evolution timestamps
  - Lines 225-226: Session start/end times
- ✅ **FIX endpoints.py:272**: Corrected `unit=` → `unit_number=` parameter

**Implemented in Cortez56 (Frontend Integration):**
- ✅ **training.service.ts** - Updated types for V1 endpoints:
  - `SubmitEjercicioResponse`: Changed from nested `resultado` to flat structure (`correcto`, `tests_pasados`, `tests_totales`, `mensaje`)
  - `CorreccionIAResponse`: Added `porcentaje`, `aprobado`, `tiempo_usado_min`, `resultados_detalle`
  - `obtenerEstadoSesion()`: Now returns `SesionEntrenamientoExtendida` with N4 fields
- ✅ **useTrainingSession hook** - Extended with Cortez56 features:
  - New state: `correccionIA`, `loadingCorreccion`, `showCorreccionModal`
  - New actions: `requestCorreccionIA()`, `openCorreccionModal()`, `closeCorreccionModal()`, `refreshSessionState()`
  - Fixed V1 submit response handling (flat structure vs nested)
- ✅ **CorreccionIADisplay.tsx** (~220 lines) - New component:
  - `CorreccionIADisplay`: Full AI feedback display (analysis, suggestions, test results)
  - `CorreccionIABadge`: Compact inline version with percentage
  - `CorreccionIAModal`: Modal wrapper for full display
- ✅ **Exports updated**: `components/index.ts` exports new CorreccionIA components

**Cleaned in Cortez57 (Frontend Obsolete Code Audit):**
- ✅ **Orphan file deleted**: `pages/ExerciseDetailPage.tsx` (347 lines) - no route, superseded by features/training/
- ✅ **User type consolidated**: `auth.service.ts` now imports `User` from `@/types` instead of local definition
- ✅ **SimulatorStatus added**: New type in `types/domain/enums.ts`, imported by `simulators.service.ts`
- ✅ **TokenResponse inlined**: Removed duplicate interface, uses inline type in `refreshToken()`
- ✅ **Internal services documented**: `admin.service.ts` and `institutionalRisks.service.ts` marked `@internal`

**Cleaned in Cortez58 (Backend Obsolete Code Audit):**
- ✅ **3 orphan core modules deleted** (964 lines total):
  - `core/response_generator.py` (246 lines) - never imported, God Class extraction artifact
  - `core/trace_manager.py` (314 lines) - never imported, superseded by training_traceability.py
  - `core/risk_analyzer.py` (404 lines) - superseded by agents/risk_analyst.py
- ✅ **Example file moved**: `background_session_examples.py` → `docs/examples/`
- ✅ **HTTPException imports cleaned** from 5 routers:
  - exercises.py, activities.py, sessions.py, events.py, cognitive_path.py
- ✅ **Database error handling added** (4 locations):
  - `exercises.py`: submit endpoint db.commit()
  - `cognitive_status.py`: update endpoint db.commit()
  - `events.py`: create_event and create_batch_events db.commit()
  - Pattern: try/except with db.rollback() and DatabaseOperationError

**Implemented in Cortez63 (N4 Traceability for Teachers):**
- ✅ **Backend** - 3 new endpoints in `backend/api/routers/teacher_tools.py`:
  - `GET /teacher/students/{student_id}/traceability` - Student N4 traces with:
    - Pagination support (limit, offset)
    - Activity filter
    - Cognitive state distribution, trace level distribution, interaction types
    - Average AI involvement calculation
  - `GET /teacher/students/{student_id}/cognitive-path` - Cognitive evolution:
    - State transitions with timestamps
    - Time spent in each state
    - Auto-generated insights (stagnation alerts, patterns)
  - `GET /teacher/traceability/summary` - Global metrics:
    - AI dependency classification (high >70%, medium 40-70%, low <40%)
    - Cognitive state distribution across all students
    - Traceability alerts (high dependency, frequent stagnation)
- ✅ **Frontend Service** - `frontEnd/src/services/api/teacherTraceability.service.ts`:
  - TypeScript types: `TraceLevel`, `CognitiveState`, `TraceData`, `TraceabilitySummary`
  - Types: `AIDependencyDistribution`, `TraceabilityAlert`, pagination interfaces
  - Methods: `getStudentTraceability()`, `getStudentCognitivePath()`, `getTraceabilitySummary()`
- ✅ **StudentTraceabilityViewer** - `frontEnd/src/components/teacher/StudentTraceabilityViewer.tsx`:
  - 3-tab interface: Overview, Traces, Cognitive Path
  - Overview: Stats grid, cognitive state chart, trace level distribution
  - Traces: Paginated list with expandable details
  - Cognitive Path: Timeline visualization with insights
- ✅ **StudentMonitoringPage** - New "Trazabilidad N4" tab:
  - Global stats panel (students, traces, AI dependency %)
  - Cognitive state distribution chart
  - Traceability alerts with severity colors
  - Students grouped by AI dependency level
  - Expandable student details with full TraceabilityViewer
- ✅ **TeacherDashboardPage** - Enhanced with traceability:
  - New "Trazas N4" stats card with trend indicator
  - New "Trazabilidad N4" quick action
  - "Trazabilidad Cognitiva N4" section with charts:
    - Cognitive state distribution (horizontal bars)
    - AI dependency distribution (high/medium/low)
- ✅ **Exports updated**: `services/api/index.ts` exports new service and types

## Troubleshooting

### Common Windows vs Linux/Mac Issues

**Path separators:**
```bash
# Windows uses backslashes, Linux/Mac use forward slashes
# In code, always use forward slashes or path.join()
import os
path = os.path.join("backend", "api", "routers")  # CORRECT
path = "backend\\api\\routers"  # Windows-only, INCORRECT
```

**Line endings (CRLF vs LF):**
```bash
# Configure git to handle line endings
git config --global core.autocrlf true   # Windows
git config --global core.autocrlf input  # Linux/Mac
```

**Docker on Windows:**
- Use WSL2 backend for Docker Desktop
- If containers fail to start, check that WSL2 is properly configured
- Volume mounts may need adjustment: `/c/users/...` instead of `C:\Users\...`

**Python encoding issues (cp1252):**
```python
# Windows console may have encoding issues with emojis/unicode
# FIX Cortez54: Don't use emojis in log messages
logger.info("Session started")  # CORRECT
logger.info("✅ Session started")  # May fail on Windows cp1252
```

**PowerShell vs Bash:**
```powershell
# PowerShell equivalent commands
Invoke-RestMethod http://localhost:8000/api/v1/health  # curl equivalent
$env:JWT_SECRET_KEY = "your-secret"  # export equivalent
```

### Common Development Errors

**"Module not found" in Python:**
```bash
# Always run from activia1-main/ directory
cd activia1-main
python -m backend  # CORRECT
python backend/api/main.py  # May fail due to import paths
```

**"Cannot find module" in TypeScript:**
```bash
# Ensure path aliases are configured in tsconfig.json
# Use @/ prefix for src imports
import { authService } from '@/services/api';  # CORRECT
import { authService } from '../../services/api';  # INCORRECT (fragile)
```

**PostgreSQL connection refused:**
```bash
# Check if PostgreSQL is running
docker-compose ps  # Check container status
docker-compose logs db  # Check PostgreSQL logs

# Common fix: wait for PostgreSQL to be ready
docker-compose up -d db && sleep 5 && docker-compose up -d api
```

**Redis connection issues:**
```bash
# Check Redis is accessible
docker-compose exec redis redis-cli ping  # Should return PONG

# Check Redis password is set
echo $REDIS_PASSWORD  # Must match .env
```

**LLM provider timeout:**
```python
# Ollama may need more time for first response (model loading)
# Increase timeout in .env
OLLAMA_TIMEOUT=120  # Default is 60 seconds

# Check Ollama is running and model is available
curl http://localhost:11434/api/tags  # List available models
```

**Frontend build failures:**
```bash
# Clear cache and reinstall
cd frontEnd
rm -rf node_modules .vite dist
npm install
npm run build
```

**TypeScript type errors after changes:**
```bash
# Run type check to see all errors
npm run type-check

# Common fix: regenerate types from API
# Check that frontend types match backend schemas
```