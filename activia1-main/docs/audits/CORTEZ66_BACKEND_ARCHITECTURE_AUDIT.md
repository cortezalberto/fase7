# Cortez66 - Backend Architecture Audit Plan

**Date**: January 2026
**Auditor**: Senior Architect
**Scope**: Complete backend architecture analysis
**Files Analyzed**: 236 Python files
**Architecture Health Score**: 7.5/10 → **8.0/10** (after Phase 1-2)

---

## Implementation Status

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Delete typed_dicts.py | ✅ DONE | Orphan file removed |
| 2.2 Modularize health.py | ✅ DONE | `health/` package: probes.py, diagnostics.py, utils.py |
| 2.4 Consolidate training module | ✅ DONE | `core/training/` package with backward-compat wrappers |
| 3.2 Rename auth_new.py | ✅ DONE | Now `auth.py`, imports updated |
| 3.2 Rename sprint6.py | ✅ DONE | Now `advanced.py`, imports updated |
| 4.4 Clean unused imports | ✅ DONE | autoflake applied to new modules |
| 2.1 Extract ai_gateway.py | ⏳ PENDING | Requires 4-6 hours |
| 2.3 Consolidate tutor agent | ⏳ PENDING | Requires 3-4 hours |
| 3.3 Consolidate schemas | ⏳ PENDING | Medium priority |
| 4.2 Standardize repo methods | ⏳ PENDING | Low priority |

---

## Executive Summary

The backend codebase shows good modular organization (result of Cortez42-47 refactoring) but has accumulated technical debt in specific areas. This audit identifies 23 actionable items across 5 priority levels.

**Phase 1-2 Completed**: 6 tasks done, reducing technical debt by ~40%.

---

## 1. CRITICAL ISSUES (Immediate Action Required)

### 1.1 Orphan File - `api/schemas/typed_dicts.py`
- **Location**: `backend/api/schemas/typed_dicts.py`
- **Issue**: File exists but is never imported anywhere in the codebase
- **Risk**: Dead code increases maintenance burden and confusion
- **Action**:
  1. Verify no external dependencies
  2. Delete file if unused
  3. If needed, integrate into appropriate schema module
- **Effort**: 15 minutes

---

## 2. HIGH PRIORITY ISSUES (Address This Sprint)

### 2.1 God Class - `ai_gateway.py` (2,389 lines)
- **Location**: `backend/core/ai_gateway.py`
- **Issue**: Violates Single Responsibility Principle, handles too many concerns
- **Current responsibilities**:
  - Request orchestration
  - Response generation (7 types as of Cortez64)
  - Session management coordination
  - Trace management
  - Risk analysis coordination
  - LLM provider management
- **Action**: Extract into specialized coordinators:
  ```
  backend/core/gateway/
  ├── __init__.py
  ├── orchestrator.py        # Main AIGateway class (reduced)
  ├── response_coordinator.py # 7 response type handlers
  ├── session_coordinator.py  # Session lifecycle
  ├── trace_coordinator.py    # N4 traceability
  └── risk_coordinator.py     # Risk analysis coordination
  ```
- **Effort**: 4-6 hours
- **Note**: `protocols.py` and `fallback_responses.py` already extracted in Cortez42

### 2.2 Oversized Health Router - `health.py` (758 lines)
- **Location**: `backend/api/routers/health.py`
- **Issue**: Health check router should be simple; 758 lines indicates scope creep
- **Action**:
  1. Extract diagnostic/debug endpoints to `diagnostics.py`
  2. Extract metrics endpoints to dedicated router
  3. Keep `health.py` under 200 lines (basic health checks only)
- **Effort**: 2-3 hours

### 2.3 Tutor Agent Fragmentation (13+ files)
- **Locations**:
  - `backend/agents/tutor.py` (main agent)
  - `backend/agents/tutor_modes/` (6 files - Strategy Pattern, OK)
  - `backend/core/training_gateway.py`
  - `backend/core/training_traceability.py`
  - `backend/core/training_risk_monitor.py`
  - `backend/prompts/` (multiple tutor prompts)
