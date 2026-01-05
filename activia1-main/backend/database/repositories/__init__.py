"""
Repository Module - Domain-specific database operations.

Cortez42: Refactored from monolithic repositories.py (5,134 lines)
Cortez46: Completed extraction of all remaining repositories

This module provides backward-compatible imports for all repository classes.
Each repository has been extracted into its own module for better maintainability:

- base.py: Common utilities and base classes
- session_repository.py: SessionRepository
- trace_repository.py: TraceRepository
- risk_repository.py: RiskRepository
- evaluation_repository.py: EvaluationRepository
- activity_repository.py: ActivityRepository
- user_repository.py: UserRepository
- exercise_repository.py: Exercise-related repositories
- git_repository.py: GitTraceRepository (N2-level Git traceability)
- institutional_repository.py: CourseReportRepository, RemediationPlanRepository, RiskAlertRepository
- simulator_repository.py: InterviewSessionRepository, IncidentSimulationRepository, SimulatorEventRepository
- lti_repository.py: LTIDeploymentRepository, LTISessionRepository
- profile_repository.py: StudentProfileRepository, SubjectRepository, TraceSequenceRepository

All 24 repository classes have been extracted from the original monolithic file.
"""

# Base utilities
from .base import (
    BaseRepository,
    _safe_enum_to_str,
    _safe_cognitive_state_to_str,
)

# Core domain repositories
from .session_repository import SessionRepository
from .trace_repository import TraceRepository
from .risk_repository import RiskRepository
from .evaluation_repository import EvaluationRepository
from .activity_repository import ActivityRepository
from .user_repository import UserRepository

# Exercise-related repositories
from .exercise_repository import (
    ExerciseRepository,
    ExerciseHintRepository,
    ExerciseTestRepository,
    ExerciseAttemptRepository,
    RubricCriterionRepository,
    RubricLevelRepository,
)

# Git traceability repository (Cortez46)
from .git_repository import GitTraceRepository

# Institutional repositories (Cortez46)
from .institutional_repository import (
    CourseReportRepository,
    RemediationPlanRepository,
    RiskAlertRepository,
)

# Simulator repositories (Cortez46)
from .simulator_repository import (
    InterviewSessionRepository,
    IncidentSimulationRepository,
    SimulatorEventRepository,
)

# LTI integration repositories (Cortez46)
from .lti_repository import (
    LTIDeploymentRepository,
    LTISessionRepository,
)

# Profile and misc repositories (Cortez46)
from .profile_repository import (
    StudentProfileRepository,
    SubjectRepository,
    TraceSequenceRepository,
)

# Academic content repositories (Cortez72)
from .unidad_repository import UnidadRepository

# Teacher intervention repository (Cortez82)
from .intervention_repository import InterventionRepository

__all__ = [
    # Base
    "BaseRepository",
    "_safe_enum_to_str",
    "_safe_cognitive_state_to_str",
    # Core repositories (refactored)
    "SessionRepository",
    "TraceRepository",
    "RiskRepository",
    "EvaluationRepository",
    "ActivityRepository",
    "UserRepository",
    # Exercise repositories (refactored)
    "ExerciseRepository",
    "ExerciseHintRepository",
    "ExerciseTestRepository",
    "ExerciseAttemptRepository",
    "RubricCriterionRepository",
    "RubricLevelRepository",
    # Git traceability (Cortez46)
    "GitTraceRepository",
    # Institutional (Cortez46)
    "CourseReportRepository",
    "RemediationPlanRepository",
    "RiskAlertRepository",
    # Simulator (Cortez46)
    "InterviewSessionRepository",
    "IncidentSimulationRepository",
    "SimulatorEventRepository",
    # LTI integration (Cortez46)
    "LTIDeploymentRepository",
    "LTISessionRepository",
    # Profile and misc (Cortez46)
    "StudentProfileRepository",
    "SubjectRepository",
    "TraceSequenceRepository",
    # Academic content (Cortez72)
    "UnidadRepository",
    # Teacher intervention (Cortez82)
    "InterventionRepository",
]
