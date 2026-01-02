# CORTEZ35 - Memory Leaks & Concurrency Audit

**Date:** December 2025
**Auditor:** Senior Developer & Software Architect (6 Parallel Agents)
**Scope:** Comprehensive backend analysis - Memory leaks, Connection leaks, Race conditions, Resource cleanup
**Total Issues Found:** 52 issues across 6 categories
**Methodology:** Deep static analysis with concurrent pattern detection

## ✅ FIXES APPLIED (December 29, 2025)

The following critical and high-priority issues have been remediated:

| # | Issue | File | Status |
|---|-------|------|--------|
| 1 | Redis clients in health checks | `health.py` | ✅ FIXED - Added `finally: client.close()` |
| 2 | Fire-and-forget task tracking | `ai_gateway.py` | ✅ FIXED - Added `_background_tasks` registry |
| 3 | LLM provider shutdown | `main.py` | ✅ FIXED - Added `await provider.close()` in lifespan |
| 4 | Prometheus high cardinality | `metrics.py` | ✅ FIXED - Removed session_id/student_id labels |
| 5 | User verify/deactivate TOCTOU | `repositories.py` | ✅ FIXED - Atomic SQL UPDATE |
| 6 | Database pool shutdown | `main.py` | ✅ FIXED - Added `db_config.close()` in lifespan |

**Total Fixed:** 6 issues (4 CRITICAL + 2 HIGH)
**Remaining:** 45 issues (pending Phase 2-4 implementation)

---

## Executive Summary

This audit was conducted using 6 specialized analysis agents examining the backend for memory leaks and concurrency issues. The codebase shows solid foundational patterns but has critical gaps in resource lifecycle management, particularly around HTTP clients, database connections, and background tasks.

### Risk Assessment by Category

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Async/Await Anti-Patterns | 1 | 3 | 3 | 2 | 9 |
| Database Connection Leaks | 0 | 2 | 6 | 2 | 10 |
| HTTP Client Leaks | 1 | 3 | 2 | 0 | 6 |
| Cache Memory Leaks | 1 | 1 | 4 | 1 | 7 |
| Race Conditions | 0 | 4 | 3 | 3 | 10 |
| Resource Cleanup | 1 | 3 | 3 | 2 | 9 |
| **TOTAL** | **4** | **16** | **21** | **10** | **51** |

### Critical Issues Requiring Immediate Attention

1. **Fire-and-forget tasks without tracking** (`ai_gateway.py`) - Memory leak potential
2. **Redis clients never closed in health checks** (`health.py`) - Connection exhaustion
3. **HTTP clients not closed on shutdown** (`ollama_provider.py`) - Connection leak
4. **Prometheus metrics with high cardinality labels** (`metrics.py`) - Unbounded memory growth

---

## 1. ASYNC/AWAIT ANTI-PATTERNS

### 1.1 CRITICAL: Fire-and-Forget Task Without Resource Tracking

**File:** `backend/core/ai_gateway.py`
**Lines:** 547-654

```python
task = loop.create_task(_async_task(), name=f"risk_analysis_{session_id}")
task.add_done_callback(_task_done_callback)
# Task is NOT stored in a registry - can be GC'd while pending
```

**Impact:**
- Tasks can be garbage collected while pending, canceling unexpectedly
- No mechanism to cancel/cleanup pending tasks during shutdown
- Memory accumulates if many tasks queue up
- `asyncio.to_thread()` spawns threads without bounds

**Recommendation:**
```python
self._background_tasks = set()
task = loop.create_task(_async_task(), name=f"risk_analysis_{session_id}")
self._background_tasks.add(task)
task.add_done_callback(lambda t: self._background_tasks.discard(t))
```

### 1.2 HIGH: Non-Awaited Coroutine in Thread Context

**File:** `backend/core/ai_gateway.py`
**Lines:** 578-600

```python
def _analyze_with_fresh_db_session() -> None:
    """Run risk analysis using a brand-new DB session"""
    with get_db_session() as db_session:
        self._analyze_risks_async(  # ← Missing await!
            session_id, input_trace, response_trace, ...
        )
```

