"""
Excepciones personalizadas para la API REST
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AINativeAPIException(HTTPException):
    """Excepción base para la API AI-Native"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.extra = extra or {}


class NotFoundError(AINativeAPIException):
    """Generic not found error for any resource"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} '{resource_id}' not found",
            error_code="NOT_FOUND",
            extra={"resource_type": resource_type, "resource_id": resource_id}
        )


class SessionNotFoundError(AINativeAPIException):
    """Sesión no encontrada"""

    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
            error_code="SESSION_NOT_FOUND",
            extra={"session_id": session_id}
        )


class StudentNotFoundError(AINativeAPIException):
    """Estudiante no encontrado"""

    def __init__(self, student_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{student_id}' not found",
            error_code="STUDENT_NOT_FOUND",
            extra={"student_id": student_id}
        )


class InvalidInteractionError(AINativeAPIException):
    """Interacción inválida"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="INVALID_INTERACTION",
            extra=details or {}
        )


class GovernanceBlockedError(AINativeAPIException):
    """Interacción bloqueada por políticas de gobernanza"""

    def __init__(self, reason: str, policy: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Interaction blocked by governance: {reason}",
            error_code="GOVERNANCE_BLOCKED",
            extra={"reason": reason, "policy": policy}
        )


class RiskThresholdExceededError(AINativeAPIException):
    """Umbral de riesgo excedido"""

    def __init__(self, risk_type: str, risk_level: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Risk threshold exceeded: {risk_type} ({risk_level})",
            error_code="RISK_THRESHOLD_EXCEEDED",
            extra={"risk_type": risk_type, "risk_level": risk_level}
        )


class AgentNotAvailableError(AINativeAPIException):
    """Agente no disponible"""

    def __init__(self, agent_name: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent '{agent_name}' is not available",
            error_code="AGENT_NOT_AVAILABLE",
            extra={"agent_name": agent_name}
        )


class DatabaseOperationError(AINativeAPIException):
    """Error en operación de base de datos"""

    def __init__(self, operation: str, details: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {operation}",
            error_code="DATABASE_ERROR",
            extra={"operation": operation, "details": details}
        )


class AuthenticationError(AINativeAPIException):
    """Error de autenticación"""

    def __init__(self, detail: str = "Invalid authentication credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_FAILED",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(AINativeAPIException):
    """Error de autorización"""

    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_FAILED"
        )


# FIX Cortez33: Add missing custom exceptions for consistent error handling

class TraceNotFoundError(AINativeAPIException):
    """Traza no encontrada"""

    def __init__(self, trace_id: str = None, session_id: str = None):
        if trace_id:
            detail = f"Trace '{trace_id}' not found"
            extra = {"trace_id": trace_id}
        elif session_id:
            detail = f"No traces found for session '{session_id}'"
            extra = {"session_id": session_id}
        else:
            detail = "Trace not found"
            extra = {}
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="TRACE_NOT_FOUND",
            extra=extra
        )


class ActivityNotFoundError(AINativeAPIException):
    """Actividad no encontrada"""

    def __init__(self, activity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity '{activity_id}' not found",
            error_code="ACTIVITY_NOT_FOUND",
            extra={"activity_id": activity_id}
        )


# FIX Cortez36: Added ExerciseNotFoundError for consistent error handling
class ExerciseNotFoundError(AINativeAPIException):
    """Ejercicio no encontrado"""

    def __init__(self, exercise_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejercicio '{exercise_id}' no encontrado",
            error_code="EXERCISE_NOT_FOUND",
            extra={"exercise_id": exercise_id}
        )


class EventNotFoundError(AINativeAPIException):
    """Evento no encontrado"""

    def __init__(self, event_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found",
            error_code="EVENT_NOT_FOUND",
            extra={"event_id": event_id}
        )


class GitTraceNotFoundError(AINativeAPIException):
    """Git trace no encontrado"""

    def __init__(self, trace_id: str = None, session_id: str = None):
        if trace_id:
            detail = f"Git trace '{trace_id}' not found"
            extra = {"git_trace_id": trace_id}
        elif session_id:
            detail = f"No git traces found for session '{session_id}'"
            extra = {"session_id": session_id}
        else:
            detail = "Git trace not found"
            extra = {}
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="GIT_TRACE_NOT_FOUND",
            extra=extra
        )


