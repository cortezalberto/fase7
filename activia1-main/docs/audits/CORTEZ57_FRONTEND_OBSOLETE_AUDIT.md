# CORTEZ57 - Frontend Obsolete Code Audit

**Date**: 2026-01-01
**Scope**: Frontend codebase analysis for obsolete files, unused services, orphan components, and type inconsistencies
**Status**: COMPLETE - ALL ACTIONS IMPLEMENTED

---

## Executive Summary

| Category | Found | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Obsolete Services | 2 | 0 | 2 | 0 | 0 |
| Orphan Files | 1 | 0 | 1 | 0 | 0 |
| Duplicate Types | 3 | 0 | 0 | 3 | 0 |
| Unused Exports | 3 | 0 | 0 | 0 | 3 |
| **TOTAL** | **9** | **0** | **3** | **3** | **3** |

---

## 1. Obsolete Services (HIGH Priority)

### 1.1 adminService - Never Imported Outside Definition

**Location**: `frontEnd/src/services/api/admin.service.ts`
**Lines**: 179 lines
**Severity**: HIGH

**Evidence**:
```bash
# Only found in its own definition and index.ts export
grep -r "adminService" src/
# Results: Only in admin.service.ts:179 and index.ts:45
```

**Analysis**:
- Service is exported in `index.ts:45` but never imported by any page, component, or hook
- Backend routes exist at `/admin/llm/*` but no frontend UI consumes them
- Methods: `getLLMConfig()`, `updateLLMConfig()`, `getLLMUsageStats()`, `getSystemMetrics()`, `testLLMConnection()`

**Recommendation**:
- Keep for future admin panel implementation
- Mark as `@internal` or document as "reserved for admin features"

---

### 1.2 institutionalRisksService - Never Imported Outside Definition

**Location**: `frontEnd/src/services/api/institutionalRisks.service.ts`
**Lines**: 270 lines
**Severity**: HIGH

**Evidence**:
```bash
grep -r "institutionalRisksService" src/
# Only in institutionalRisks.service.ts:270 and index.ts:47
```

**Analysis**:
- Comprehensive service for institutional risk management
- Backend routes exist at `/admin/risks/*`
- No UI components consume: `scanForRisks()`, `getAlerts()`, `getDashboard()`, `createRemediationPlan()`, etc.

**Recommendation**:
- Keep for future teacher/admin dashboard
- Document as "HU-DOC-010 pending implementation"

---

## 2. Orphan Files (HIGH Priority)

### 2.1 ExerciseDetailPage.tsx - Not Routed

**Location**: `frontEnd/src/pages/ExerciseDetailPage.tsx`
**Lines**: 347 lines
**Severity**: HIGH

**Evidence**:
```typescript
// App.tsx routes - ExerciseDetailPage NOT imported
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TutorPage = lazy(() => import('./pages/TutorPage'));
// ... ExerciseDetailPage missing
```

**Analysis**:
- File exists and exports `ExerciseDetailPage` component
- Not imported in `App.tsx`
- Not lazy loaded
- Route `/exercises/:id` does not exist
- Component uses `exercisesService.getById()` which exists
- Appears to be legacy code from before TrainingExamPage refactoring

**Recommendation**:
- **DELETE** - Functionality superseded by TrainingExamPage + ExercisePanel
- Or route to `/exercises/:id` if needed for direct exercise access

---

## 3. Duplicate Types (MEDIUM Priority)

### 3.1 User Interface - Duplicated

**Locations**:
1. `frontEnd/src/types/index.ts:153-163` (canonical)
2. `frontEnd/src/services/api/auth.service.ts:10-20` (duplicate)

**Comparison**:
```typescript
// types/index.ts
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;      // optional
  student_id?: string;
  roles: string[];
  is_active: boolean;
  is_verified?: boolean;
  created_at?: string;
}

// auth.service.ts
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null; // nullable, not optional
  student_id?: string | null;
  roles: string[];
  created_at: string;       // required, not optional
  is_active: boolean;
  is_verified?: boolean;
}
```

**Discrepancies**:
- `full_name`: `string | undefined` vs `string | null`
- `created_at`: optional vs required

**Recommendation**:
- Use `types/index.ts` as canonical source
- Change auth.service.ts to: `import type { User } from '@/types';`

---

### 3.2 SimulatorStatus - Duplicated

**Locations**:
1. `frontEnd/src/types/index.ts:217` (inline in Simulator interface)
2. `frontEnd/src/services/api/simulators.service.ts:36` (exported type)

**Current State**:
```typescript
// types/index.ts - inline
status: 'active' | 'development' | 'deprecated';

// simulators.service.ts - exported
export type SimulatorStatus = 'active' | 'development' | 'deprecated';
```

**Recommendation**:
- Add to `types/domain/enums.ts` as canonical source
- Import in both files

---

### 3.3 TokenResponse - Duplicated (Scoped)

**Locations**:
1. `frontEnd/src/types/index.ts:166-171` (exported)
2. `frontEnd/src/services/api/auth.service.ts:210-214` (local interface)

**Analysis**:
- auth.service.ts uses local interface inside `refreshToken()` method
- Not a conflict since local scope, but redundant

**Recommendation**:
- Remove local interface in auth.service.ts
- Import from `@/types` instead

---

## 4. Unused Exports (LOW Priority)

