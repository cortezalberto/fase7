"""
Simulators Package - Professional role simulators (S-IA-X).

Cortez42: Refactored from monolithic simulators.py (1,638 lines)

This package provides modular, strategy-based simulators while maintaining
full backward compatibility with existing code.

Organization:
- base.py: SimuladorType enum and BaseSimulator abstract class
- factory.py: SimulatorFactory for creating simulator instances
- product_owner.py: ProductOwnerSimulator (PO-IA)
- scrum_master.py: ScrumMasterSimulator (SM-IA)
- tech_interviewer.py: TechInterviewerSimulator (IT-IA)
- incident_responder.py: IncidentResponderSimulator (IR-IA)
- devsecops.py: DevSecOpsSimulator (DSO-IA)
- client.py: ClientSimulator (CX-IA)

Usage (backward compatible):
    # Old import still works (via SimuladorProfesionalAgent wrapper):
    from backend.agents.simulators import SimuladorProfesionalAgent, SimuladorType

    # New import also works:
    from backend.agents.simulators import SimulatorFactory, SimuladorType
    simulator = SimulatorFactory.create(SimuladorType.PRODUCT_OWNER, llm_provider)
"""

# Base types
from .base import SimuladorType, BaseSimulator

# Factory
from .factory import SimulatorFactory

# Individual simulators (for direct import)
from .product_owner import ProductOwnerSimulator
from .scrum_master import ScrumMasterSimulator
from .tech_interviewer import TechInterviewerSimulator
from .incident_responder import IncidentResponderSimulator
from .devsecops import DevSecOpsSimulator
from .client import ClientSimulator