class InvalidUUIDError(AINativeAPIException):
    """UUID inválido"""

    def __init__(self, field_name: str, value: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Expected UUID format, got: {value[:50]}",
            error_code="INVALID_UUID_FORMAT",
            extra={"field": field_name, "value": value[:50]}
        )


# Cortez46: Additional custom exceptions for common HTTP patterns

class UserNotFoundError(AINativeAPIException):
    """Usuario no encontrado"""

    def __init__(self, user_id: str = None, email: str = None):
        if user_id:
            detail = f"User with ID '{user_id}' not found"
            extra = {"user_id": user_id}
        elif email:
            detail = f"User with email '{email}' not found"
            extra = {"email": email}
        else:
            detail = "User not found"
            extra = {}
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="USER_NOT_FOUND",
            extra=extra
        )


class UserInactiveError(AINativeAPIException):
    """Usuario inactivo"""

    def __init__(self, user_id: str = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact an administrator.",
            error_code="USER_INACTIVE",
            extra={"user_id": user_id} if user_id else {}
        )


class RoleRequiredError(AINativeAPIException):
    """Rol requerido no presente"""

    def __init__(self, required_role: str, user_roles: list = None):
        user_roles = user_roles or []
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{required_role.capitalize()} role required. Your roles: {', '.join(user_roles) or 'none'}",
            error_code="ROLE_REQUIRED",
            extra={"required_role": required_role, "user_roles": user_roles}
        )


class InvalidTokenError(AINativeAPIException):
    """Token inválido o expirado"""

    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_TOKEN",
            headers={"WWW-Authenticate": "Bearer"}
        )


class ReportNotFoundError(AINativeAPIException):
    """Reporte no encontrado"""

    def __init__(self, report_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
            error_code="REPORT_NOT_FOUND",
            extra={"report_id": report_id}
        )


class RiskAlertNotFoundError(AINativeAPIException):
    """Alerta de riesgo no encontrada"""

    def __init__(self, alert_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk alert '{alert_id}' not found",
            error_code="RISK_ALERT_NOT_FOUND",
            extra={"alert_id": alert_id}
        )


class SimulationNotFoundError(AINativeAPIException):
    """Simulación no encontrada"""

    def __init__(self, simulation_id: str, simulation_type: str = "simulation"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{simulation_type.capitalize()} '{simulation_id}' not found",
            error_code="SIMULATION_NOT_FOUND",
            extra={"simulation_id": simulation_id, "simulation_type": simulation_type}
        )


class ValidationError(AINativeAPIException):
    """Error de validación"""

    def __init__(self, detail: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            extra={"field": field} if field else {}
        )


class ExportError(AINativeAPIException):
    """Error de exportación"""

    def __init__(self, detail: str, export_format: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {detail}",
            error_code="EXPORT_ERROR",
            extra={"format": export_format} if export_format else {}
        )


class LLMServiceError(AINativeAPIException):
    """Error del servicio LLM"""

    def __init__(self, detail: str, provider: str = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {detail}",
            error_code="LLM_SERVICE_ERROR",
            extra={"provider": provider} if provider else {}
        )


class SubjectNotFoundError(AINativeAPIException):
    """Materia no encontrada"""

    def __init__(self, subject_code: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject_code}' not found",
            error_code="SUBJECT_NOT_FOUND",
            extra={"subject_code": subject_code}
        )


class EvaluationNotFoundError(AINativeAPIException):
    """Evaluación no encontrada"""

    def __init__(self, evaluation_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found",
            error_code="EVALUATION_NOT_FOUND",
            extra={"evaluation_id": evaluation_id}
        )


class RiskNotFoundError(AINativeAPIException):
    """Riesgo no encontrado"""

    def __init__(self, risk_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk '{risk_id}' not found",
            error_code="RISK_NOT_FOUND",
            extra={"risk_id": risk_id}
        )


# =============================================================================
# FIX Cortez52: Added Simulator-specific exceptions
# =============================================================================


class SimulatorNotSupportedError(AINativeAPIException):
    """Tipo de simulador no soportado"""

    def __init__(self, simulator_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Simulator type '{simulator_type}' is not supported",
            error_code="SIMULATOR_NOT_SUPPORTED",
            extra={"simulator_type": simulator_type}
        )


class SimulatorCreationError(AINativeAPIException):
    """Error al crear el simulador"""

    def __init__(self, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating simulator: {details}" if details else "Error creating simulator",
            error_code="SIMULATOR_CREATION_ERROR",
            extra={"details": details}
        )