**Impact:** Coroutine object created but never executed = memory leak. Risk analysis never actually runs.

### 1.3 HIGH: Event Loop Fallback Logic Error

**File:** `backend/core/ai_gateway.py`
**Lines:** 571-576

```python
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    self._analyze_risks_async(...)  # Missing await in fallback!
    return
```

**Impact:** In sync context fallback, async function is called but not awaited.

**Fix:**
```python
except RuntimeError:
    asyncio.run(self._analyze_risks_async(...))
    return
```

### 1.4 HIGH: HTTP Client Destructor Cannot Await

**File:** `backend/llm/ollama_provider.py`
**Lines:** 213-225

```python
def __del__(self):
    if self._client is not None:
        # Can't await in __del__, so just log a warning
        logger.warning("OllamaProvider destroyed without closing HTTP client...")
```

**Impact:** HTTP connections leak when provider is garbage collected without explicit close().

### 1.5 MEDIUM: Blocking Database Calls in Async Context

**File:** `backend/core/ai_gateway.py`
**Throughout:** `process_interaction()` method

```python
async def process_interaction(...):
    db_session = self.session_repo.get_by_id(session_id)  # ← Blocking I/O!
```

**Impact:** Synchronous SQLAlchemy calls block event loop during I/O under high concurrency.

**Recommendation:** Wrap with `asyncio.to_thread()`:
```python
db_session = await asyncio.to_thread(self.session_repo.get_by_id, session_id)
```

### 1.6 MEDIUM: Connection Pool Size Mismatch

**File:** `backend/llm/ollama_provider.py`
**Lines:** 156-163

```python
self._client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
)
# But semaphore allows max_concurrent=10
```

**Impact:** Pool limits match semaphore exactly - should have headroom (2x).

### 1.7 MEDIUM: Double-Checked Locking in Async

**File:** `backend/llm/ollama_provider.py`
**Lines:** 165-182

The semaphore initialization uses double-checked locking which is technically safe but considered an anti-pattern in Python async.

### 1.8 LOW: Redis Connection Not Closed in Shutdown

**File:** `backend/core/redis_cache.py`

No explicit shutdown handler for Redis client closure.

### 1.9 LOW: LLM Provider Not Closed in FastAPI Lifespan

**File:** `backend/api/main.py`
**Lines:** 68-127

Lifespan manager has no cleanup for LLM provider:
```python
async def lifespan(app: FastAPI):
    yield
    # Missing: await provider.close()
```

---

## 2. DATABASE CONNECTION LEAKS

### 2.1 HIGH: Unbounded Query Loading Into Memory

**File:** `backend/api/routers/export.py`
**Lines:** 82, 98, 102-152

```python
sessions = db.query(SessionDB).filter(*filters).all()  # No limit!
traces = db.query(CognitiveTraceDB).filter(...).all()  # All into memory!
```

**Impact:** For large datasets, this:
- Consumes all available memory
- Holds DB connection for extended time
- Can cause pool exhaustion under concurrency

**Recommendation:** Add pagination/streaming:
```python
sessions = db.query(SessionDB).filter(*filters).limit(1000).offset(page * 1000).all()
```

### 2.2 HIGH: Loop-Based Deletion Pattern (N+1 Deletes)

**File:** `backend/scripts/clean_and_reset_db.py`
**Lines:** 69-123

```python
non_sec_attempts = session.query(ExerciseAttemptDB).filter(...).all()
for attempt in non_sec_attempts:
    session.delete(attempt)  # N separate delete operations!
```

**Impact:** Extremely slow with large datasets, holds connection during entire loop.

**Fix:** Use bulk delete:
```python
session.query(ExerciseAttemptDB).filter(...).delete()
```

### 2.3 MEDIUM: User Role Query Memory Fallback

**File:** `backend/database/repositories.py`
**Line:** 2230

```python
# Fallback for unknown dialects: Load and filter in Python
all_users = self.db.query(UserDB).filter(UserDB.is_active == True).all()
return [user for user in all_users if role in user.roles]
```