### 4.1 cognitivePathService - Only Used Internally

**Location**: `frontEnd/src/services/api/cognitivePath.service.ts`
**Status**: LOW - Correctly used by delegation

**Evidence**:
```typescript
// traces.service.ts:145
return cognitivePathService.getCognitivePath(sessionId);
```

**Analysis**:
- Exported in index.ts but only consumed internally by tracesService
- This is correct architecture (tracesService delegates to cognitivePathService)

**Recommendation**: Keep as-is, proper internal delegation pattern

---

### 4.2 BaseApiService - Infrastructure Export

**Location**: `frontEnd/src/services/api/base.service.ts`
**Status**: LOW - Infrastructure class

**Analysis**:
- Abstract class used by all services internally
- Exported for potential external service creation
- 15 services extend it

**Recommendation**: Keep as infrastructure export

---

### 4.3 Deprecated Type Exports

**Location**: `frontEnd/src/services/api/evaluations.service.ts`

```typescript
// Lines 69-88
export interface StudentEvaluationSummary { ... }  // @deprecated
export interface ComparisonMetric { ... }          // @deprecated
```

**Recommendation**:
- Add `@deprecated` JSDoc comments
- Plan removal in next major version

---

## 5. Backend-Frontend Endpoint Alignment

### 5.1 All Training Endpoints - ALIGNED

| Backend Endpoint | Frontend Method | Status |
|------------------|-----------------|--------|
| `GET /training/lenguajes` | `trainingService.obtenerLenguajes()` | OK |
| `POST /training/iniciar` | `trainingService.iniciarEntrenamiento()` | OK |
| `POST /training/submit-ejercicio` | `trainingService.submitEjercicio()` | OK |
| `POST /training/corregir-ia` | `trainingService.corregirConIA()` | OK |
| `GET /training/sesion/{id}/estado` | `trainingService.obtenerEstadoSesion()` | OK |
| `POST /training/pista` | `trainingService.solicitarPista()` | OK |
| `POST /training/pista/v2` | `trainingService.solicitarPistaV2()` | OK |
| `POST /training/reflexion` | `trainingService.capturarReflexion()` | OK |
| `GET /training/sesion/{id}/proceso` | `trainingService.obtenerProcesoAnalisis()` | OK |
| `POST /training/submit/v2` | `trainingService.submitEjercicioV2()` | OK |

### 5.2 Services Without UI Consumers

| Service | Endpoints Covered | UI Consumer |
|---------|-------------------|-------------|
| adminService | `/admin/llm/*` | NONE |
| institutionalRisksService | `/admin/risks/*` | NONE |
| reportsService | `/reports/*` | Partial (some methods unused) |

---

## 6. Action Items

### Immediate (Cortez57) - ALL COMPLETED

| # | Action | File | Priority | Status |
|---|--------|------|----------|--------|
| 1 | Delete orphan file | `pages/ExerciseDetailPage.tsx` | HIGH | DONE |
| 2 | Consolidate User type | `services/api/auth.service.ts` | MEDIUM | DONE |
| 3 | Add SimulatorStatus to enums | `types/domain/enums.ts` | MEDIUM | DONE |
| 4 | Remove local TokenResponse | `services/api/auth.service.ts` | LOW | DONE |
| 5 | Document internal services | `admin.service.ts`, `institutionalRisks.service.ts` | LOW | DONE |

### Changes Made

1. **Deleted**: `frontEnd/src/pages/ExerciseDetailPage.tsx` (347 lines removed)
2. **Modified**: `auth.service.ts` - Now imports User from `@/types`, removed duplicate interface
3. **Modified**: `auth.service.ts` - Replaced local TokenResponse with inline type
4. **Added**: `SimulatorStatus` type to `types/domain/enums.ts`
5. **Modified**: `simulators.service.ts` - Now imports SimulatorStatus from enums
6. **Updated**: `types/domain/index.ts` - Exports new SimulatorStatus
7. **Documented**: `admin.service.ts` and `institutionalRisks.service.ts` marked as `@internal`

**TypeScript Compilation**: Verified - No errors

### Future (Post-Cortez57)

| # | Action | Notes |
|---|--------|-------|
| 1 | Implement Admin LLM UI | Use adminService |
| 2 | Implement Institutional Risks Dashboard | Use institutionalRisksService |
| 3 | Audit reportsService usage | Some methods may be unused |

---

## 7. Files Summary

### Safe to Delete
```
frontEnd/src/pages/ExerciseDetailPage.tsx  (347 lines)
```

### Keep but Mark Internal
```
frontEnd/src/services/api/admin.service.ts
frontEnd/src/services/api/institutionalRisks.service.ts
```

### Requires Type Consolidation
```
frontEnd/src/services/api/auth.service.ts (User, TokenResponse)
frontEnd/src/services/api/simulators.service.ts (SimulatorStatus)
```

---

## 8. Audit Methodology

1. **Service Usage Analysis**: Grep for service imports across all frontend code
2. **Route Analysis**: Compare App.tsx routes with page files
3. **Type Duplication**: Search for duplicate interface/type definitions
4. **Backend Alignment**: Match frontend service methods to backend router endpoints
5. **Export Analysis**: Track which exports are consumed vs orphaned

---

**Auditor**: Claude Code (Cortez57)
**Review Required**: Developer confirmation before deletions