class SimulatorInteractionError(AINativeAPIException):
    """Error en la interacción con el simulador"""

    def __init__(self, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing simulator interaction: {details}" if details else "Error processing simulator interaction",
            error_code="SIMULATOR_INTERACTION_ERROR",
            extra={"details": details}
        )


class EmptyPromptError(AINativeAPIException):
    """Prompt vacío"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El prompt no puede estar vacío",
            error_code="EMPTY_PROMPT"
        )


class SessionInactiveError(AINativeAPIException):
    """Sesión no está activa"""

    def __init__(self, session_id: str, current_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session '{session_id}' is not active (status: {current_status})",
            error_code="SESSION_INACTIVE",
            extra={"session_id": session_id, "status": current_status}
        )


class InterviewNotFoundError(AINativeAPIException):
    """Entrevista técnica no encontrada"""

    def __init__(self, interview_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found",
            error_code="INTERVIEW_NOT_FOUND",
            extra={"interview_id": interview_id}
        )


class IncidentNotFoundError(AINativeAPIException):
    """Incidente no encontrado"""

    def __init__(self, incident_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
            error_code="INCIDENT_NOT_FOUND",
            extra={"incident_id": incident_id}
        )


# =============================================================================
# FIX Cortez53: Additional custom exceptions for Git and validation
# =============================================================================


class GitSyncError(AINativeAPIException):
    """Error al sincronizar Git"""

    def __init__(self, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing Git commits: {details}" if details else "Error syncing Git commits",
            error_code="GIT_SYNC_ERROR",
            extra={"details": details}
        )


class InvalidRepoPathError(AINativeAPIException):
    """Ruta de repositorio inválida"""

    def __init__(self, path: str, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid repository path: {reason}",
            error_code="INVALID_REPO_PATH",
            extra={"path": path, "reason": reason}
        )


class UnauthorizedRepoAccessError(AINativeAPIException):
    """Acceso no autorizado a repositorio"""

    def __init__(self, path: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository path is outside allowed directories. Contact administrator.",
            error_code="UNAUTHORIZED_REPO_ACCESS",
            extra={"attempted_path": path}
        )


class MetricsAccessDeniedError(AINativeAPIException):
    """Acceso denegado a métricas"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Metrics endpoint requires valid API key or localhost access. "
                   "Set METRICS_API_KEY env var and pass via X-Metrics-Key header.",
            error_code="METRICS_ACCESS_DENIED"
        )


class TooManyStudentsError(AINativeAPIException):
    """Demasiados estudiantes para comparar"""

    def __init__(self, received: int, max_allowed: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many student_ids provided. Maximum allowed: {max_allowed}, received: {received}",
            error_code="TOO_MANY_STUDENTS",
            extra={"received": received, "max_allowed": max_allowed}
        )


class NoSessionsFoundError(AINativeAPIException):
    """No se encontraron sesiones"""

    def __init__(self, activity_id: str = None, student_ids: list = None):
        if activity_id and student_ids:
            detail = f"No sessions found for specified students in activity '{activity_id}'"
        elif activity_id:
            detail = f"No sessions found for activity '{activity_id}'"
        else:
            detail = "No sessions found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NO_SESSIONS_FOUND",
            extra={"activity_id": activity_id, "student_ids": student_ids}
        )


class LLMConfigurationError(AINativeAPIException):
    """Error de configuración del LLM"""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM configuration error: {detail}",
            error_code="LLM_CONFIGURATION_ERROR"
        )


class TrainingSessionNotFoundError(AINativeAPIException):
    """Sesión de entrenamiento no encontrada"""

    def __init__(self, session_id: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada o expirada",
            error_code="TRAINING_SESSION_NOT_FOUND",
            extra={"session_id": session_id} if session_id else {}
        )


