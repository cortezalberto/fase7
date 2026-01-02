"""
Simulator Factory - Creates appropriate simulator based on type.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)

Uses Strategy Pattern to instantiate the correct simulator class.
"""
from typing import Optional, Dict, Any
import logging

from .base import SimuladorType, BaseSimulator
from .product_owner import ProductOwnerSimulator
from .scrum_master import ScrumMasterSimulator
from .tech_interviewer import TechInterviewerSimulator
from .incident_responder import IncidentResponderSimulator
from .devsecops import DevSecOpsSimulator
from .client import ClientSimulator

logger = logging.getLogger(__name__)


class SimulatorFactory:
    """
    Factory for creating simulator instances.

    Uses Strategy Pattern - each simulator type has its own class
    implementing the BaseSimulator interface.
    """

    # Registry mapping simulator types to their classes
    _simulators = {
        SimuladorType.PRODUCT_OWNER: ProductOwnerSimulator,
        SimuladorType.SCRUM_MASTER: ScrumMasterSimulator,
        SimuladorType.TECH_INTERVIEWER: TechInterviewerSimulator,
        SimuladorType.INCIDENT_RESPONDER: IncidentResponderSimulator,
        SimuladorType.DEVSECOPS: DevSecOpsSimulator,
        SimuladorType.CLIENT: ClientSimulator,
        # V2 simulators - to be implemented
        # SimuladorType.SENIOR_DEV: SeniorDevSimulator,
        # SimuladorType.QA_ENGINEER: QAEngineerSimulator,
        # SimuladorType.SECURITY_AUDITOR: SecurityAuditorSimulator,
        # SimuladorType.TECH_LEAD: TechLeadSimulator,
        # SimuladorType.DEMANDING_CLIENT: DemandingClientSimulator,
    }

    @classmethod
    def create(
        cls,
        simulator_type: SimuladorType,
        llm_provider=None,
        trace_repo=None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseSimulator:
        """
        Create a simulator instance of the specified type.

        Args:
            simulator_type: Type of simulator to create
            llm_provider: LLM provider for dynamic responses
            trace_repo: Repository for loading conversation history
            config: Additional configuration options

        Returns:
            BaseSimulator instance

        Raises:
            ValueError: If simulator type is not supported
        """
        simulator_class = cls._simulators.get(simulator_type)

        if simulator_class is None:
            logger.warning(
                "Simulator type %s not implemented, using fallback",
                simulator_type
            )
            # Return a generic simulator that returns "in development" message
            return _FallbackSimulator(
                simulator_type=simulator_type,
                llm_provider=llm_provider,
                trace_repo=trace_repo,
                config=config
            )

        logger.info(
            "Creating simulator",
            extra={
                "simulator_type": simulator_type.value,
                "has_llm": llm_provider is not None
            }
        )

        return simulator_class(
            llm_provider=llm_provider,
            trace_repo=trace_repo,
            config=config
        )

    @classmethod
    def register(cls, simulator_type: SimuladorType, simulator_class: type):
        """
        Register a new simulator class.

        Allows extending the factory with new simulator types at runtime.

        Args:
            simulator_type: The type to register
            simulator_class: The class to instantiate for this type
        """
        if not issubclass(simulator_class, BaseSimulator):
            raise TypeError(f"{simulator_class} must inherit from BaseSimulator")

        cls._simulators[simulator_type] = simulator_class
        logger.info("Registered simulator: %s", simulator_type.value)

    @classmethod
    def available_types(cls) -> list:
        """Return list of available simulator types."""
        return list(cls._simulators.keys())


class _FallbackSimulator(BaseSimulator):
    """
    Fallback simulator for unimplemented types.

    Returns a message indicating the simulator is in development.
    """

    ROLE_NAME = "Unknown"
    SYSTEM_PROMPT = ""
    COMPETENCIES = []
    EXPECTS = []

    def __init__(
        self,
        simulator_type: SimuladorType,
        llm_provider=None,
        trace_repo=None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm_provider, trace_repo, config)
        self.simulator_type = simulator_type
        self.ROLE_NAME = simulator_type.value

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return 'in development' message."""
        return self.get_fallback_response()

    def get_fallback_response(self) -> Dict[str, Any]:
        """Return message indicating simulator is in development."""
        return {
            "message": f"El simulador {self.simulator_type.value} esta en desarrollo. Por favor, selecciona otro simulador.",
            "role": self.simulator_type.value,
            "expects": [],
            "metadata": {"status": "in_development"}
        }
