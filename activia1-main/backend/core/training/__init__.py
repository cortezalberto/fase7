"""
Training Module Package - Entrenador Digital Integration

Cortez66: Consolidated from scattered training_*.py files

This package contains the core training integration components:
- gateway.py: TrainingGateway - Orchestrator for agent integration
- traceability.py: TrainingTraceCollector - N4 trace capture
- risk_monitor.py: TrainingRiskMonitor - Real-time risk detection

Usage:
    from backend.core.training import (
        TrainingGateway,
        TrainingGatewayConfig,
        TrainingTraceCollector,
        TrainingRiskMonitor,
    )
"""

# Re-export from individual modules for backward compatibility
from .gateway import (
    TrainingGateway,
    TrainingGatewayConfig,
    CodeSubmissionResult,
    HintRequestResult,
)

from .traceability import (
    TrainingTraceCollector,
    TrainingTraceData,
    CognitiveInference,
    InferredCognitiveState,
    InferenceConfidence,
)

from .risk_monitor import (
    TrainingRiskMonitor,
    RiskType,
    RiskSeverity,
    RiskFlag,
    RiskAnalysisResult,
    SessionRiskState,
)

__all__ = [
    # Gateway
    "TrainingGateway",
    "TrainingGatewayConfig",
    "CodeSubmissionResult",
    "HintRequestResult",
    # Traceability
    "TrainingTraceCollector",
    "TrainingTraceData",
    "CognitiveInference",
    "InferredCognitiveState",
    "InferenceConfidence",
    # Risk Monitor
    "TrainingRiskMonitor",
    "RiskType",
    "RiskSeverity",
    "RiskFlag",
    "RiskAnalysisResult",
    "SessionRiskState",
]
