# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Location

The actual project is in `activia1-main/`. **All commands must run from there.**

```bash
cd activia1-main
```

## Project Overview

AI-Native MVP for teaching-learning programming with generative AI. Doctoral thesis implementing **process-based evaluation** (not product-based) with N4-level cognitive traceability.

**Stack**: Python 3.11+/FastAPI, React 19/TypeScript/Vite, PostgreSQL, Redis, Ollama/Phi-3 or Gemini for LLM.

**Key Concept**: The system evaluates HOW students solve problems (cognitive process), not just final code output. This is achieved through 7 AI agents and N4-level cognitive traceability.

**Health Score**: 9.6/10 frontend, 9.6/10 backend, 9.6/10 database (after Cortez93)

**Latest - Cortez93**: React 19 Exhaustive Audit + ALL Fixes (January 2026)
- Comprehensive React 19 patterns analysis of 153 TSX files
- Found 31 issues: 0 Critical, 5 High, 15 Medium, 11 Low
- **11 of 11 fixes implemented (100%)**:
  - Created `utils/responseHandler.ts` - Eliminates 9 `as unknown` assertions with `unwrapResponse<T>()`
  - Added Zustand DevTools middleware (`devtools` in uiStore.ts)
  - Fixed `useAsyncOperation.ts` reset callback dependency
  - Fixed `CodeEditor.tsx` key index pattern
  - Removed 5 unnecessary React default imports (React 19 JSX transform)
  - Documented AbortController limitation in useFetchSessions
  - Verified AppContext already migrated to Zustand
  - **React 19 `useActionState()` implemented in 3 forms**:
    - `LoginPage.tsx` - useActionState with isPending and formState
    - `RegisterPage.tsx` - useActionState with integrated validation
    - `CreateSessionModal.tsx` - useActionState for session creation
- TypeScript type-check: 0 errors
- Build: Successful (10.03s)
- Audit report: `docs/audits/cortez93_react19_exhaustive_audit.md`

**Cortez92**: Frontend Exhaustive Audit + All Fixes
- Created `utils/queryBuilder.ts`, `utils/retryUtil.ts`, `utils/serviceErrorHandler.ts`
- Fixed memory leaks, TypeScript types, granular Zustand selectors
- Audit report: `docs/audits/cortez92_frontend_exhaustive_audit.md`

## Commands

### Docker (Recommended)
```bash
docker-compose up -d                    # Start full stack
docker-compose logs -f api              # View API logs
docker-compose down                     # Stop services
docker-compose --profile debug up -d    # Includes pgAdmin + Redis Commander
```

### Backend
```bash
pip install -r requirements.txt
python -m backend                       # Runs uvicorn on :8000

# Migrations
python -m backend.database.migrations.add_n4_dimensions
python -m backend.database.migrations.add_traceability_improvements
python -m backend.database.migrations.add_cortez85_fixes
python -m backend.database.migrations.add_knowledge_rag

# Testing
pytest tests/ -v --cov=backend          # All tests (70% min coverage)
pytest tests/ -v -m "unit"              # Unit tests only
pytest tests/test_agents.py -v          # Single file
pytest tests/test_agents.py::test_tutor_mode -v  # Single test
pytest -k "test_tutor" -v               # Pattern matching
```

Test markers: `unit`, `integration`, `cognitive`, `agents`, `models`, `gateway`, `slow`, `asyncio`

### Frontend
```bash
cd frontEnd
npm install && npm run dev              # Dev server on :3000
npm run build                           # Production build
npm run lint                            # ESLint
npm run type-check                      # TypeScript check
npm test                                # Vitest tests
npm run e2e                             # Playwright E2E
```

## Architecture

### Request Flow
```
Client -> FastAPI Router -> AIGateway (STATELESS) -> CRPE -> Governance Agent
    -> Target Agent -> LLM Provider -> Response Generator -> TC-N4 Traceability
    -> Risk Analyzer -> Repositories (PostgreSQL) -> Response
```

