/**
 * LTI Service - Learning Tools Interoperability API client
 *
 * HU-SYS-010: Integracion con Moodle via LTI 1.3
 *
 * This service provides frontend utilities for LTI integration:
 * - Detecting LTI context from URL parameters
 * - Fetching LTI session information
 * - Admin deployment management (future)
 *
 * NOTE: The actual LTI launch flow happens server-side.
 * The frontend receives session_id and lti=true query params
 * after successful LTI launch from Moodle.
 */

import { BaseApiService } from './base.service';

// =============================================================================
// Types
// =============================================================================

/**
 * LTI deployment configuration (admin view)
 */
export interface LTIDeployment {
  id: string;
  platform_name: string;
  issuer: string;
  client_id: string;
  deployment_id: string;
  auth_login_url: string;
  auth_token_url: string;
  public_keyset_url: string;
  access_token_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

/**
 * LTI session information
 */
export interface LTISession {
  id: string;
  deployment_id: string;
  lti_user_id: string;
  lti_user_name: string | null;  // Nombre completo del estudiante
  lti_user_email: string | null;
  lti_context_id: string | null;
  lti_context_label: string | null;  // Comision (ej: "PROG1-A")
  lti_context_title: string | null;  // Nombre del curso
  resource_link_id: string;
  resource_link_title: string | null;  // Nombre de la actividad
  session_id: string | null;
  locale: string | null;
  created_at: string;
}

/**
 * LTI context extracted from URL params after launch
 */
export interface LTIContext {
  isLTI: boolean;
  sessionId: string | null;
  userName: string | null;          // Nombre completo del estudiante
  contextTitle: string | null;       // Nombre del curso
  contextLabel: string | null;       // Comision (ej: "PROG1-A")
  resourceLinkTitle: string | null;  // Nombre de la actividad
}

/**
 * LTI health status
 */
export interface LTIHealthStatus {
  status: string;
  state_cache_size: number;
  nonce_cache_size: number;
  jwks_cache_size: number;
  message: string;
}

/**
 * Create deployment request
 */
export interface CreateDeploymentRequest {
  platform_name: string;
  issuer: string;
  client_id: string;
  deployment_id: string;
  auth_login_url: string;
  auth_token_url: string;
  public_keyset_url: string;
  access_token_url?: string;
}

// =============================================================================
// LTI Service Class
// =============================================================================

class LTIServiceClass extends BaseApiService {
  constructor() {
    super('/api/v1/lti');
  }

  // ===========================================================================
  // Context Detection (Client-side)
  // ===========================================================================

  /**
   * Detect LTI context from current URL.
   *
   * After a successful LTI launch from Moodle, the user is redirected to:
   * /tutor?session_id=xxx&lti=true
   *
   * This function extracts that context.
   *
   * @returns LTI context with session info
   */
  detectLTIContext(): LTIContext {
    if (typeof window === 'undefined') {
      return {
        isLTI: false,
        sessionId: null,
        userName: null,
        contextTitle: null,
        contextLabel: null,
        resourceLinkTitle: null,
      };
    }

    const params = new URLSearchParams(window.location.search);
    const isLTI = params.get('lti') === 'true';
    const sessionId = params.get('session_id');

    return {
      isLTI,
      sessionId: isLTI ? sessionId : null,
      userName: null,           // Will be fetched from session
      contextTitle: null,       // Will be fetched from session (course name)
      contextLabel: null,       // Will be fetched from session (commission)
      resourceLinkTitle: null,  // Will be fetched from session (activity name)
    };
  }

  /**
   * Check if current page is in LTI embedded mode.
   *
   * @returns true if page was launched from LTI (Moodle iframe)
   */
  isLTIMode(): boolean {
    return this.detectLTIContext().isLTI;
  }

  /**
   * Check if running inside an iframe (typical for LTI).
   *
   * @returns true if page is embedded in iframe
   */
  isEmbedded(): boolean {
    if (typeof window === 'undefined') return false;
    try {
      return window.self !== window.top;
    } catch {
      // Cross-origin iframe - assume embedded
      return true;
    }
  }

  // ===========================================================================
  // API Endpoints
  // ===========================================================================

  /**
   * Get LTI integration health status.
   *
   * @returns Health status including cache sizes
   */
  async getHealth(): Promise<LTIHealthStatus> {
    return this.get<LTIHealthStatus>('/health');
  }

  /**
   * List all LTI deployments (admin only).
   *
   * @returns Array of deployment configurations
   */
  async listDeployments(): Promise<LTIDeployment[]> {
    return this.get<LTIDeployment[]>('/deployments');
  }

  /**
   * Create a new LTI deployment (admin only).
   *
   * @param deployment - Deployment configuration
   * @returns Created deployment
   */
  async createDeployment(deployment: CreateDeploymentRequest): Promise<LTIDeployment> {
    return this.post<LTIDeployment, CreateDeploymentRequest>('/deployments', deployment);
  }

  /**
   * Deactivate an LTI deployment (admin only).
   *
   * @param deploymentId - Deployment ID to deactivate
   * @returns Success message
   */
  async deactivateDeployment(deploymentId: string): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/deployments/${deploymentId}`);
  }

  // ===========================================================================
  // UI Helpers
  // ===========================================================================

  /**
   * Get CSS class for LTI embedded mode.
   *
   * When embedded in Moodle iframe, we may want to hide certain UI elements
   * like the main navigation or show a more compact layout.
   *
   * @returns CSS class string or empty
   */
  getEmbeddedClass(): string {
    return this.isLTIMode() ? 'lti-embedded' : '';
  }

  /**
   * Clean URL by removing LTI parameters.
   *
   * After processing LTI context, clean the URL to prevent
   * issues with React Router and browser history.
   *
   * @param preserveSessionId - Whether to keep session_id in URL
   */
  cleanURL(preserveSessionId = true): void {
    if (typeof window === 'undefined') return;

    const url = new URL(window.location.href);
    url.searchParams.delete('lti');

    if (!preserveSessionId) {
      url.searchParams.delete('session_id');
    }

    // Update URL without triggering navigation
    window.history.replaceState({}, '', url.toString());
  }

  /**
   * Store LTI context in session storage for later use.
   *
   * @param context - LTI context to store
   */
  storeLTIContext(context: LTIContext): void {
    if (typeof window === 'undefined') return;
    sessionStorage.setItem('lti_context', JSON.stringify(context));
  }

  /**
   * Retrieve stored LTI context from session storage.
   *
   * @returns Stored LTI context or null
   */
  getStoredLTIContext(): LTIContext | null {
    if (typeof window === 'undefined') return null;
    try {
      const stored = sessionStorage.getItem('lti_context');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  /**
   * Clear stored LTI context.
   */
  clearLTIContext(): void {
    if (typeof window === 'undefined') return;
    sessionStorage.removeItem('lti_context');
  }
}

// =============================================================================
// Singleton Export
// =============================================================================

export const ltiService = new LTIServiceClass();
export default ltiService;
