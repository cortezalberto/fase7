"""
User Model - User authentication and authorization database model.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- UserDB: Database model for user authentication and authorization
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Index
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, JSONBCompatible


class UserDB(Base, BaseModel):
    """
    User model for authentication and authorization.

    Stores user credentials, profile information, and roles.
    Used for JWT authentication in production.
    """

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)
    student_id = Column(String(100), nullable=True, unique=True, index=True)

    # Authorization
    roles = Column(JSONBCompatible, default=list, nullable=False)  # ["student", "instructor", "admin"]
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)
    is_verified = Column(Boolean, default=False, server_default='false', nullable=False)

    # Metadata
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, server_default='0')

    # Academic context (Cortez65.2 - for testing without LTI)
    # These fields allow students to have course/commission info without Moodle integration
    course_name = Column(String(255), nullable=True)  # Current course name (e.g., "Programación I")
    commission = Column(String(100), nullable=True)   # Commission code (e.g., "K1021")

    # Relationships
    sessions = relationship("SessionDB", back_populates="user", foreign_keys="SessionDB.user_id")
    student_profiles = relationship("StudentProfileDB", back_populates="user", foreign_keys="StudentProfileDB.user_id")
    activities = relationship("ActivityDB", back_populates="teacher", foreign_keys="ActivityDB.teacher_id")
    course_reports = relationship(
        "CourseReportDB",
        back_populates="teacher",
        foreign_keys="CourseReportDB.teacher_id"
    )
    remediation_plans_created = relationship(
        "RemediationPlanDB",
        back_populates="teacher",
        foreign_keys="RemediationPlanDB.teacher_id"
    )
    assigned_alerts = relationship(
        "RiskAlertDB",
        back_populates="assigned_to_user",
        foreign_keys="RiskAlertDB.assigned_to"
    )
    acknowledged_alerts = relationship(
        "RiskAlertDB",
        back_populates="acknowledged_by_user",
        foreign_keys="RiskAlertDB.acknowledged_by"
    )
    # FIX Cortez83: Add teacher_interventions relationship for bidirectional navigation
    teacher_interventions = relationship(
        "TeacherInterventionDB",
        back_populates="teacher",
        foreign_keys="TeacherInterventionDB.teacher_id"
    )

    # Composite indexes
    __table_args__ = (
        Index('idx_email_active', 'email', 'is_active'),
        Index('idx_username_active', 'username', 'is_active'),
        # GIN index for roles (PostgreSQL only)
        Index('idx_roles_gin', 'roles', postgresql_using='gin'),
    )
