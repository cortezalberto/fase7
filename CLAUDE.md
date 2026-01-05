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

**Last Updated**: Cortez86 - Frontend-Backend Integration Audit (January 2026)
- Audited 55+ files: 22 API services, 11 domain types, 19 pages, 3 stores
- Found 12 issues, **10 fixed** (2 documented for future sprints)
- Health Score: 8.8 -> **9.6/10** frontend
- Key fixes applied:
  - Removed 7 unused imports across components
  - Extracted `LTIContainer` context/hook to separate files for fast-refresh compatibility
  - Created `contexts/LTIContext.ts` and `hooks/useLTIContext.ts`
  - Removed debug console.log statements from auth.service.ts
  - Fixed unused function parameters with `_` prefix
- ESLint warnings: 10 -> 0

**Previous - Cortez85**: Database & ORM Exhaustive Audit (January 2026)
- Audited 34 files: 17 ORM models, 16 repositories, 1 config
- Found 7 issues, **5 fixed** (2 MEDIUM documented as design decisions)
- Health Score: **9.6/10** database layer
- New migration: `add_cortez85_fixes.py` (creates indexes, verifies deleted_at columns)

**Previous - Cortez84**: Backend Exhaustive Audit + Full Remediation (January 2026)
- Audited 88 files (~20,300 lines): 17 ORM models, 16 repositories, 35 routers, 12 AI agents
- Found 133 issues initially, **16 remediated/verified**
- Health Score: 9.5/10 -> **9.8/10** backend

**Previous - Cortez83**: Backend Exhaustive Audit (January 2026)
- Initial audit identifying 61 issues, basic remediation

**Previous - Cortez82**: Teacher-Student Traceability Compatibility (January 2026)
- Created `compatibilidad.md` with 10 traceability improvements analysis
- Added `TeacherInterventionDB` model for persistent alert acknowledgments
- Added `course_id` column to sessions for course-level filtering
- Added PostgreSQL trigger for automatic `trace_count` synchronization
- Created `CognitiveTimeline.tsx` - Visual timeline of cognitive journey
- Created `StudentCognitiveProfile.tsx` - Student self-view of cognitive metrics
- Added WebSocket endpoint `/ws/teacher/alerts` for real-time notifications
- Added export endpoints (JSON/CSV) for student and activity traceability
- Added `/students/{id}/trends` endpoint for longitudinal metrics
- Implemented `calculate_process_score()` - Process-based evaluation (autonomy 40%, diversity 20%, persistence 20%, risk avoidance 20%)

**Previous - Cortez81**: Institutional Risks Dashboard Fix (January 2026)
- Fixed InstitutionalRisksPage not loading - backend now returns correct `RiskDashboard` structure
- Updated `get_dashboard_metrics()` to return: `summary`, `alerts_by_severity`, `alerts_by_type`, `recent_alerts`, `trends`
- Fixed `/alerts` endpoint to return fields matching frontend `RiskAlert` interface
- Made `acknowledgeAlert` work without body (gets teacher_id from current_user)
- Added explicit "Subir Archivos" button to FileUploader component
- Added Edit button to units in ContentManagementPage

**Previous - Cortez80**: Unit Count Fix + Role Detection
- Fixed role detection: `current_user.get("roles")` is a LIST, not singular `role` string
- Teachers/instructors/admins see all units (including unpublished)

**Previous - Cortez79**: Materias CRUD Fix + Database Migrations
- Fixed `UnidadDB.deleted_at` attribute error causing materias listing to fail
- Added `deleted_at` column to PostgreSQL `unidades`, `apuntes`, `archivos_adjuntos` tables
- Changed `JSONB` to `JSONBCompatible` in `unidad.py` for SQLite/PostgreSQL compatibility
- Fixed MateriasManagementPage form styling for dark theme (CSS variables)
- Added TEACHER role to UserRole enum
- Executed 25 pending database migrations (N4 dimensions, Moodle fields, soft delete columns)

**Previous - Cortez78**: Documentation Cleanup (January 2026)
- Removed 31 obsolete/duplicate .md files (146 → 115)

**Previous - Cortez77**: Frontend Exhaustive Audit
- 144 files analyzed, 28 issues found, 14 fixed
- Health Score: 8.2 → 9.3/10

