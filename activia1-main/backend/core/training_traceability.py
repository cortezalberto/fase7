"""
Training Trace Collector - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated training package.
Import from here or from backend.core.training.traceability - both work.

Original implementation moved to: backend/core/training/traceability.py
"""

# Re-export everything from the new location
from .training.traceability import (
    TrainingTraceCollector,
    TrainingTraceData,
    CognitiveInference,
    InferredCognitiveState,
    InferenceConfidence,
)

__all__ = [
    "TrainingTraceCollector",
    "TrainingTraceData",
    "CognitiveInference",
    "InferredCognitiveState",
    "InferenceConfidence",
]
