"""
Training Risk Monitor - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated training package.
Import from here or from backend.core.training.risk_monitor - both work.

Original implementation moved to: backend/core/training/risk_monitor.py
"""

# Re-export everything from the new location
from .training.risk_monitor import (
    TrainingRiskMonitor,
    RiskType,
    RiskSeverity,
    RiskFlag,
    RiskAnalysisResult,
    SessionRiskState,
)

__all__ = [
    "TrainingRiskMonitor",
    "RiskType",
    "RiskSeverity",
    "RiskFlag",
    "RiskAnalysisResult",
    "SessionRiskState",
]