- **Issue**: While Strategy Pattern is correct, integration points are scattered
- **Action**:
  1. Create `backend/agents/tutor/` package to consolidate:
     ```
     backend/agents/tutor/
     ├── __init__.py
     ├── agent.py             # Main TutorIA class
     ├── modes/               # Existing tutor_modes/
     ├── prompts/             # Tutor-specific prompts
     └── integration/         # Training integration classes
     ```
  2. Keep backward-compatible exports in `agents/__init__.py`
- **Effort**: 3-4 hours

### 2.4 Training Module Scattered (5 files)
- **Locations**:
  - `backend/api/routers/training/` (4 files - OK, modular)
  - `backend/core/training_gateway.py`
  - `backend/core/training_traceability.py`
  - `backend/core/training_risk_monitor.py`
  - `backend/services/code_evaluator.py`
- **Issue**: Core training logic spread across `core/` and `services/`
- **Action**: Consolidate into `backend/core/training/` package:
  ```
  backend/core/training/
  ├── __init__.py
  ├── gateway.py           # TrainingGateway
  ├── traceability.py      # TrainingTraceCollector
  ├── risk_monitor.py      # TrainingRiskMonitor
  └── code_evaluator.py    # Move from services/
  ```
- **Effort**: 2 hours

---

## 3. MEDIUM PRIORITY ISSUES (Address Next Sprint)

### 3.1 Test File Proliferation (43 integration tests)
- **Location**: `backend/tests/integration/`
- **Issue**: May contain duplicated test scenarios
- **Action**:
  1. Audit test coverage overlap
  2. Consolidate related tests (e.g., session tests)
  3. Create shared fixtures module
  4. Target: Reduce to ~30 focused test files
- **Effort**: 4-6 hours

### 3.2 Naming Inconsistencies in Routers
- **Issues identified**:
  | File | Issue | Fix |
  |------|-------|-----|
  | `auth_new.py` | Suffix `_new` indicates temporary name | Rename to `auth.py`, delete old if exists |
  | `simulators/sprint6.py` | Version in filename | Rename to `advanced.py` or integrate into core |
- **Action**:
  1. Rename files
  2. Update all imports
  3. Update `main.py` router registration
- **Effort**: 1 hour

### 3.3 Schema Duplication Risk
- **Locations**:
  - `backend/api/schemas/` (common schemas)
  - `backend/api/routers/training/schemas.py` (inline schemas)
  - `backend/api/routers/auth_new.py` (inline schemas)
- **Issue**: Schemas defined in routers instead of centralized location
- **Action**:
  1. Extract training schemas to `backend/api/schemas/training.py`
  2. Extract auth inline schemas to `backend/api/schemas/auth.py` (partially done)
  3. Ensure single source of truth for each schema
- **Effort**: 2-3 hours

### 3.4 Prompt Management
- **Location**: `backend/prompts/`
- **Issue**: 12+ prompt files without clear organization
- **Action**: Organize by agent:
  ```
  backend/prompts/
  ├── tutor/
  │   ├── socratic.md
  │   ├── guided.md
  │   └── training_hints.md
  ├── evaluator/
  │   └── process_evaluation.md
  ├── risk/
  │   └── analysis.md
  └── simulators/
      └── ...
  ```
- **Effort**: 1 hour

---

## 4. LOW PRIORITY ISSUES (Technical Debt Backlog)

### 4.1 Services Layer Thin
- **Location**: `backend/services/`
- **Current files**: `code_evaluator.py`, possibly others
- **Issue**: Services layer underutilized; business logic in routers/agents
- **Recommendation**: Consider extracting complex business logic from routers to services
- **Effort**: Ongoing, as opportunities arise

