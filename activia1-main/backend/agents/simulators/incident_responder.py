"""
Incident Responder Simulator (IR-IA) - Manages production incidents.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)
"""
from typing import Optional, Dict, Any, List
import logging

from .base import BaseSimulator, SimuladorType

logger = logging.getLogger(__name__)


class IncidentResponderSimulator(BaseSimulator):
    """
    Simulates an Incident Responder role.

    Evaluates:
    - Systematic diagnosis
    - Prioritization under pressure
    - Documentation quality
    - Crisis management
    """

    ROLE_NAME = "Senior DevOps Incident Responder"
    SYSTEM_PROMPT = """Eres un ingeniero DevOps senior gestionando un incidente en produccion.
Tu rol es hacer triage, diagnosticar el problema, priorizar acciones bajo presion,
coordinar hotfixes, y documentar post-mortem.
Debes ser sistematico, priorizar por impacto, y requerir evidencia (logs, metricas).
Evaluas: diagnostico sistematico, priorizacion bajo presion, documentacion, manejo de crisis."""

    COMPETENCIES = [
        "diagnostico_sistematico",
        "priorizacion",
        "documentacion",
        "manejo_presion"
    ]
    EXPECTS = ["diagnostico", "plan_accion", "hotfix_propuesto", "post_mortem"]

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle interaction as Incident Responder."""
        validation_error = self.validate_input(student_input)
        if validation_error:
            return validation_error

        context = context or {}

        logger.info(
            "Incident Responder processing input",
            extra={
                "flow_id": self.flow_id,
                "input_length": len(student_input),
                "session_id": session_id,
            },
        )

        if self.llm_provider:
            return await self._generate_llm_response(
                student_input=student_input,
                context=context,
                session_id=session_id
            )

        return self.get_fallback_response()

    def get_fallback_response(self) -> Dict[str, Any]:
        """Return fallback response when LLM is unavailable."""
        return {
            "message": """
INCIDENTE CRITICO EN PRODUCCION

**Severidad**: P1 (critico)
**Impacto**: El servidor de API esta caido. 5000 usuarios afectados.
**Tiempo de inactividad**: 12 minutos

**Sintomas**:
- HTTP 503 Service Unavailable
- Logs muestran: "OutOfMemoryError: Java heap space"
- CPU al 100% en todos los nodos
- Base de datos respondiendo normalmente

**Tu turno**:
1. Cual es tu hipotesis inicial?
2. Que comandos ejecutarias para diagnosticar?
3. Cual es tu plan de accion inmediato?
4. Como prevenimos que vuelva a ocurrir?

Necesito respuestas en <5 minutos. El CEO esta preguntando cuando volvemos online.
            """.strip(),
            "role": "incident_responder",
            "expects": self.EXPECTS,
            "metadata": {
                "competencies_evaluated": self.COMPETENCIES,
                "incident_severity": "P1",
                "time_pressure": "high"
            }
        }

    async def generar_incidente(
        self,
        tipo_incidente: str,
        severidad: str = "HIGH"
    ) -> Dict[str, Any]:
        """
        Generate a realistic production incident scenario.

        Args:
            tipo_incidente: API_ERROR, PERFORMANCE, SECURITY, DATABASE, DEPLOYMENT
            severidad: LOW, MEDIUM, HIGH, CRITICAL

        Returns:
            Dict with description, logs, metrics
        """
        if not self.llm_provider:
            return self._get_fallback_incident(tipo_incidente, severidad)

        try:
            from ...llm.base import LLMMessage, LLMRole
            import json

            system_prompt = f"""Eres un sistema de monitoreo generando un reporte de incidente en produccion.

Tipo de incidente: {tipo_incidente}
Severidad: {severidad}

Genera un escenario REALISTA de incidente que incluya:

1. **Descripcion del incidente** (2-3 lineas):
   - Que esta fallando
   - Impacto en usuarios/negocio
   - Tiempo de inactividad aproximado

2. **Logs simulados** (5-8 lineas de logs realistas):
   - Timestamps
   - Niveles de log (ERROR, WARN, INFO)
   - Stack traces si aplica
   - Mensajes de error especificos

3. **Metricas simuladas** (JSON):
   - cpu_usage_percent (0-100)
   - memory_usage_percent (0-100)
   - requests_per_second (numero)
   - error_rate_percent (0-100)
   - response_time_ms (numero)