**Impact:** Loads ALL active users into memory for filtering.

### 2.4 MEDIUM: Missing Pagination on .all() Queries

**File:** `backend/database/repositories.py`
**Lines:** 1821, 1840, 2901, 3068, 3077, 3088

Multiple `get_all()` methods without limits:
```python
def get_all(self):
    return query.order_by(...).all()  # No limit!
```

### 2.5 MEDIUM: Script Creates Duplicate Engine

**File:** `backend/scripts/clean_and_reset_db.py`
**Lines:** 54-56

```python
engine = create_engine(config.database_url)  # Creates NEW engine!
Session = sessionmaker(bind=engine)
```

**Impact:** Script creates separate connection pool from application.

### 2.6 MEDIUM: SimulatorEventDB Bulk Delete Without Batching

**File:** `backend/database/repositories.py`
**Lines:** 3855-3861

Large bulk deletes without batching can lock tables.

### 2.7 MEDIUM: Export Function Cascading Loads

**File:** `backend/api/routers/export.py`
**Lines:** 80-170

Multiple `.all()` calls load progressively larger datasets simultaneously.

### 2.8 MEDIUM: Two Transactions for Init Exercises

**File:** `backend/scripts/init_exercises.py`
**Lines:** 138-146

Separate delete and insert commits extend connection usage.

### 2.9 LOW: Large IN Clause in Export

**File:** `backend/api/routers/export.py`
**Lines:** 426, 484

```python
sessions = db.query(SessionDB).filter(SessionDB.id.in_(session_ids)).all()
```

With 10K+ IDs, SQL IN clause becomes problematic.

### 2.10 LOW: Error Case Connection Handling

**File:** `backend/scripts/clean_and_reset_db.py`
**Lines:** 160-165

While `finally` block exists, edge cases could leak connections.

---

## 3. HTTP CLIENT CONNECTION LEAKS

### 3.1 CRITICAL: Ollama Provider Client Not Closed on Shutdown

**File:** `backend/llm/ollama_provider.py`
**Lines:** 156-163, 184-203

```python
self._client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
)
```

**Impact:**
- Client is lazily initialized but NO FastAPI shutdown handler calls `await provider.close()`
- On app restart, OLD connections remain open
- Connection pool accumulates across restarts

**Fix:** Add to `backend/api/main.py` lifespan:
```python
async def lifespan(app: FastAPI):
    yield
    if hasattr(app.state, 'llm_provider'):
        await app.state.llm_provider.close()
```

### 3.2 HIGH: Gemini Provider Creates New Client Per Request

**File:** `backend/llm/gemini_provider.py`
**Lines:** 200-272, 374-402

```python
for attempt in range(self.max_retries):
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(...)
```

**Impact:** Creates new client on EACH retry (up to 3x per request). No connection pool reuse.

### 3.3 HIGH: Mistral Provider Creates New Client Per Request

**File:** `backend/llm/mistral_provider.py`
**Lines:** 150-206, 276-304

Same pattern as Gemini - new client per request.

### 3.4 HIGH: Test Script Uses Blocking requests Library

**File:** `backend/tests/integration/test_direct.py`
**Lines:** 3-37

```python
import requests
login_resp = requests.post(...)  # Blocking, no cleanup
```

### 3.5 MEDIUM: No Timeout Override for Model Checks

**File:** `backend/llm/ollama_provider.py`
**Lines:** 615-634

`is_model_available()` uses same timeout as main calls - should be shorter.

### 3.6 MEDIUM: Database Pool Not Disposed on Shutdown

**File:** `backend/database/config.py`
**Lines:** 136-141

`close()` method exists but never called in app lifecycle.

---

## 4. CACHE MEMORY LEAKS

### 4.1 CRITICAL: Prometheus Metrics High Cardinality Labels

**File:** `backend/api/monitoring/metrics.py`
**Lines:** 68, 318-323