### 7 AI Agents (`backend/agents/`)
| Agent | Purpose |
|-------|---------|
| T-IA-Cog (`tutor/`) | Cognitive Tutor - Strategy Pattern (4 modes: Socratic, Explicative, Guided, Metacognitive) |
| E-IA-Proc (`evaluator.py`) | Process Evaluator |
| S-IA-X (`simulators/`) | Professional Role Simulators - Strategy Pattern (11 roles) |
| AR-IA (`risk_analyst.py`) | Risk Analyst (5 dimensions) |
| GOV-IA (`governance.py`) | Governance & Delegation |
| TC-N4 (`traceability.py`) | N4-level Traceability |
| K-RAG (`knowledge_rag.py`) | Knowledge RAG - Context enrichment with pgvector |

### Key Files
| Component | Path |
|-----------|------|
| AI Gateway (orchestrator) | `backend/core/ai_gateway.py` |
| Cognitive Engine (CRPE) | `backend/core/cognitive_engine.py` |
| GenericRepository[T] | `backend/database/repositories/base.py` |
| LLMGenerationMixin | `backend/agents/base_agent.py` |
| Custom Exceptions | `backend/api/exceptions.py` (50+ classes) |
| JSON Extraction | `backend/utils/json_extraction.py` |
| Prompt Security | `backend/utils/prompt_security.py` |
| Constants | `backend/core/constants.py` |
| Document Chunker | `backend/services/document_chunker.py` |
| Typed Configs | `backend/agents/base_agent.py` (LLMConfig, RAGConfig, AgentConfig) |

### Cognitive States
```typescript
type CognitiveState =
  | 'INICIO' | 'EXPLORACION' | 'IMPLEMENTACION' | 'DEPURACION'
  | 'CAMBIO_ESTRATEGIA' | 'VALIDACION' | 'ESTANCAMIENTO' | 'REFLEXION';

type TraceLevel = 'N1' | 'N2' | 'N3' | 'N4';
// N1: Raw, N2: Preprocessed, N3: LLM processed, N4: Synthesized
```

## Critical Patterns

### AIGateway is STATELESS
All state persists to PostgreSQL via repositories. No in-memory sessions/traces/risks. Supports horizontal scaling.

### Avoid Circular Imports in core/ Modules
```python
# NEVER import from backend.api.* in backend.core.* modules
# Read env directly in core/ modules:
import os
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))

# Use TYPE_CHECKING for type hints:
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..agents.knowledge_rag import KnowledgeRAGAgent
```

### get_current_user Returns Dict with roles LIST
```python
# CRITICAL: roles is a LIST, not a singular role string
user_roles = current_user.get("roles", [])  # Returns list
es_profesor = "teacher" in user_roles or "instructor" in user_roles or "admin" in user_roles

# WRONG - "role" singular doesn't exist
es_profesor = current_user.get("role") == "teacher"  # Always False
```

### GenericRepository[T] Pattern
```python
from .base import GenericRepository

class MyRepository(GenericRepository[MyModelDB]):
    model = MyModelDB  # Required

    # Inherited: create, get_by_id, get_by_ids, get_all, update, delete, soft_delete, restore
    # Add domain-specific methods only:
    def get_by_student(self, student_id: str) -> List[MyModelDB]:
        return self.db.query(self.model).filter(self.model.student_id == student_id).all()
```

### LLMGenerationMixin for Agents
```python
from ..base_agent import LLMGenerationMixin, AgentResponseBuilder, LLMConfig, AgentConfig

class MyAgent(LLMGenerationMixin):
    def __init__(self, llm_provider, config: AgentConfig = None):
        self.llm_provider = llm_provider  # Required
        self.config = config or AgentConfig()

    async def process(self, input_data: str) -> Dict[str, Any]:
        messages = self._build_conversation_messages(system_prompt="...", user_input=input_data)
        response = await self._generate_with_timeout(messages, context_label="my_agent")
        if response is None:
            return AgentResponseBuilder.fallback(self.config.fallback_message, role="my_agent")
        return AgentResponseBuilder.success(response.content, role="my_agent")
```

