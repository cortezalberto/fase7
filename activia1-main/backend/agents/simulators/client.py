"""
Client Simulator (CX-IA) - Non-technical client with ambiguous requirements.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)
"""
from typing import Optional, Dict, Any, List
import logging

from .base import BaseSimulator, SimuladorType

logger = logging.getLogger(__name__)


class ClientSimulator(BaseSimulator):
    """
    Simulates a Non-technical Client role.

    Evaluates:
    - Requirements elicitation
    - Negotiation skills
    - Empathy
    - Expectation management
    """

    ROLE_NAME = "Non-technical Client"
    SYSTEM_PROMPT = """Eres un cliente no tecnico con una idea de negocio.
Tus requisitos son ambiguos, a veces contradictorios, y cambias de opinion.
El estudiante debe hacer elicitacion efectiva, negociar prioridades, y gestionar expectativas.
No entiendes jerga tecnica. Valoras explicaciones simples y justificaciones de negocio.
Evaluas: elicitacion de requisitos, negociacion, empatia, gestion de expectativas."""

    COMPETENCIES = [
        "elicitacion_requisitos",
        "negociacion",
        "empatia",
        "gestion_expectativas"
    ]
    EXPECTS = ["clarificacion_requisitos", "propuesta_alternativas", "justificacion_negocio"]

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle interaction as Client."""
        validation_error = self.validate_input(student_input)
        if validation_error:
            return validation_error

        context = context or {}

        logger.info(
            "Client processing input",
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
Hola, necesito una app "como Uber pero para delivery de comida".

Quiero que:
- Los usuarios puedan pedir comida
- Los restaurantes reciban los pedidos
- Los repartidores... no se, algo con GPS
- Pagos con tarjeta, pero tambien efectivo
- Notificaciones cuando llegue el pedido

Ah, y tiene que estar lista en 2 semanas porque mi cunado dijo que puede conseguir inversores.

Cuanto sale? Podes empezar ya?
            """.strip(),
            "role": "client",
            "expects": self.EXPECTS,
            "metadata": {
                "competencies_evaluated": self.COMPETENCIES,
                "requirements_clarity": "low",
                "technical_knowledge": "none"
            }
        }

    def generar_requerimientos_cliente(self, tipo_proyecto: str) -> Dict[str, Any]:
        """
        Generate ambiguous client requirements.

        Args:
            tipo_proyecto: Type of project the client wants

        Returns:
            Dict with requirements and additional requirements
        """
        return {
            "requirements": f"Necesito una app de {tipo_proyecto} que sea facil de usar y rapida. Quiero que los usuarios puedan hacer... bueno, las cosas tipicas de este tipo de apps. Cuanto sale?",
            "additional": [
                "Tambien querria notificaciones push",
                "Y que funcione offline",
                "Ah, y tiene que ser en espanol e ingles"
            ]
        }

    def responder_clarificacion(self, pregunta: str) -> Dict[str, Any]:
        """
        Respond to student's clarification question.

        Returns:
            Dict with answer, new_requirements, soft_skills_evaluation
        """
        return {
            "answer": "Buena pregunta. No habia pensado en eso. Si, definitivamente necesitamos esa funcionalidad.",
            "new_requirements": ["Requisito adicional descubierto"],
            "soft_skills_evaluation": {
                "empathy": 0.8,
                "clarity": 0.75,
                "professionalism": 0.85
            }
        }