**Health Score**: 9.6/10 frontend, 9.8/10 backend, 9.6/10 database (after 86 audits)

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
python -m backend.database.migrations.add_user_academic_context
python -m backend.database.migrations.fix_subjects_basemodel
python -m backend.database.migrations.add_traceability_improvements  # Cortez82
python -m backend.database.migrations.add_cortez85_fixes  # Cortez85 - indexes + deleted_at

# Manual PostgreSQL column addition (when model changes)
# If you add a new column to a model, also add it to PostgreSQL:
# Connect via: postgresql://ai_native:dev_postgres_password_12345@localhost:5433/ai_native
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://ai_native:dev_postgres_password_12345@localhost:5433/ai_native')
cursor = conn.cursor()
cursor.execute('ALTER TABLE table_name ADD COLUMN column_name TYPE')
conn.commit()
conn.close()
"
```

### Backend Testing
```bash
pytest tests/ -v --cov=backend          # All tests (70% min coverage required)
pytest tests/ -v -m "unit"              # Unit tests only
pytest tests/ -v -m "integration"       # Integration tests
pytest tests/test_agents.py -v          # Single file
pytest tests/test_agents.py::test_tutor_mode -v  # Single test function
pytest -k "test_tutor" -v               # Pattern matching
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

### Windows PowerShell (without Make)
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
docker-compose up -d
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
| T-IA-Cog | `tutor.py` + `tutor_modes/` | Cognitive Tutor - Strategy Pattern (4 modes: Socratic, Explicative, Guided, Metacognitive) |
| E-IA-Proc | `evaluator.py` | Process Evaluator |
| S-IA-X | `simulators/` | Professional Role Simulators - Strategy Pattern (11 roles) |
| AR-IA | `risk_analyst.py` | Risk Analyst (5 dimensions) |
| GOV-IA | `governance.py` | Governance & Delegation |
| TC-N4 | `traceability.py` | N4-level Traceability |

### Teacher Management (`/teacher/*` routes)

**Layout**: `TeacherLayout.tsx` - Dedicated layout for teacher routes with purple/violet gradient branding.

| Page | File | Purpose |
|------|------|---------|
| TeacherDashboardPage | `pages/TeacherDashboardPage.tsx` | Dashboard with alerts, analytics |
| StudentMonitoringPage | `pages/StudentMonitoringPage.tsx` | Real-time monitoring, 30s auto-refresh |
| ActivityManagementPage | `pages/ActivityManagementPage.tsx` | CRUD + PolicyConfig + Maestro-Detalle |
| ContentManagementPage | `pages/ContentManagementPage.tsx` | 3-level Maestro-Detalle (Materia → Unidad → Contenido) |
| ReportsPage | `pages/ReportsPage.tsx` | Cohort reports, export (JSON/PDF/XLSX) |
| InstitutionalRisksPage | `pages/InstitutionalRisksPage.tsx` | Risk management, remediation plans |

### Key Files
| Component | Path |
|-----------|------|
| AI Gateway (orchestrator) | `backend/core/ai_gateway.py` |
| Response Generators | `backend/core/gateway/response_generators.py` |
| Trace Coordinator | `backend/core/gateway/trace_coordinator.py` |
| Risk Coordinator | `backend/core/gateway/risk_coordinator.py` |
| Cognitive Engine (CRPE) | `backend/core/cognitive_engine.py` |
| LLM Factory | `backend/llm/factory.py` |
| ORM Models | `backend/database/models/` (15 domain files) |
| Repositories | `backend/database/repositories/` (13 domain files) |
| Teacher Interventions | `backend/database/models/teacher_intervention.py` |
| Custom Exceptions | `backend/api/exceptions.py` (50+ exception classes) |
| API Main | `backend/api/main.py` |
| Frontend API Services | `frontEnd/src/services/api/` (22 services) |
| Frontend Types | `frontEnd/src/types/domain/` (11 domain files) |
| Frontend Contexts | `frontEnd/src/contexts/` (AuthContext, LTIContext) |
| Frontend Hooks | `frontEnd/src/hooks/` (useLTIContext) |
| Frontend Stores | `frontEnd/src/stores/` (uiStore, sessionStore) |
| Prompt Security Utils | `backend/utils/prompt_security.py` |

### Cognitive State & Trace Types (Critical for N4 Traceability)

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

