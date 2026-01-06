/**
 * Layout principal de la aplicación
 * FIX Cortez31: Migrated to Zustand for state management
 * Cortez92: Use granular selectors to prevent unnecessary re-renders
 */
import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
// Cortez92: Use granular selectors to prevent unnecessary re-renders
import {
  useTheme,
  useSidebarCollapsed,
  useToggleTheme,
  useToggleSidebar,
  useCurrentSession,
} from '@/stores';
import { useAuth } from '@/contexts/AuthContext';
import { ROUTES } from '@/core/config/routes.config';
import { wsService } from '@/core/websocket/WebSocketService';
import './MainLayout.css';

// FIX Cortez48: Use function component pattern instead of React.FC
export function MainLayout() {
  // FIX Cortez31: Use Zustand stores instead of AppContext
  // Cortez92: Use granular selectors - prevents re-render when unrelated store values change
  const theme = useTheme();
  const sidebarCollapsed = useSidebarCollapsed();
  const toggleTheme = useToggleTheme();
  const toggleSidebar = useToggleSidebar();
  const currentSession = useCurrentSession();
  const { user, logout } = useAuth();
  const [wsStatus, setWsStatus] = React.useState(wsService.getState());

  React.useEffect(() => {
    const unsubscribe = wsService.onEvent('connect', () => {
      setWsStatus(wsService.getState());
    });

    const unsubscribe2 = wsService.onEvent('disconnect', () => {
      setWsStatus(wsService.getState());
    });

    return () => {
      unsubscribe();
      unsubscribe2();
    };
  }, []);

  return (
    <div className={`main-layout ${theme}`}>
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <h1 className="logo">🎓 AI-Native</h1>
          <button
            className="collapse-btn"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        <nav className="sidebar-nav">
          <NavLink to={ROUTES.DASHBOARD} className="nav-item">
            <span className="nav-icon">📊</span>
            <span className="nav-label">Dashboard</span>
          </NavLink>

          <div className="nav-section">
            <div className="nav-section-title">Agentes IA</div>
            
            <NavLink to={ROUTES.AGENTS.TUTOR} className="nav-item">
              <span className="nav-icon">🎓</span>
              <span className="nav-label">Tutor Cognitivo</span>
            </NavLink>

            <NavLink to={ROUTES.AGENTS.EVALUATOR} className="nav-item">
              <span className="nav-icon">📈</span>
              <span className="nav-label">Evaluador</span>
            </NavLink>

            <NavLink to={ROUTES.AGENTS.SIMULATOR} className="nav-item">
              <span className="nav-icon">🎭</span>
              <span className="nav-label">Simuladores</span>
            </NavLink>

            <NavLink to={ROUTES.AGENTS.RISK_ANALYST} className="nav-item">
              <span className="nav-icon">⚠️</span>
              <span className="nav-label">Análisis de Riesgos</span>
            </NavLink>

            <NavLink to={ROUTES.AGENTS.TRACEABILITY} className="nav-item">
              <span className="nav-icon">🔍</span>
              <span className="nav-label">Trazabilidad N4</span>
            </NavLink>

            <NavLink to={ROUTES.AGENTS.GIT_ANALYTICS} className="nav-item">
              <span className="nav-icon">📊</span>
              <span className="nav-label">Git Analytics</span>
            </NavLink>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Herramientas</div>
            
            <NavLink to={ROUTES.TEACHER} className="nav-item">
              <span className="nav-icon">👨‍🏫</span>
              <span className="nav-label">Panel Docente</span>
            </NavLink>

            <NavLink to={ROUTES.PLAYGROUND} className="nav-item">
              <span className="nav-icon">🧪</span>
              <span className="nav-label">Playground</span>
            </NavLink>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className={`ws-status ${wsStatus === 'OPEN' ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            <span className="status-text">
              {wsStatus === 'OPEN' ? 'Conectado' : 'Desconectado'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-content">
        {/* Top Bar */}
        <header className="top-bar">
          <div className="top-bar-left">
            {currentSession && (
              <div className="session-indicator">
                <span className="session-badge">
                  Sesión activa: {currentSession.id.slice(0, 8)}
                </span>
              </div>
            )}
          </div>

          <div className="top-bar-right">
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>

            {/* FIX Cortez31: Use user/logout from AuthContext */}
            {user && (
              <div className="user-menu">
                <span className="user-name">{user.username || user.email}</span>
                <button onClick={logout} className="logout-btn">
                  Salir
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