class TrainingSessionAccessDeniedError(AINativeAPIException):
    """Acceso denegado a sesión de entrenamiento"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a esta sesión",
            error_code="TRAINING_SESSION_ACCESS_DENIED"
        )


class TrainingOperationError(AINativeAPIException):
    """Error en operación de entrenamiento"""

    def __init__(self, operation: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al {operation}",
            error_code="TRAINING_OPERATION_ERROR",
            extra={"operation": operation}
        )


# =============================================================================
# FIX Cortez53: Export and Reports exceptions
# =============================================================================


class NoDataFoundError(AINativeAPIException):
    """No se encontraron datos para los filtros especificados"""

    def __init__(self, filters: str = "specified filters"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found matching {filters}",
            error_code="NO_DATA_FOUND"
        )


class PrivacyValidationError(AINativeAPIException):
    """Error de validación de privacidad"""

    def __init__(self, errors: list, metrics: dict = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Privacy validation failed",
                "errors": errors,
                "metrics": metrics or {},
            },
            error_code="PRIVACY_VALIDATION_ERROR",
            extra={"errors": errors, "metrics": metrics}
        )


class StudentIdsRequiredError(AINativeAPIException):
    """Se requieren IDs de estudiantes"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="student_ids cannot be empty",
            error_code="STUDENT_IDS_REQUIRED"
        )


class InvalidPeriodError(AINativeAPIException):
    """Período inválido"""

    def __init__(self, message: str = "period_end must be after period_start"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="INVALID_PERIOD"
        )


class ReportGenerationError(AINativeAPIException):
    """Error al generar reporte"""

    def __init__(self, report_type: str, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating {report_type}: {details}" if details else f"Error generating {report_type}",
            error_code="REPORT_GENERATION_ERROR",
            extra={"report_type": report_type, "details": details}
        )


class ReportFileNotFoundError(AINativeAPIException):
    """Archivo de reporte no encontrado"""

    def __init__(self, file_path: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file not found: {file_path}",
            error_code="REPORT_FILE_NOT_FOUND",
            extra={"file_path": file_path}
        )


class InvalidAnalyticsPeriodError(AINativeAPIException):
    """Período de analytics inválido"""

    def __init__(self, period: str, valid_periods: list):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period '{period}'. Valid values: {', '.join(sorted(valid_periods))}",
            error_code="INVALID_ANALYTICS_PERIOD",
            extra={"period": period, "valid_periods": valid_periods}
        )


class RiskScanError(AINativeAPIException):
    """Error al escanear riesgos"""

    def __init__(self, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning for alerts: {details}" if details else "Error scanning for alerts",
            error_code="RISK_SCAN_ERROR",
            extra={"details": details}
        )


class AlertOperationError(AINativeAPIException):
    """Error en operación de alerta"""

    def __init__(self, operation: str, alert_id: str, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error {operation} alert: {details}" if details else f"Error {operation} alert",
            error_code="ALERT_OPERATION_ERROR",
            extra={"operation": operation, "alert_id": alert_id, "details": details}
        )


class RemediationPlanNotFoundError(AINativeAPIException):
    """Plan de remediación no encontrado"""

    def __init__(self, plan_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Remediation plan '{plan_id}' not found",
            error_code="REMEDIATION_PLAN_NOT_FOUND",
            extra={"plan_id": plan_id}
        )


class RemediationPlanError(AINativeAPIException):
    """Error en plan de remediación"""

    def __init__(self, operation: str, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error {operation} remediation plan: {details}" if details else f"Error {operation} remediation plan",
            error_code="REMEDIATION_PLAN_ERROR",
            extra={"operation": operation, "details": details}
        )


# =============================================================================
# FIX Cortez73 (HIGH-004): File management exceptions
# =============================================================================

class FileNotFoundError(AINativeAPIException):
    """Archivo no encontrado"""

    def __init__(self, file_id: str = "", path: str = ""):
        identifier = file_id or path or "unknown"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{identifier}' not found",
            error_code="FILE_NOT_FOUND",
            extra={"file_id": file_id, "path": path}
        )


class FileUploadError(AINativeAPIException):
    """Error al subir archivo"""

    def __init__(self, details: str = ""):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload error: {details}" if details else "File upload error",
            error_code="FILE_UPLOAD_ERROR",
            extra={"details": details}
        )


class FileAccessDeniedError(AINativeAPIException):
    """Acceso denegado al archivo"""

    def __init__(self, path: str = ""):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to file",
            error_code="FILE_ACCESS_DENIED",
            extra={"path": path}
        )


class FileStorageError(AINativeAPIException):
    """Error de almacenamiento de archivos"""

    def __init__(self, operation: str, details: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File storage error during {operation}: {details}" if details else f"File storage error during {operation}",
            error_code="FILE_STORAGE_ERROR",
            extra={"operation": operation, "details": details}
        )