### React 19 Patterns
```typescript
// DON'T use React.FC (deprecated in React 19)
const MyComponent: React.FC<Props> = ({ prop }) => { ... };  // INCORRECT

// DO use function component with typed props
const MyComponent = ({ prop }: Props) => { ... };  // CORRECT

// Use React 19's use() hook for context - NOT useContext()
const context = use(MyContext);  // React 19 pattern

// Use Zustand for UI state (stores in src/stores/)
import { useUIStore, useSessionStore } from '@/stores';
```

### Frontend Anti-Patterns (Cortez77)
```typescript
// Division by zero - always guard Math.max with empty arrays
const maxCount = Math.max(...Object.values(distribution), 1);  // Add ,1

// parseInt always needs radix
parseInt(e.target.value, 10)  // CORRECT
parseInt(e.target.value)       // INCORRECT

// Abort signal verification before setState
const loadData = useCallback(async (signal?: AbortSignal) => {
  const data = await api.get('/data', { signal });
  if (signal?.aborted) return;  // Check before setState
  setData(data);
}, []);

// useMemo for arrays recreated each render
const views = useMemo(() => [
  { id: 'tab1', label: 'Tab 1', count: data?.count },
], [data?.count]);

// Optional interface fields with null checks
interface Alert { suggestions?: string[]; }  // Optional
{alert.suggestions && alert.suggestions.length > 0 && ...}

// DEV-only logging
if (import.meta.env.DEV) console.log('Debug:', data);

// Keyboard accessibility
onKeyDown={(e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();  // Prevent scroll on space
    handleAction();
  }
}}

// CSS variables for dark/light theme compatibility (Cortez79)
// Use these instead of hardcoded colors like bg-white
className="bg-[var(--bg-card)] text-[var(--text-primary)]"
className="bg-[var(--bg-tertiary)] border-[var(--border-color)]"
className="text-[var(--text-secondary)] placeholder:text-[var(--text-muted)]"

// Fast Refresh Compatibility (Cortez86)
// React contexts must be in separate files from components
// CORRECT structure:
//   contexts/LTIContext.ts     <- Context + types
//   hooks/useLTIContext.ts     <- Hook that uses the context
//   components/LTIContainer.tsx <- Component that provides context
// INCORRECT - context in same file as component triggers warning
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

### Database Pessimistic Locking
```python
# Use SELECT FOR UPDATE for concurrent updates
from sqlalchemy import select

def update_with_lock(self, entity_id: str, **kwargs):
    try:
        stmt = select(EntityDB).where(EntityDB.id == entity_id).with_for_update()
        entity = self.db.execute(stmt).scalar_one_or_none()
        if entity:
            self.db.commit()
        return entity
    except Exception as e:
        self.db.rollback()
        raise
```

### Student Code Execution Security
```python
# NEVER use exec/eval directly in server process
# ALWAYS use the sandbox utility
from backend.utils.sandbox import execute_python_code

stdout, stderr, exec_time = execute_python_code(
    code=student_code,
    test_input="",
    timeout_seconds=30
)
```

### Prompt Injection Detection
```python
# ALWAYS use centralized prompt security utility
from backend.utils.prompt_security import detect_prompt_injection

if detect_prompt_injection(user_prompt):
    return "Lo siento, no puedo procesar ese tipo de solicitud."
```

### Custom Exceptions
```python
# Use custom exceptions for consistent error handling (50+ classes)
from ..exceptions import SessionNotFoundError, ValidationError

if not session:
    raise SessionNotFoundError(session_id)