```python
_metrics: Dict[str, Any] = {}  # Global mutable dictionary

metrics_counter("interactions_total", {
    "session_id": session_id[:8],  # 8 chars still creates cardinality
    "student_id": student_id[:8],
    "agent_used": agent_used,
    "status": status,
})
```

**Impact:** Each unique combination of labels creates a new time series in memory. With many sessions/students, this grows unbounded.

**Recommendation:** Use low-cardinality labels only (agent_type, status) - not session IDs.

### 4.2 HIGH: Cache Singleton No Automatic TTL Cleanup

**File:** `backend/core/cache.py`
**Lines:** 433-471

```python
_global_cache: Optional[LLMResponseCache] = None
# cleanup_expired() is never automatically called!
```

**Impact:** `_timestamps` dict grows with cache insertions; expired entries only removed on explicit cleanup which is never scheduled.

**Recommendation:** Add periodic cleanup task:
```python
@app.on_event("startup")
async def schedule_cache_cleanup():
    asyncio.create_task(periodic_cache_cleanup())
```

### 4.3 MEDIUM: Redis Cache Fallback Never Cleared

**File:** `backend/core/redis_cache.py`
**Lines:** 500-536

`_fallback_cache` (LRUCache with max_size=1000) is never cleared on shutdown.

### 4.4 MEDIUM: Prometheus Registry Not Disposed

**File:** `backend/api/monitoring/metrics.py`
**Lines:** 40-60

Global registry accumulates metrics without cleanup.

### 4.5 MEDIUM: Lazy Metrics Module Pattern Repeated

**Files:** `cache.py`, `ai_gateway.py`, `ollama_provider.py`

Same lazy-load pattern duplicated in 3+ files - violates DRY.

### 4.6 MEDIUM: Database Pool Recycle Without Dispose

**File:** `backend/database/config.py`
**Lines:** 69-105

Pool recycle is set but `pool.dispose()` never called on shutdown.

### 4.7 LOW: Metrics Module Never Unloaded

Multiple files hold module references that are never released.

---

## 5. RACE CONDITIONS

### 5.1 HIGH: Sessions Active Gauge Race Condition

**File:** `backend/core/metrics.py`
**Lines:** 207-213

```python
def record_session(mode: str, active: bool):
    sessions_total.labels(mode=mode).inc()
    if active:
        sessions_active.inc()  # Race with concurrent dec()!
    else:
        sessions_active.dec()
```

**Scenario:**
- Thread 1 reads sessions_active = 5, about to inc()
- Thread 2 reads sessions_active = 5, about to dec()
- Thread 1 writes 6
- Thread 2 writes 4 (should be 5)

### 5.2 HIGH: User Verification TOCTOU Vulnerability

**File:** `backend/database/repositories.py`
**Lines:** 2385-2405

```python
def verify_user(self, user_id: str) -> Optional[UserDB]:
    user = self.get_by_id(user_id)      # CHECK
    if not user:
        return None
    user.is_verified = True              # TOCTOU GAP - another request could modify/delete
    self.db.commit()                     # USE
```

**Fix:** Use atomic SQL UPDATE like `update_last_login`:
```python
rows = self.db.query(UserDB).filter(UserDB.id == user_id).update(
    {UserDB.is_verified: True},
    synchronize_session='fetch'
)
```

### 5.3 HIGH: Deactivate User TOCTOU

**File:** `backend/database/repositories.py`
**Lines:** 2407-2445

Same pattern as verify_user - read-modify-write without locking.

### 5.4 HIGH: Reactivate User TOCTOU

**File:** `backend/database/repositories.py`
**Lines:** 2429+

Same vulnerable pattern.

### 5.5 MEDIUM: Redis Connection Error Flag Race

**File:** `backend/core/redis_cache.py`
**Line:** 216

```python
if not self._connection_error_logged:    # Check without lock
    logger.error(f"Redis connection error: {e}")
    self._connection_error_logged = True  # Set without lock
```

**Impact:** Multiple threads could log error simultaneously.

### 5.6 MEDIUM: Cache Key Session Isolation

**File:** `backend/core/cache.py`
**Line:** 268

Session ID included in cache key, but empty session_id could share cache between sessions.

