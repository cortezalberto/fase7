"""
DevSecOps Simulator (DSO-IA) - Security analyst for code auditing.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)
"""
from typing import Optional, Dict, Any, List
import logging
import uuid

from .base import BaseSimulator, SimuladorType

logger = logging.getLogger(__name__)


class DevSecOpsSimulator(BaseSimulator):
    """
    Simulates a DevSecOps Security Analyst role.

    Evaluates:
    - Security awareness
    - Vulnerability analysis
    - Risk management
    - Compliance
    """

    ROLE_NAME = "DevSecOps Security Analyst"
    SYSTEM_PROMPT = """Eres un analista de seguridad DevSecOps experimentado.
Tu rol es auditar codigo, detectar vulnerabilidades (SQL injection, XSS, CSRF, etc.),
analizar dependencias obsoletas, y exigir planes de remediacion con timeline.
Debes ser directo, enfocarte en riesgos criticos, y pedir evidencia de mitigacion.
Evaluas: seguridad, analisis de vulnerabilidades, gestion de riesgo, cumplimiento normativo."""

    COMPETENCIES = [
        "seguridad",
        "analisis_vulnerabilidades",
        "gestion_riesgo",
        "cumplimiento"
    ]
    EXPECTS = ["plan_remediacion", "analisis_riesgo", "estrategia_testing"]

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle interaction as DevSecOps analyst."""
        validation_error = self.validate_input(student_input)
        if validation_error:
            return validation_error

        context = context or {}

        logger.info(
            "DevSecOps processing input",
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
He detectado varias vulnerabilidades en tu codigo:

1. **SQL Injection** en linea 45: query string no parametrizada
2. **XSS** en linea 78: input de usuario sin sanitizar
3. **Dependencia vulnerable**: lodash 4.17.15 (CVE-2020-8203)

Como pensas remediar estos issues? Necesito:
- Plan de mitigacion
- Timeline
- Tests que validen el fix
            """.strip(),
            "role": "devsecops",
            "expects": self.EXPECTS,
            "metadata": {
                "competencies_evaluated": self.COMPETENCIES
            }
        }

    def auditar_seguridad(self, codigo: str, lenguaje: str) -> Dict[str, Any]:
        """
        Audit code for security vulnerabilities.

        Args:
            codigo: Source code to audit
            lenguaje: Programming language (python, java, etc.)

        Returns:
            Dict with audit_id, vulnerabilities, security_score, etc.
        """
        vulnerabilities_found = []

        # Simple pattern detection (in production use real static analysis)
        if "eval(" in codigo or "exec(" in codigo:
            vulnerabilities_found.append({
                "severity": "CRITICAL",
                "vulnerability_type": "CODE_INJECTION",
                "description": "Uso de eval/exec permite ejecucion de codigo arbitrario",
                "recommendation": "Nunca uses eval/exec con input de usuario"
            })

        if "SELECT * FROM" in codigo and "%" in codigo:
            vulnerabilities_found.append({
                "severity": "HIGH",
                "vulnerability_type": "SQL_INJECTION",
                "description": "Posible SQL injection por concatenacion de strings",
                "recommendation": "Usa queries parametrizadas"
            })

        if "password" in codigo.lower() and ("=" in codigo or ":" in codigo):
            vulnerabilities_found.append({
                "severity": "CRITICAL",
                "vulnerability_type": "HARDCODED_CREDENTIALS",
                "description": "Credenciales hardcodeadas en el codigo",
                "recommendation": "Usa variables de entorno o secret management"
            })

        total = len(vulnerabilities_found)
        critical = sum(1 for v in vulnerabilities_found if v.get("severity") == "CRITICAL")
        high = sum(1 for v in vulnerabilities_found if v.get("severity") == "HIGH")

        security_score = max(10.0 - (critical * 3 + high * 2), 0.0)

        return {
            "audit_id": str(uuid.uuid4()),
            "total_vulnerabilities": total,
            "critical_count": critical,
            "high_count": high,
            "medium_count": 0,
            "low_count": 0,
            "vulnerabilities": vulnerabilities_found,
            "security_score": security_score,
            "recommendations": ["Revisar todos los critical y high priority issues"],
            "owasp_compliant": critical == 0 and high == 0
        }
