"""
Gateway Module - AIGateway coordination components.

Cortez42: Initial refactoring from monolithic ai_gateway.py
Cortez66: Complete extraction of coordinators and response generators

This module provides modular components for the AI Gateway:

- protocols.py: Repository protocol interfaces for type checking
- fallback_responses.py: Circuit breaker fallback responses
- response_generators.py: LLM response generation (7 types + fallbacks)
- trace_coordinator.py: N4 traceability management
- risk_coordinator.py: Risk analysis and persistence

The main AIGateway class remains in ai_gateway.py but imports
these extracted components for cleaner separation of concerns.
"""

# Protocol interfaces
from .protocols import (
    SessionRepositoryProtocol,
    TraceRepositoryProtocol,
    RiskRepositoryProtocol,
    EvaluationRepositoryProtocol,
    SequenceRepositoryProtocol,
)

# Fallback responses
from .fallback_responses import (
    get_fallback_socratic_response,
    get_fallback_conceptual_explanation,
    get_fallback_guided_hints,
    get_blocked_response_message,
)

# Response generators (Cortez66)
from .response_generators import (
    generate_socratic_response,
    generate_conceptual_explanation,
    generate_guided_hints,
    generate_empathetic_support,
    generate_metacognitive_guidance,
    generate_example_based,
    generate_clarification_request,
    # Fallbacks for new types (Cortez64)
    get_fallback_empathetic_support,
    get_fallback_metacognitive_guidance,
    get_fallback_example_based,
    get_fallback_clarification_request,
)

# Trace coordinator (Cortez66)
from .trace_coordinator import TraceCoordinator

# Risk coordinator (Cortez66)
from .risk_coordinator import RiskCoordinator

__all__ = [
    # Protocols
    "SessionRepositoryProtocol",
    "TraceRepositoryProtocol",
    "RiskRepositoryProtocol",
    "EvaluationRepositoryProtocol",
    "SequenceRepositoryProtocol",
    # Fallback responses (original)
    "get_fallback_socratic_response",
    "get_fallback_conceptual_explanation",
    "get_fallback_guided_hints",
    "get_blocked_response_message",
    # Response generators
    "generate_socratic_response",
    "generate_conceptual_explanation",
    "generate_guided_hints",
    "generate_empathetic_support",
    "generate_metacognitive_guidance",
    "generate_example_based",
    "generate_clarification_request",
    # Fallbacks for new types (Cortez64)
    "get_fallback_empathetic_support",
    "get_fallback_metacognitive_guidance",
    "get_fallback_example_based",
    "get_fallback_clarification_request",
    # Coordinators
    "TraceCoordinator",
    "RiskCoordinator",
]