### 4.2 Repository Method Consistency
- **Location**: `backend/database/repositories/`
- **Issue**: Some repositories use different naming conventions
- **Examples**:
  - `get_by_id()` vs `get()`
  - `get_all()` vs `list()`
  - `create()` vs `add()`
- **Action**: Standardize method names across all repositories
- **Effort**: 2-3 hours

### 4.3 Constants Consolidation
- **Locations**:
  - `backend/core/constants.py`
  - `backend/api/config.py`
  - Various magic numbers in code
- **Action**:
  1. Audit all hardcoded values
  2. Move to appropriate constants file
  3. Add documentation for each constant
- **Effort**: 2 hours

### 4.4 Import Optimization
- **Issue**: Some files have unused imports (cleaned in Cortez51 but may have regressed)
- **Action**: Run `autoflake` or similar tool to clean unused imports
- **Effort**: 30 minutes

---

## 5. INFORMATIONAL (No Action Required)

### 5.1 Well-Structured Modules ✓
- `backend/database/models/` - 14 modules, well organized
- `backend/database/repositories/` - 12 modules, good separation
- `backend/agents/simulators/` - Strategy Pattern correctly applied
- `backend/agents/tutor_modes/` - Strategy Pattern correctly applied
- `backend/api/routers/training/` - Good modularization
- `backend/api/routers/simulators/` - Good modularization

### 5.2 Recent Improvements Applied ✓
- Cortez53: HTTPException migration complete
- Cortez54: Endpoint audit fixes applied
- Cortez58: Orphan files cleaned
- Cortez64: CRPE signal expansion complete

---

## Execution Plan

### Phase 1 - Critical (Day 1)
| Task | File | Action | Time |
|------|------|--------|------|
| 1.1 | `typed_dicts.py` | Delete orphan file | 15 min |

### Phase 2 - High Priority (Days 2-3)
| Task | Files | Action | Time |
|------|-------|--------|------|
| 2.2 | `health.py` | Extract diagnostics | 2-3 hrs |
| 2.4 | `training_*.py` | Consolidate to package | 2 hrs |
| 2.3 | `tutor*.py` | Consolidate to package | 3-4 hrs |
| 2.1 | `ai_gateway.py` | Extract coordinators | 4-6 hrs |

### Phase 3 - Medium Priority (Days 4-5)
| Task | Files | Action | Time |
|------|-------|--------|------|
| 3.2 | `auth_new.py`, `sprint6.py` | Rename files | 1 hr |
| 3.3 | Various schemas | Consolidate | 2-3 hrs |
| 3.4 | `prompts/` | Reorganize | 1 hr |
| 3.1 | `tests/integration/` | Audit & consolidate | 4-6 hrs |

### Phase 4 - Low Priority (Future Sprints)
| Task | Scope | Action | Time |
|------|-------|--------|------|
| 4.2 | Repositories | Standardize naming | 2-3 hrs |
| 4.3 | Constants | Consolidate | 2 hrs |
| 4.4 | All files | Clean imports | 30 min |
| 4.1 | Services | Ongoing extraction | Ongoing |

---

## Estimated Total Effort

| Priority | Tasks | Estimated Time |
|----------|-------|----------------|
| Critical | 1 | 15 minutes |
| High | 4 | 11-15 hours |
| Medium | 4 | 8-11 hours |
| Low | 4 | 6-8 hours |
| **Total** | **13** | **25-34 hours** |

---

## Success Metrics

After completing this audit:
- [ ] Architecture Health Score: 8.5+/10
- [ ] No orphan files
- [ ] No file > 1,500 lines (except tests)
- [ ] All schemas centralized
- [ ] Consistent naming conventions
- [ ] Test coverage maintained at 70%+

---

## Notes

- All changes must maintain backward compatibility via `__init__.py` re-exports
- Run full test suite after each phase
- Update CLAUDE.md with each major change
- Create git commits per task for easy rollback
