"""
Gateway Module - AIGateway coordination components.

Cortez42: Refactored from monolithic ai_gateway.py (1,996 lines)

This module provides modular components for the AI Gateway:

- protocols.py: Repository protocol interfaces for type checking
- fallback_responses.py: Circuit breaker fallback responses

Future modules (to be extracted):
- trace_coordinator.py: Trace management coordination
- risk_coordinator.py: Risk analysis coordination
- response_generators.py: LLM response generation

The main AIGateway class remains in ai_gateway.py but imports
these extracted components.
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

__all__ = [
    # Protocols
    "SessionRepositoryProtocol",
    "TraceRepositoryProtocol",
    "RiskRepositoryProtocol",
    "EvaluationRepositoryProtocol",
    "SequenceRepositoryProtocol",
    # Fallback responses
    "get_fallback_socratic_response",
    "get_fallback_conceptual_explanation",
    "get_fallback_guided_hints",
    "get_blocked_response_message",
]