# INCORRECT - direct HTTPException
raise HTTPException(status_code=404, detail="...")  # DON'T
```

### get_current_user Returns Dict with roles LIST
```python
# CORRECT - access user_id from dict
async def my_endpoint(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")  # NOT current_user.id

# CRITICAL: roles is a LIST, not a singular role string
# get_current_user returns: {"user_id": ..., "roles": ["teacher", "student"], ...}
user_roles = current_user.get("roles", [])  # CORRECT - returns list
es_profesor = "teacher" in user_roles or "instructor" in user_roles or "admin" in user_roles

# INCORRECT - "role" (singular) doesn't exist, returns None
es_profesor = current_user.get("role") == "teacher"  # WRONG - always False
```

### Process Score Calculation (Cortez82)
```python
# Process-based evaluation formula implemented in teacher_tools.py
# Components:
#   - Autonomy (40%): 1 - avg_ai_dependency
#   - Diversity (20%): unique_states / 8 possible states
#   - Persistence (20%): completed / total sessions
#   - Risk Avoidance (20%): 1 - (critical_risks / total_risks)

def calculate_process_score(sessions, traces_by_session, risks) -> dict:
    return {
        "overall_score": 0-10 scale,
        "components": { "autonomy", "diversity", "persistence", "risk_avoidance" },
        "interpretation": "Excelente" | "Bueno" | "Aceptable" | "Necesita mejora"
    }
```

### Datetime Always Timezone-Aware
```python
from datetime import datetime, timezone

# NEVER use datetime.utcnow() - deprecated
timestamp = datetime.now(timezone.utc)  # CORRECT
```

### JSONBCompatible for Database Portability
```python
# Use JSONBCompatible for JSON columns (supports both PostgreSQL and SQLite)
from .base import JSONBCompatible

# CORRECT - works with both databases
objetivos: Mapped[List[str]] = mapped_column(JSONBCompatible, default=list)

# INCORRECT - PostgreSQL only, fails on SQLite
from sqlalchemy.dialects.postgresql import JSONB
objetivos: Mapped[List[str]] = mapped_column(JSONB, default=list)
```

### Soft Delete Pattern
```python
# Models use deleted_at column for soft deletes
# Repository queries must filter by deleted_at IS NULL
from sqlalchemy import select

def get_active(self, materia_code: str):
    stmt = select(UnidadDB).where(
        UnidadDB.materia_code == materia_code,
        UnidadDB.deleted_at.is_(None)  # CRITICAL: Filter soft-deleted
    )
    return list(self.db.execute(stmt).scalars().all())

# Soft delete instead of hard delete
def soft_delete(self, entity_id: str):
    entity = self.get_by_id(entity_id)
    entity.deleted_at = datetime.now(timezone.utc)
    self.db.commit()
```

### Database Commit Error Handling
```python
try:
    db.add(entity)
    db.commit()
    db.refresh(entity)
except Exception as e:
    db.rollback()
    raise DatabaseOperationError(operation="create_entity", details=str(e))
```

### SQLAlchemy Boolean Comparisons (Cortez84)
```python
# CORRECT - Use .is_(True) for boolean columns
query.filter(ModelDB.is_active.is_(True))
query.filter(ModelDB.deleted_at.is_(None))

# INCORRECT - Generates SQLAlchemy warning
query.filter(ModelDB.is_active == True)  # DON'T
```

### Magic Bytes File Validation (Cortez84)
```python
# File uploads must validate magic bytes, not just MIME type
# Implemented in backend/services/file_storage.py
MAGIC_BYTES = {
    "application/pdf": [b"%PDF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/gif": [b"GIF87a", b"GIF89a"],
}
```

### Centralized Configuration (Cortez84)
```python
# LLM timeout is centralized - don't hardcode
from backend.api.config import LLM_TIMEOUT_SECONDS  # 30.0 default

# Override via environment:
# LLM_TIMEOUT_SECONDS=60.0
```

### Bulk Updates Instead of Loops (Cortez84)
```python
# CORRECT - Single UPDATE with CASE WHEN
from sqlalchemy import case, update

orden_mapping = {id: idx for idx, id in enumerate(orden_ids, start=1)}
stmt = (
    update(ApuntesDB)
    .where(ApuntesDB.id.in_(orden_ids))
    .values(orden=case(orden_mapping, value=ApuntesDB.id))
)
db.execute(stmt)
db.commit()

# INCORRECT - N queries in a loop
for idx, id in enumerate(orden_ids):
    db.query(ApuntesDB).filter_by(id=id).update({"orden": idx})  # DON'T
```

### Windows Encoding Issues
```python
# Don't use emojis in log messages on Windows
logger.info("Session started")  # CORRECT
logger.info("✅ Session started")  # May fail on Windows cp1252
```

### Frontend/Backend Interface Alignment
```python
# CRITICAL: Backend responses must match frontend TypeScript interfaces
# Example: RiskDashboard interface expects specific structure

# Frontend expects (institutionalRisks.service.ts):
# {
#   summary: { total_alerts, pending_alerts, critical_alerts, resolved_this_week },
#   alerts_by_severity: Record<AlertSeverity, number>,
#   alerts_by_type: Record<string, number>,
#   recent_alerts: RiskAlert[],
#   trends: { date, alerts_created, alerts_resolved }[]
# }

# Backend MUST return this exact structure in get_dashboard_metrics()
# The BaseApiService extracts response.data.data from APIResponse wrapper

# RiskAlert interface field mappings:
# Backend field      -> Frontend field
# a.id              -> id (NOT alert_id)
# a.student_id      -> affected_students (as array)
# a.activity_id     -> affected_activities (as array)
# a.detected_at     -> created_at
# a.evidence        -> evidence (default to [])
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

**Storage:**
- `UPLOAD_DIR=uploads` - Directory for uploaded files
- `MAX_FILE_SIZE_MB=50` - Maximum file size limit

**Test Credentials** (created by `python -m backend.scripts.create_test_users`):
- `teacher@activia.com` / `Teacher1234` - Teacher role (can see unpublished units)
- `student@activia.com` / `Student1234` - Student role
- `admin@activia.com` / `admin123` - Admin role
- `demo@activia.com` / `demo123` - Demo student

## Documentation

**Entry Points:**
- `backend/README.md` - Backend architecture (900+ lines)
- `frontEnd/README.md` - Frontend architecture (1,350+ lines)
- `backend/agents/README.md` - AI agents documentation

**Architecture Proposals:**
- `backend/ImplementacionAgentes.md` - Multi-Agent Active-IA technical proposal
- `stack.md` - Technology Stack Recommendation (pgvector, embeddings, LLM strategy)
- `docs/metodologia.md` - Academic Content Management Implementation Guide

## Troubleshooting

### Common Windows vs Linux/Mac Issues

```bash
# Path separators - always use forward slashes or path.join()
import os
path = os.path.join("backend", "api", "routers")  # CORRECT

# Line endings
git config --global core.autocrlf true   # Windows
git config --global core.autocrlf input  # Linux/Mac
```

### Common Development Errors

```bash
# "Module not found" - always run from activia1-main/
cd activia1-main
python -m backend  # CORRECT

# TypeScript path aliases
import { authService } from '@/services/api';  # Use @/ prefix

# PostgreSQL connection refused
docker-compose up -d db && sleep 5 && docker-compose up -d api

# Frontend build failures
cd frontEnd && rm -rf node_modules .vite dist && npm install && npm run build
```

## Audit History Summary

86 audits have been performed. Key improvements:
- **Cortez86**: Frontend-Backend Integration Audit (12 issues, 10 fixed, health 8.8→9.6)
  - Removed unused imports, extracted LTI context/hook for fast-refresh
  - Created `contexts/LTIContext.ts` and `hooks/useLTIContext.ts`
  - ESLint warnings: 10 → 0
- **Cortez85**: Database & ORM Exhaustive Audit (7 issues, 5 fixed, health 9.6)
  - Added missing indexes on exercises.deleted_at
  - Fixed 24 boolean comparisons to use `.is_(True/False/None)` pattern
  - Added try/except to EvaluationRepository.create()
  - Created migration for PostgreSQL index creation
- **Cortez84**: Backend Exhaustive Audit + Full Remediation (133→110 issues, health 9.5→9.8)
  - 11 fixes applied: current_user.get(), timeout centralization, magic bytes, bulk updates
  - 5 pre-existing protections verified: CircuitBreaker, with_for_update, _max_background_tasks
- **Cortez83**: Backend Exhaustive Audit (61 issues found, remediation plan created)
- **Cortez82**: Teacher-Student Traceability Compatibility (WebSockets, process score, export endpoints)
- **Cortez81**: Institutional Risks Dashboard fix (frontend/backend structure alignment)
- **Cortez80**: Unit count fix (roles LIST detection, dynamic unit count from DB)
- **Cortez79**: Materias CRUD fix (deleted_at column, JSONBCompatible, dark theme styling)
- **Cortez78**: Documentation cleanup (31 obsolete files removed, 146→115)
- **Cortez77**: Frontend exhaustive audit (14/28 issues fixed, health 8.2→9.3)
- **Cortez76**: Entrenador Digital removal
- **Cortez73-75**: Backend security remediation (prompt injection, circuit breaker, locking)
- **Cortez72**: Academic Content Management System (Materias, Unidades, Apuntes)
- **Cortez70**: Concurrency & Security (thread locks, DB locking, sandbox)
- **Cortez66**: Architecture (coordinator extraction, schema consolidation)
- **Cortez53**: HTTPException → custom exceptions migration
- **Cortez46-47**: Backend modularization (repositories, models, simulators packages)
- **Cortez43**: Frontend modularization (types, features, HTTP utilities)

Full audit reports in `docs/audits/`