### Typed Config Dataclasses (Cortez92)
```python
from backend.agents.base_agent import LLMConfig, RAGConfig, AgentConfig

# LLMConfig - validated LLM generation settings
config = LLMConfig(temperature=0.5, max_tokens=500, timeout=30.0)
# Raises ValueError if temperature not in 0.0-2.0, max_tokens < 1, timeout <= 0

# RAGConfig - validated RAG settings
rag = RAGConfig(max_documents=5, min_confidence=0.6)

# AgentConfig - base config with nested LLM and RAG
agent_config = AgentConfig(
    llm=LLMConfig(temperature=0.7),
    rag=RAGConfig(max_documents=3),
    fallback_message="Service unavailable"
)

# Backward compatible factory
config = AgentConfig.from_dict({"llm": {"temperature": 0.5}})
```

### Database Patterns
```python
# Soft delete - filter by deleted_at IS NULL
stmt = select(UnidadDB).where(UnidadDB.materia_code == code, UnidadDB.deleted_at.is_(None))

# Pessimistic locking for concurrent updates
stmt = select(EntityDB).where(EntityDB.id == entity_id).with_for_update()

# Batch loading for N+1 prevention
traces_by_session = trace_repo.get_by_session_ids(session_ids)  # CORRECT
for sid in session_ids: trace_repo.get_by_session(sid)  # WRONG - N+1

# Boolean comparisons
query.filter(ModelDB.is_active.is_(True))  # CORRECT
query.filter(ModelDB.is_active == True)     # WRONG - SQLAlchemy warning

# JSONBCompatible for PostgreSQL/SQLite portability
objetivos: Mapped[List[str]] = mapped_column(JSONBCompatible, default=list)

# Commit error handling
try:
    db.add(entity); db.commit(); db.refresh(entity)
except Exception as e:
    db.rollback()
    raise DatabaseOperationError(operation="create", details=str(e))
```

### LLM Patterns
```python
# Always use timeout
import asyncio
from backend.core.constants import LLM_TIMEOUT_SECONDS

response = await asyncio.wait_for(llm_provider.generate(messages), timeout=LLM_TIMEOUT_SECONDS)

# Use centralized JSON extraction for LLM responses
from backend.utils.json_extraction import extract_json_from_text, extract_json_with_fallback
result = extract_json_with_fallback(llm_response, {"default": "value"})

# Lazy logging (CRIT-002 fix) - use %s format, not f-strings
logger.info("Processing %s with %d items", name, count)  # CORRECT
logger.info(f"Processing {name} with {count} items")     # WRONG - perf hit
```

### Security Patterns
```python
# Prompt injection detection
from backend.utils.prompt_security import detect_prompt_injection
if detect_prompt_injection(user_prompt):
    return "Lo siento, no puedo procesar ese tipo de solicitud."

# Student code execution - NEVER use exec/eval directly
from backend.utils.sandbox import execute_python_code
stdout, stderr, exec_time = execute_python_code(code=student_code, timeout_seconds=30)

# Custom exceptions instead of HTTPException
from ..exceptions import SessionNotFoundError
raise SessionNotFoundError(session_id)  # NOT HTTPException(404, ...)

# Error sanitization for users
error_id = str(uuid.uuid4())[:8]
logger.error("Error [%s]: %s", error_id, str(error))
return f"Error occurred (ref: {error_id})"  # Safe for user display
```

### Thread Safety for Singletons (with Thundering Herd Prevention)
```python
# Cortez92: Use Union[None, bool, Instance] to prevent retry storms
_instance: Union[None, bool, MyClass] = None
_lock = threading.Lock()

def get_instance():
    global _instance
    with _lock:  # Lock-first pattern (safer than double-checked locking)
        if _instance is None:
            try:
                _instance = create_instance()
            except Exception:
                _instance = False  # Mark as failed to prevent retry storm

    if _instance is False:
        raise InitializationError("Failed to initialize. Restart to retry.")
    return _instance
```

