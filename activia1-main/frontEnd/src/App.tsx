import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './shared/components/Toast/Toast';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary, { ErrorBoundaryWithNavigation } from './components/ErrorBoundary';

// FE-OPT-004: Lazy loading for pages - reduces initial bundle size
// Critical pages (login, register) loaded eagerly for fast first paint
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Non-critical pages lazy loaded - only loaded when navigated to
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TutorPage = lazy(() => import('./pages/TutorPage'));
const ExercisesPageNew = lazy(() => import('./pages/ExercisesPageNew'));
const ExercisesPage = lazy(() => import('./pages/ExercisesPage')); // Sistema nuevo con evaluador Alex
const SimulatorsPage = lazy(() => import('./pages/SimulatorsPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
// FIX 2.1: Import missing pages (Cortez2 audit) - also lazy loaded
const EvaluatorPage = lazy(() => import('./pages/EvaluatorPage'));
const RisksPage = lazy(() => import('./pages/RisksPage'));
const GitAnalyticsPage = lazy(() => import('./pages/GitAnalyticsPage'));
const TraceabilityPage = lazy(() => import('./pages/TraceabilityPage'));
const TrainingPage = lazy(() => import('./pages/TrainingPage'));
const TrainingExamPage = lazy(() => import('./pages/TrainingExamPage'));

// Teacher/Docente pages (HU-DOC-001 to HU-DOC-010)
const TeacherDashboardPage = lazy(() => import('./pages/TeacherDashboardPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const InstitutionalRisksPage = lazy(() => import('./pages/InstitutionalRisksPage'));
const StudentMonitoringPage = lazy(() => import('./pages/StudentMonitoringPage'));
const ActivityManagementPage = lazy(() => import('./pages/ActivityManagementPage'));

// FE-OPT-004: Loading fallback component for lazy loaded pages
const PageLoadingFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes - FE-OPT-004: Wrapped with Suspense for lazy loading */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              {/* FIX Cortez48: Use ErrorBoundaryWithNavigation for proper React Router navigation */}
              <Route path="dashboard" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><DashboardPage /></Suspense></ErrorBoundaryWithNavigation>} />
              {/* Critical pages with markdown rendering wrapped with their own ErrorBoundary */}
              <Route path="tutor" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><TutorPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="exercises-old" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><ExercisesPageNew /></Suspense></ErrorBoundaryWithNavigation>} />
              {/* Sistema de Ejercicios con Evaluador Alex */}
              <Route path="exercises/*" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><ExercisesPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="simulators" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><SimulatorsPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="analytics" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><AnalyticsPage /></Suspense></ErrorBoundaryWithNavigation>} />
              {/* FIX 2.1: Add missing routes (Cortez2 audit) */}
              <Route path="evaluator" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><EvaluatorPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="risks" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><RisksPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="git" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><GitAnalyticsPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="traceability" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><TraceabilityPage /></Suspense></ErrorBoundaryWithNavigation>} />
              {/* Entrenador Digital - Sistema jerárquico (Lenguaje → Lección → Ejercicios) */}
              <Route path="training" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><TrainingPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="training/exam" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><TrainingExamPage /></Suspense></ErrorBoundaryWithNavigation>} />

              {/* Teacher/Docente routes (HU-DOC-001 to HU-DOC-010) - Requires teacher role */}
              <Route path="teacher" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><TeacherDashboardPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="teacher/dashboard" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><TeacherDashboardPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="teacher/reports" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><ReportsPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="teacher/risks" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><InstitutionalRisksPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="teacher/monitoring" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><StudentMonitoringPage /></Suspense></ErrorBoundaryWithNavigation>} />
              <Route path="teacher/activities" element={<ErrorBoundaryWithNavigation><Suspense fallback={<PageLoadingFallback />}><ActivityManagementPage /></Suspense></ErrorBoundaryWithNavigation>} />

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;