### 5.7 MEDIUM: Metrics Inc/Dec Not Atomic as Group

**File:** `backend/core/metrics.py`
**Lines:** 195-240

Multiple related metrics incremented separately - crash between them leaves inconsistent state.

### 5.8 LOW: Session Status Update Non-Atomic

**File:** `backend/database/repositories.py`
**Lines:** 438+

```python
def update_status(self, session_id: str, status: str):
    session = self.get_by_id(session_id)  # READ
    session.status = status                # MODIFY
    self.db.commit()                       # WRITE
```

Lost updates possible under concurrency.

### 5.9 LOW: LRUCache Statistics Counter

**File:** `backend/core/cache.py`
**Lines:** 86-180

While lock is used for dict access, counter increments could race in edge cases.

### 5.10 LOW: Metrics Counter Grouping

**File:** `backend/core/metrics.py`
**Lines:** 318-323

Related metrics not updated atomically.

---

## 6. RESOURCE CLEANUP ISSUES

### 6.1 CRITICAL: Redis Clients Never Closed in Health Checks

**File:** `backend/api/routers/health.py`
**Lines:** 307, 503

```python
redis_client = redis.from_url(redis_url, decode_responses=True)
redis_client.ping()
# NO CLEANUP! Client connection remains open
```

**Impact:** Every health check creates new Redis connection that's never closed. Under frequent health checks (Kubernetes probes every 10s), connections accumulate rapidly.

**Fix:**
```python
redis_client = redis.from_url(redis_url, decode_responses=True)
try:
    redis_client.ping()
finally:
    redis_client.close()
```

### 6.2 HIGH: Temporary Files May Not Be Removed

**File:** `backend/api/routers/exercises.py`
**Lines:** 222-249

```python
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(sandboxed_code)
    temp_file = f.name

try:
    result = subprocess.run([...])
finally:
    if os.path.exists(temp_file):
        os.remove(temp_file)  # Can fail silently!
```

**Impact:** If `os.remove()` fails (permission denied), temp files accumulate.

**Fix:** Log deletion failures:
```python
finally:
    try:
        os.remove(temp_file)
    except OSError as e:
        logger.error(f"Failed to remove temp file {temp_file}: {e}")
```

### 6.3 HIGH: Gemini Provider New Client Per Request

**File:** `backend/llm/gemini_provider.py`

Each request creates/destroys httpx client - inefficient resource churn.

### 6.4 HIGH: Mistral Provider New Client Per Request

**File:** `backend/llm/mistral_provider.py`

Same inefficient pattern as Gemini.

### 6.5 MEDIUM: OllamaProvider Shutdown Not Registered

**File:** `backend/llm/ollama_provider.py`

`close()` method exists but not called from FastAPI lifecycle.

### 6.6 MEDIUM: Database Config Close Never Called

**File:** `backend/database/config.py`

`engine.dispose()` method exists but not invoked on shutdown.

### 6.7 MEDIUM: psutil.Process Handle Not Freed

**File:** `backend/api/routers/health.py`
**Lines:** 42-43

```python
process = psutil.Process(os.getpid())
return process.memory_info().rss  # process object holds OS handle
```

### 6.8 LOW: Redis Cleanup Missing in Exception Path

**File:** `backend/api/routers/health.py`
**Lines:** 304-320

Redis client not closed if exception occurs before cleanup.

### 6.9 LOW: Subprocess Resources

**File:** `backend/api/routers/exercises.py`

Subprocess runs with timeout but terminated processes may leave zombie entries.

---

## PRIORITY REMEDIATION PLAN

### Phase 1: Critical (Immediate - 1-2 days) ✅ COMPLETED

| # | Issue | File | Fix | Status |
|---|-------|------|-----|--------|
| 1 | Redis clients in health checks | health.py | Add `finally: client.close()` | ✅ DONE |
| 2 | Fire-and-forget task tracking | ai_gateway.py | Add task registry set | ✅ DONE |
| 3 | LLM provider shutdown | main.py | Add `await provider.close()` in lifespan | ✅ DONE |
| 4 | Prometheus high cardinality | metrics.py | Remove session_id/student_id labels | ✅ DONE |