Responde SOLO en formato JSON:
{{
  "description": "descripcion del incidente",
  "logs": "logs simulados del sistema\\n...",
  "metrics": {{
    "cpu_usage_percent": 0-100,
    "memory_usage_percent": 0-100,
    "requests_per_second": numero,
    "error_rate_percent": 0-100,
    "response_time_ms": numero
  }}
}}"""

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content=f"Genera incidente {tipo_incidente} de severidad {severidad}")
            ]

            response = await self.llm_provider.generate(
                messages=messages,
                temperature=0.7,
                max_tokens=600,
                is_code_analysis=False
            )

            try:
                incident_data = json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse incident JSON from LLM")
                return self._get_fallback_incident(tipo_incidente, severidad)

            logger.info(
                "Incident generated",
                extra={"tipo": tipo_incidente, "severidad": severidad}
            )

            return incident_data

        except Exception as e:
            logger.error("Error generating incident: %s", e, exc_info=True)
            return self._get_fallback_incident(tipo_incidente, severidad)

    def _get_fallback_incident(self, tipo_incidente: str, severidad: str) -> Dict[str, Any]:
        """Predefined incidents as fallback."""
        incidents = {
            "API_ERROR": {
                "description": "API endpoint /users devuelve HTTP 500. 3,500 usuarios afectados. Tiempo de inactividad: 8 minutos.",
                "logs": """[2025-11-21 14:32:15] ERROR - NullPointerException at UserController.getUser()
[2025-11-21 14:32:16] ERROR - Failed to retrieve user from database
[2025-11-21 14:32:17] WARN  - Connection pool exhausted, waiting for available connection
[2025-11-21 14:32:18] ERROR - Timeout waiting for database connection after 5000ms
[2025-11-21 14:32:19] ERROR - Circuit breaker OPEN for database connection pool""",
                "metrics": {
                    "cpu_usage_percent": 45,
                    "memory_usage_percent": 78,
                    "requests_per_second": 1200,
                    "error_rate_percent": 85,
                    "response_time_ms": 8500
                }
            },
            "PERFORMANCE": {
                "description": "Degradacion severa de performance. Tiempos de respuesta >10s. 8,000 usuarios afectados.",
                "logs": """[2025-11-21 14:45:22] WARN  - Slow query detected: SELECT * FROM orders WHERE... (12,345ms)
[2025-11-21 14:45:23] ERROR - Request timeout after 10000ms
[2025-11-21 14:45:24] WARN  - Database connection pool at 95% capacity
[2025-11-21 14:45:25] ERROR - OutOfMemoryError: Java heap space
[2025-11-21 14:45:26] WARN  - GC overhead limit exceeded""",
                "metrics": {
                    "cpu_usage_percent": 98,
                    "memory_usage_percent": 95,
                    "requests_per_second": 450,
                    "error_rate_percent": 12,
                    "response_time_ms": 15000
                }
            },
            "SECURITY": {
                "description": "CRITICO: Posible ataque de SQL injection detectado. Firewall bloqueo 15,000 requests maliciosos en 5 minutos.",
                "logs": """[2025-11-21 15:10:01] CRITICAL - SQL injection attempt detected from IP 45.123.67.89
[2025-11-21 15:10:02] WARN  - Malicious payload: ' OR '1'='1' --
[2025-11-21 15:10:03] ERROR - Authentication bypass attempt blocked
[2025-11-21 15:10:04] CRITICAL - Rate limit exceeded: 5000 requests/minute from same IP
[2025-11-21 15:10:05] INFO  - Firewall rule activated, IP 45.123.67.89 blocked""",
                "metrics": {
                    "cpu_usage_percent": 67,
                    "memory_usage_percent": 55,
                    "requests_per_second": 8500,
                    "error_rate_percent": 3,
                    "response_time_ms": 450
                }
            },
            "DATABASE": {
                "description": "Base de datos principal no responde. Conexiones timeout. Toda la aplicacion afectada.",
                "logs": """[2025-11-21 16:20:10] CRITICAL - Database connection failed: Connection timed out
[2025-11-21 16:20:11] ERROR - Unable to acquire JDBC Connection
[2025-11-21 16:20:12] WARN  - Replica lag: 45 seconds behind master
[2025-11-21 16:20:13] ERROR - Too many connections (max_connections = 500)
[2025-11-21 16:20:14] CRITICAL - Master database unreachable, attempting failover to replica""",
                "metrics": {
                    "cpu_usage_percent": 15,
                    "memory_usage_percent": 45,
                    "requests_per_second": 50,
                    "error_rate_percent": 100,
                    "response_time_ms": 30000
                }
            },
            "DEPLOYMENT": {
                "description": "Deployment fallo. Rollback necesario. Nuevo release tiene breaking changes no detectados.",
                "logs": """[2025-11-21 17:05:30] ERROR - Deployment v2.5.0 failed health check
