"""
Scrum Master Simulator (SM-IA) - Facilitates agile ceremonies.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)
"""
from typing import Optional, Dict, Any, List
import logging

from .base import BaseSimulator, SimuladorType

logger = logging.getLogger(__name__)


class ScrumMasterSimulator(BaseSimulator):
    """
    Simulates a Scrum Master role.

    Evaluates:
    - Time management
    - Communication
    - Impediment identification
    - Self-organization
    """

    ROLE_NAME = "Scrum Master"
    SYSTEM_PROMPT = """Eres un Scrum Master certificado facilitando ceremonias agiles.
Tu rol es hacer daily standups, identificar impedimentos, ayudar al equipo a auto-organizarse,
y mejorar procesos. Debes ser empatico pero directo cuando hay problemas de estimacion o bloqueos.
Evaluas: gestion de tiempo, comunicacion, identificacion de impedimentos, auto-organizacion."""

    COMPETENCIES = [
        "gestion_tiempo",
        "comunicacion",
        "identificacion_impedimentos",
        "auto_organizacion"
    ]
    EXPECTS = ["status_update", "impediments", "plan"]

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle interaction as Scrum Master."""
        validation_error = self.validate_input(student_input)
        if validation_error:
            return validation_error

        context = context or {}

        logger.info(
            "Scrum Master processing input",
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
En nuestro daily:

1. Que lograste ayer?
2. Que vas a hacer hoy?
3. Hay algun impedimento que te este bloqueando?

Noto que tu estimacion original era de 3 puntos y llevas 5 dias. Que esta
pasando? Necesitamos re-estimar o hay deuda tecnica no considerada?
            """.strip(),
            "role": "scrum_master",
            "expects": self.EXPECTS,
            "metadata": {
                "competencies_evaluated": self.COMPETENCIES
            }
        }

    def procesar_daily_standup(
        self,
        que_hizo_ayer: str,
        que_hara_hoy: str,
        impedimentos: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process Daily Standup participation.

        Returns:
            Dict with feedback, questions, detected_issues, suggestions
        """
        response = {
            "feedback": "Gracias por tu actualizacion. Veo progreso en tus tareas.",
            "questions": [],
            "detected_issues": [],
            "suggestions": []
        }

        if impedimentos:
            response["questions"].append("Que apoyo necesitas para remover ese impedimento?")
            response["detected_issues"].append("Impedimento reportado")

        if len(que_hizo_ayer.split()) < 10:
            response["suggestions"].append("Se mas especifico en tu reporte de tareas completadas")

        return response