# Backward compatible wrapper
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SimuladorProfesionalAgent:
    """
    Backward-compatible wrapper for SimulatorFactory.

    This class maintains the original API while delegating to the
    new strategy-based simulators.

    S-IA-X: Simuladores Profesionales

    Funciones:
    1. Crear condiciones situadas de práctica profesional
    2. Desarrollar competencias transversales
    3. Entrenar interacción humano-IA contextualizada
    4. Modelar decisiones profesionales con trazabilidad
    5. Generar evidencia para evaluación formativa
    """

    def __init__(
        self,
        simulator_type: SimuladorType,
        llm_provider=None,
        trace_repo=None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.simulator_type = simulator_type
        self.llm_provider = llm_provider
        self.trace_repo = trace_repo
        self.config = config or {}
        self.context = {}
        self.flow_id = self.config.get("flow_id")

        # Create the actual simulator using the factory
        self._simulator = SimulatorFactory.create(
            simulator_type=simulator_type,
            llm_provider=llm_provider,
            trace_repo=trace_repo,
            config=config
        )

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Interact with the simulator (delegates to strategy).

        SPRINT 4: If llm_provider is available, uses dynamic responses.
        Otherwise, uses predefined responses (fallback for testing).
        """
        try:
            return await self._simulator.interact(student_input, context, session_id)
        except Exception as e:
            logger.error(
                "Critical error in simulator interact: %s: %s",
                type(e).__name__, e, exc_info=True
            )
            return {
                "message": "Disculpa, tuve un problema tecnico. Por favor, intenta nuevamente o reformula tu mensaje.",
                "role": self.simulator_type.value if self.simulator_type else "unknown",
                "expects": ["retry"],
                "metadata": {
                    "error": "critical_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            }

    # ========================================================================
    # Backward-compatible methods (delegate to specialized simulators)
    # ========================================================================

    async def generar_pregunta_entrevista(
        self,
        tipo_entrevista: str,
        dificultad: str = "MEDIUM",
        contexto: str = ""
    ) -> str:
        """Generate interview question (IT-IA)."""
        if isinstance(self._simulator, TechInterviewerSimulator):
            return await self._simulator.generar_pregunta_entrevista(
                tipo_entrevista, dificultad, contexto
            )
        return "Este metodo solo esta disponible para el simulador Tech Interviewer."

    async def evaluar_respuesta_entrevista(
        self,
        pregunta: str,
        respuesta: str,
        tipo_entrevista: str
    ) -> Dict[str, Any]:
        """Evaluate interview response (IT-IA)."""
        if isinstance(self._simulator, TechInterviewerSimulator):
            return await self._simulator.evaluar_respuesta_entrevista(
                pregunta, respuesta, tipo_entrevista
            )
        return {"error": "Este metodo solo esta disponible para el simulador Tech Interviewer."}

    async def generar_evaluacion_entrevista(
        self,
        preguntas: list,
        respuestas: list,
        tipo_entrevista: str
    ) -> Dict[str, Any]:
        """Generate final interview evaluation (IT-IA)."""
        if isinstance(self._simulator, TechInterviewerSimulator):
            return await self._simulator.generar_evaluacion_entrevista(
                preguntas, respuestas, tipo_entrevista
            )
        return {"error": "Este metodo solo esta disponible para el simulador Tech Interviewer."}

    async def generar_incidente(
        self,
        tipo_incidente: str,
        severidad: str = "HIGH"
    ) -> Dict[str, Any]:
        """Generate incident scenario (IR-IA)."""
        if isinstance(self._simulator, IncidentResponderSimulator):
            return await self._simulator.generar_incidente(tipo_incidente, severidad)
        return {"error": "Este metodo solo esta disponible para el simulador Incident Responder."}

    async def evaluar_resolucion_incidente(
        self,
        proceso_diagnostico: list,
        solucion: str,
        causa_raiz: str,
        post_mortem: str
    ) -> Dict[str, Any]:
        """Evaluate incident resolution (IR-IA)."""
        if isinstance(self._simulator, IncidentResponderSimulator):
            return await self._simulator.evaluar_resolucion_incidente(
                proceso_diagnostico, solucion, causa_raiz, post_mortem
            )
        return {"error": "Este metodo solo esta disponible para el simulador Incident Responder."}

    def procesar_daily_standup(
        self,
        que_hizo_ayer: str,
        que_hara_hoy: str,
        impedimentos: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process daily standup (SM-IA)."""
        if isinstance(self._simulator, ScrumMasterSimulator):
            return self._simulator.procesar_daily_standup(
                que_hizo_ayer, que_hara_hoy, impedimentos
            )
        return {"error": "Este metodo solo esta disponible para el simulador Scrum Master."}

    def generar_requerimientos_cliente(self, tipo_proyecto: str) -> Dict[str, Any]:
        """Generate client requirements (CX-IA)."""
        if isinstance(self._simulator, ClientSimulator):
            return self._simulator.generar_requerimientos_cliente(tipo_proyecto)
        return {"error": "Este metodo solo esta disponible para el simulador Client."}

    def responder_clarificacion(self, pregunta: str) -> Dict[str, Any]:
        """Respond to clarification question (CX-IA)."""
        if isinstance(self._simulator, ClientSimulator):
            return self._simulator.responder_clarificacion(pregunta)
        return {"error": "Este metodo solo esta disponible para el simulador Client."}

    def auditar_seguridad(self, codigo: str, lenguaje: str) -> Dict[str, Any]:
        """Audit code for security (DSO-IA)."""
        if isinstance(self._simulator, DevSecOpsSimulator):
            return self._simulator.auditar_seguridad(codigo, lenguaje)
        return {"error": "Este metodo solo esta disponible para el simulador DevSecOps."}


__all__ = [
    # Types
    "SimuladorType",
    "BaseSimulator",
    # Factory
    "SimulatorFactory",
    # Individual simulators
    "ProductOwnerSimulator",
    "ScrumMasterSimulator",
    "TechInterviewerSimulator",
    "IncidentResponderSimulator",
    "DevSecOpsSimulator",
    "ClientSimulator",
    # Backward compatible
    "SimuladorProfesionalAgent",
]