### Phase 2: High Priority (Week 1) - PARTIALLY COMPLETED

| # | Issue | File | Fix | Status |
|---|-------|------|-----|--------|
| 5 | Non-awaited coroutine | ai_gateway.py | Fix fallback async call | ⚠️ FALSE POSITIVE - Function is sync by design |
| 6 | Export unbounded queries | export.py | Add pagination limits | ⏳ PENDING |
| 7 | Gemini/Mistral client per request | *_provider.py | Use persistent client like Ollama | ⏳ PENDING |
| 8 | User verify/deactivate TOCTOU | repositories.py | Use atomic SQL UPDATE | ✅ DONE |
| 9 | Loop-based deletions | clean_and_reset_db.py | Use bulk delete | ⏳ PENDING |
| 10 | Temp file cleanup logging | exercises.py | Log deletion failures | ⏳ PENDING |

### Phase 3: Medium Priority (Week 2-3)

| # | Issue | File | Fix |
|---|-------|------|-----|
| 11 | Blocking DB in async | ai_gateway.py | Wrap with asyncio.to_thread |
| 12 | Cache TTL cleanup | cache.py | Add periodic cleanup task |
| 13 | Redis fallback cache cleanup | redis_cache.py | Clear on shutdown |
| 14 | Sessions gauge race | metrics.py | Use atomic operations |
| 15 | Redis error flag race | redis_cache.py | Add lock |
| 16 | Pool size mismatch | ollama_provider.py | Increase limits to 2x semaphore |

### Phase 4: Low Priority (Sprint backlog)

- Add pagination defaults to all `get_all()` methods
- Consolidate lazy metrics module pattern
- Add DB pool dispose on shutdown
- Fix session status atomic updates

---

## POSITIVE ASPECTS

The codebase demonstrates solid fundamentals:

- ✅ **Thread-safe singleton patterns** with double-checked locking
- ✅ **AIGateway is STATELESS** - eliminates entire class of race conditions
- ✅ **LRUCache uses threading.Lock** for dict operations
- ✅ **OllamaProvider has semaphore** for concurrency control (Cortez34)
- ✅ **Background tasks have error callbacks** (Cortez34)
- ✅ **Atomic SQL UPDATE pattern** used correctly in `update_last_login`
- ✅ **Context managers** used for most DB sessions
- ✅ **Transaction rollback** on exceptions in repositories

---

## CONCLUSION

The AI-Native MVP backend has a solid foundation but requires attention to resource lifecycle management. The most critical issues are:

1. **Connection leaks** in health checks and LLM providers
2. **Unbounded memory growth** from Prometheus metrics and caches
3. **Race conditions** in user state management
4. **Missing shutdown handlers** for cleanup

**Estimated Remediation Effort:**
- Critical issues: 1-2 days
- High priority: 1 week
- Complete cleanup: 2-3 weeks

**Recommendation:** Address Phase 1 (Critical) immediately. The Redis connection leak in health checks is particularly concerning since Kubernetes probes can trigger it every 10 seconds, potentially exhausting connections within hours.

---

## APPENDIX: Files Requiring Immediate Attention

### Critical
- `backend/api/routers/health.py` - Redis connection leaks
- `backend/core/ai_gateway.py` - Task tracking, async issues
- `backend/api/main.py` - Missing shutdown handlers
- `backend/api/monitoring/metrics.py` - High cardinality labels

### High Priority
- `backend/llm/gemini_provider.py` - Client per request
- `backend/llm/mistral_provider.py` - Client per request
- `backend/database/repositories.py` - TOCTOU vulnerabilities
- `backend/api/routers/export.py` - Unbounded queries

### Medium Priority
- `backend/core/cache.py` - TTL cleanup
- `backend/core/redis_cache.py` - Fallback cleanup, error flag race
- `backend/core/metrics.py` - Gauge race conditions
- `backend/llm/ollama_provider.py` - Pool sizing