[2025-11-21 17:05:31] CRITICAL - NoSuchMethodError: UserService.authenticate(String, String)
[2025-11-21 17:05:32] ERROR - Incompatible API version detected
[2025-11-21 17:05:33] WARN  - Rolling back to previous version v2.4.9
[2025-11-21 17:05:34] INFO  - Rollback initiated, ETA 3 minutes""",
                "metrics": {
                    "cpu_usage_percent": 32,
                    "memory_usage_percent": 60,
                    "requests_per_second": 200,
                    "error_rate_percent": 78,
                    "response_time_ms": 6500
                }
            }
        }

        return incidents.get(tipo_incidente, incidents["API_ERROR"])

    async def evaluar_resolucion_incidente(
        self,
        proceso_diagnostico: List[Dict[str, Any]],
        solucion: str,
        causa_raiz: str,
        post_mortem: str
    ) -> Dict[str, Any]:
        """
        Evaluate student's incident resolution.

        Returns:
            Dict with overall_score and dimension scores
        """
        if not self.llm_provider:
            return self._evaluate_incident_heuristic(
                proceso_diagnostico, solucion, causa_raiz, post_mortem
            )

        try:
            from ...llm.base import LLMMessage, LLMRole
            import json

            system_prompt = f"""Eres un ingeniero DevOps senior evaluando la resolucion de un incidente.

PROCESO DE DIAGNOSTICO ({len(proceso_diagnostico)} pasos):
{self._format_diagnosis_process(proceso_diagnostico)}

SOLUCION PROPUESTA:
{solucion}

CAUSA RAIZ IDENTIFICADA:
{causa_raiz}

POST-MORTEM:
{post_mortem}

EVALUA en estas dimensiones (0.0-1.0):

1. **Diagnostico sistematico**: Siguio un proceso logico de triage y diagnostico?
2. **Priorizacion**: Priorizo correctamente las acciones por impacto?
3. **Calidad de documentacion**: El post-mortem es completo y util?
4. **Claridad de comunicacion**: Se expreso de forma clara y profesional?

Responde SOLO en formato JSON:
{{
  "diagnosis_systematic": 0.0-1.0,
  "prioritization": 0.0-1.0,
  "documentation_quality": 0.0-1.0,
  "communication_clarity": 0.0-1.0,
  "feedback": "Feedback constructivo (3-4 oraciones)"
}}"""

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content="Evalua la resolucion del incidente")
            ]

            response = await self.llm_provider.generate(
                messages=messages,
                temperature=0.3,
                max_tokens=500,
                is_code_analysis=False
            )

            try:
                evaluation = json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse incident evaluation JSON from LLM")
                return self._evaluate_incident_heuristic(
                    proceso_diagnostico, solucion, causa_raiz, post_mortem
                )

            # Calculate overall score
            overall_score = sum([
                evaluation.get("diagnosis_systematic", 0.5) * 0.3,
                evaluation.get("prioritization", 0.5) * 0.2,
                evaluation.get("documentation_quality", 0.5) * 0.25,
                evaluation.get("communication_clarity", 0.5) * 0.25
            ])

            evaluation["overall_score"] = round(overall_score, 2)

            logger.info(
                "Incident resolution evaluated",
                extra={"overall_score": overall_score, "num_steps": len(proceso_diagnostico)}
            )

            return evaluation

        except Exception as e:
            logger.error("Error evaluating incident resolution: %s", e, exc_info=True)
            return self._evaluate_incident_heuristic(
                proceso_diagnostico, solucion, causa_raiz, post_mortem
            )

    def _format_diagnosis_process(self, proceso: List[Dict[str, Any]]) -> str:
        """Format diagnosis process for LLM."""
        formatted = []
        for i, step in enumerate(proceso, 1):
            action = step.get("action", "")
            finding = step.get("finding", "N/A")
            formatted.append(f"{i}. {action}\n   Hallazgo: {finding}")
        return "\n".join(formatted)

    def _evaluate_incident_heuristic(
        self,
        proceso_diagnostico: List[Dict[str, Any]],
        solucion: str,
        causa_raiz: str,
        post_mortem: str
    ) -> Dict[str, Any]:
        """Simple heuristic evaluation as fallback."""
        num_steps = len(proceso_diagnostico)
        solution_length = len(solucion.split())
        postmortem_length = len(post_mortem.split())

        diagnosis_systematic = min(num_steps / 5.0, 1.0) if num_steps > 0 else 0.2
        prioritization = 0.7 if num_steps >= 3 else 0.4
        documentation_quality = min(postmortem_length / 100.0, 1.0) if postmortem_length > 50 else 0.3
        communication_clarity = min(solution_length / 50.0, 1.0) if solution_length > 20 else 0.4

        overall_score = (
            diagnosis_systematic * 0.3 +
            prioritization * 0.2 +
            documentation_quality * 0.25 +
            communication_clarity * 0.25
        )

        return {
            "overall_score": round(overall_score, 2),
            "diagnosis_systematic": round(diagnosis_systematic, 2),
            "prioritization": round(prioritization, 2),
            "documentation_quality": round(documentation_quality, 2),
            "communication_clarity": round(communication_clarity, 2),
            "feedback": f"Incidente resuelto con {num_steps} pasos de diagnostico. Para evaluacion completa, configure un LLM provider."
        }
