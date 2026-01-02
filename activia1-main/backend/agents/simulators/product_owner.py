"""
Product Owner Simulator (PO-IA) - Questions technical proposals.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)
"""
from typing import Optional, Dict, Any, List
import logging

from .base import BaseSimulator, SimuladorType

logger = logging.getLogger(__name__)


class ProductOwnerSimulator(BaseSimulator):
    """
    Simulates a Product Owner role.

    Evaluates:
    - Technical communication
    - Requirements analysis
    - Prioritization
    - Decision justification
    """

    ROLE_NAME = "Product Owner"
    SYSTEM_PROMPT = """Eres un Product Owner experimentado de una empresa de software.
Tu rol es cuestionar propuestas tecnicas, pedir criterios de aceptacion claros,
evaluar el valor para el usuario final, y priorizar el backlog por ROI.
Debes ser exigente pero constructivo. Pide justificaciones tecnicas solidas.
Evaluas: comunicacion tecnica, analisis de requisitos, priorizacion, justificacion de decisiones."""

    COMPETENCIES = [
        "comunicacion_tecnica",
        "analisis_requisitos",
        "priorizacion",
        "justificacion_decisiones"
    ]
    EXPECTS = [
        "criterios_aceptacion",
        "justificacion_tecnica",
        "analisis_alternativas"
    ]

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle interaction as Product Owner."""
        # Validate input
        validation_error = self.validate_input(student_input)
        if validation_error:
            return validation_error

        context = context or {}

        logger.info(
            "Product Owner processing input",
            extra={
                "flow_id": self.flow_id,
                "input_length": len(student_input),
                "session_id": session_id,
            },
        )

        # Use LLM if available
        if self.llm_provider:
            return await self._generate_llm_response(
                student_input=student_input,
                context=context,
                session_id=session_id
            )

        # Fallback response
        return self.get_fallback_response()

    def get_fallback_response(self) -> Dict[str, Any]:
        """Return fallback response when LLM is unavailable."""
        return {
            "message": """
Como Product Owner, necesito que me aclares algunos puntos:

1. Cuales son los criterios de aceptacion especificos para esta funcionalidad?
2. Como pensas que esto agrega valor al usuario final?
3. Que alternativas consideraste y por que elegiste este enfoque?
4. Cual es el impacto si postergamos esta funcionalidad un sprint?

Necesito justificaciones tecnicas solidas para priorizar esto en el backlog.
            """.strip(),
            "role": "product_owner",
            "expects": self.EXPECTS,
            "metadata": {
                "competencies_evaluated": self.COMPETENCIES
            }
        }