### React 19 Patterns
```typescript
// Function components with typed props (NOT React.FC)
const MyComponent = ({ prop }: Props) => { ... };

// React 19's use() hook for context
const context = use(MyContext);

// React 19's useActionState for forms (Cortez93)
interface FormState { error: string | null; success: boolean; }
const [formState, submitAction, isPending] = useActionState<FormState, FormData>(
  async (_prevState, _formData): Promise<FormState> => {
    try {
      await submitData();
      return { error: null, success: true };
    } catch (err) {
      return { error: err.message, success: false };
    }
  },
  { error: null, success: false }
);
// Use in form: <form action={submitAction}>
// Use isPending for loading state, formState.error for errors

// Zustand for UI state
import { useUIStore, useSessionStore } from '@/stores';

// CSS variables for dark/light theme
className="bg-[var(--bg-card)] text-[var(--text-primary)]"

// Fast Refresh: contexts in separate files from components
// contexts/LTIContext.ts <- Context + types
// hooks/useLTIContext.ts <- Hook
// components/LTIContainer.tsx <- Component

// Guard Math.max with empty arrays
const maxCount = Math.max(...Object.values(distribution), 1);

// parseInt needs radix
parseInt(e.target.value, 10)

// Abort signal verification before setState
if (signal?.aborted) return;
```

### ORM Field Mappings
```python
# Enums stored as lowercase strings in DB
session.status = "active"        # NOT "ACTIVE"
risk.risk_level = "critical"     # NOT "CRITICAL"

# Score scales differ by context
evaluation.overall_score         # 0-10
session_summary.overall_score    # 0-1 normalized
risk_analysis.overall_score      # 0-100 percentage

# Datetime always timezone-aware
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc)  # NOT datetime.utcnow()
```

### Document Chunking for RAG (Cortez92)
```python
from backend.services.document_chunker import DocumentChunker, ChunkerConfig, ChunkingStrategy

# Configure chunker
config = ChunkerConfig(
    max_chunk_size=800,
    overlap_size=100,
    strategy=ChunkingStrategy.SEMANTIC,  # Respects paragraphs, code blocks, headings
    extract_keywords=True,
)

# Chunk any document (text, markdown, code files)
chunker = DocumentChunker(config)
result = await chunker.chunk_document(
    "path/to/file.txt",
    custom_metadata={"custom": {"materia": "Prog I", "source": "notes"}}
)

# Access chunks with rich metadata
for chunk in result.chunks:
    print(chunk.content[:100])
    print(chunk.metadata.keywords)       # Extracted keywords
    print(chunk.metadata.code_language)  # Detected: python, java, sql, etc. (23+ languages)
    print(chunk.metadata.section_title)  # Heading hierarchy
    print(chunk.metadata.prev_chunk_id)  # Relationship tracking
```

## Environment Configuration

Key `.env` variables:

```bash
# Required
POSTGRES_PASSWORD=xxx
REDIS_PASSWORD=xxx
JWT_SECRET_KEY=xxx
SECRET_KEY=xxx

# LLM
LLM_PROVIDER=gemini|ollama|mock|openai|mistral
GEMINI_API_KEY=xxx
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3

# RAG (optional)
RAG_ENABLED=false
RAG_MIN_CONFIDENCE=0.6
RAG_MAX_DOCUMENTS=3

# Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=50
```

**Test Credentials** (`python -m backend.scripts.create_test_users`):
- `teacher@activia.com` / `Teacher1234`
- `student@activia.com` / `Student1234`
- `admin@activia.com` / `admin123`

## Troubleshooting

```bash
# Module not found - run from activia1-main/
cd activia1-main && python -m backend

# PostgreSQL connection refused
docker-compose up -d db && sleep 5 && docker-compose up -d api

# Frontend build failures
cd frontEnd && rm -rf node_modules .vite dist && npm install && npm run build

# Windows encoding - avoid emojis in log messages
logger.info("Session started")  # CORRECT
logger.info("✅ Session started")  # May fail on Windows cp1252

# Path separators
import os
path = os.path.join("backend", "api", "routers")
```

## Documentation

- `backend/README.md` - Backend architecture (1,850+ lines)
- `frontEnd/README.md` - Frontend architecture
- `backend/agents/README.md` - AI agents documentation
