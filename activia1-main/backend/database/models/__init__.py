"""
Database Models Package - Domain-specific ORM models.

Cortez42: Refactored from monolithic models.py (1,772 lines, 25 classes)

This package provides modular, domain-specific ORM models while maintaining
full backward compatibility with existing code that imports from models.py.

Organization:
- base.py: Common utilities (JSONBCompatible, utc_now, Base, BaseModel)
- session.py: SessionDB - Learning sessions
- trace.py: CognitiveTraceDB, TraceSequenceDB - N4 cognitive traceability
- risk.py: RiskDB - Detected risks
- evaluation.py: EvaluationDB - Process evaluations
- user.py: UserDB - User authentication
- activity.py: ActivityDB - Learning activities
- student_profile.py: StudentProfileDB - Student profiles
- git.py: GitTraceDB - Git N2 traceability
- reports.py: CourseReportDB, RemediationPlanDB, RiskAlertDB - Institutional reports
- simulation.py: InterviewSessionDB, IncidentSimulationDB, SimulatorEventDB
- lti.py: LTIDeploymentDB, LTISessionDB - LTI 1.3 integration
- subject.py: SubjectDB - Subject/course organization
- exercise.py: ExerciseDB, ExerciseHintDB, ExerciseTestDB, ExerciseAttemptDB,
               ExerciseRubricCriterionDB, RubricLevelDB

Usage (backward compatible):
    # Old import still works:
    from backend.database.models import SessionDB, UserDB

    # New import also works:
    from backend.database.models.session import SessionDB
    from backend.database.models.user import UserDB
"""

# Base utilities
from .base import (
    Base,
    BaseModel,
    JSONBCompatible,
    utc_now,
)

# Core domain models
from .session import SessionDB
from .trace import CognitiveTraceDB, TraceSequenceDB
from .risk import RiskDB
from .evaluation import EvaluationDB
from .user import UserDB
from .activity import ActivityDB
from .student_profile import StudentProfileDB

# Git traceability
from .git import GitTraceDB

# Institutional reports
from .reports import (
    CourseReportDB,
    RemediationPlanDB,
    RiskAlertDB,
)

# Simulations
from .simulation import (
    InterviewSessionDB,
    IncidentSimulationDB,
    SimulatorEventDB,
)

# LTI integration
from .lti import (
    LTIDeploymentDB,
    LTISessionDB,
)

# Exercises
from .subject import SubjectDB
from .exercise import (
    ExerciseDB,
    ExerciseHintDB,
    ExerciseTestDB,
    ExerciseAttemptDB,
    ExerciseRubricCriterionDB,
    RubricLevelDB,
)

# Legacy alias for utc_now (original name in models.py)
_utc_now = utc_now

__all__ = [
    # Base utilities
    "Base",
    "BaseModel",
    "JSONBCompatible",
    "utc_now",
    "_utc_now",  # Legacy alias
    # Core domain
    "SessionDB",
    "CognitiveTraceDB",
    "TraceSequenceDB",
    "RiskDB",
    "EvaluationDB",
    "UserDB",
    "ActivityDB",
    "StudentProfileDB",
    # Git traceability
    "GitTraceDB",
    # Institutional reports
    "CourseReportDB",
    "RemediationPlanDB",
    "RiskAlertDB",
    # Simulations
    "InterviewSessionDB",
    "IncidentSimulationDB",
    "SimulatorEventDB",
    # LTI
    "LTIDeploymentDB",
    "LTISessionDB",
    # Exercises
    "SubjectDB",
    "ExerciseDB",
    "ExerciseHintDB",
    "ExerciseTestDB",
    "ExerciseAttemptDB",
    "ExerciseRubricCriterionDB",
    "RubricLevelDB",
]
