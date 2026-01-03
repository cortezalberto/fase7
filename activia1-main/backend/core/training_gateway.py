"""
Training Gateway - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated training package.
Import from here or from backend.core.training.gateway - both work.

Original implementation moved to: backend/core/training/gateway.py
"""

# Re-export everything from the new location
from .training.gateway import (
    TrainingGateway,
    TrainingGatewayConfig,
    CodeSubmissionResult,
    HintRequestResult,
)

__all__ = [
    "TrainingGateway",
    "TrainingGatewayConfig",
    "CodeSubmissionResult",
    "HintRequestResult",
]
