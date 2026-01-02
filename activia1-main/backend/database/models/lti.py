"""
LTI Models - LTI 1.3 platform deployments and sessions.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- LTIDeploymentDB: LTI platform configurations (Moodle, Canvas, etc.)
- LTISessionDB: LTI launch sessions
"""
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel


class LTIDeploymentDB(Base, BaseModel):
    """
    LTI 1.3 platform deployments (Moodle, Canvas, etc.)

    Stores LTI configuration for external platforms for HU-SYS-010
    """

    __tablename__ = "lti_deployments"

    # Platform information
    platform_name = Column(String(100), nullable=False)  # "Moodle", "Canvas", "Blackboard"
    issuer = Column(String(255), nullable=False)  # LTI issuer URL
    client_id = Column(String(255), nullable=False)  # OAuth2 client ID
    deployment_id = Column(String(255), nullable=False)  # LTI deployment ID

    # OIDC endpoints
    auth_login_url = Column(Text, nullable=False)  # OIDC auth login URL
    auth_token_url = Column(Text, nullable=False)  # OAuth2 token URL
    public_keyset_url = Column(Text, nullable=False)  # JWKS URL (for token validation)

    # Optional: Access token URL for LTI Advantage services
    access_token_url = Column(Text, nullable=True)

    # Status
    # FIX 4.4 Cortez7: Added server_default for raw SQL compatibility
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)

    # Relationships
    lti_sessions = relationship("LTISessionDB", back_populates="deployment", cascade="all, delete-orphan")

    # Composite indexes
    __table_args__ = (
        # Unique constraint: One deployment per issuer + deployment_id
        Index('idx_lti_deployment_unique', 'issuer', 'deployment_id', unique=True),
        # Query: Get active deployments
        Index('idx_lti_deployment_active', 'is_active'),
    )


class LTISessionDB(Base, BaseModel):
    """
    LTI launch sessions (student launches from Moodle)

    Maps LTI users to AI-Native sessions for HU-SYS-010
    """

    __tablename__ = "lti_sessions"

    # LTI deployment
    # FIX 1.6 Cortez6: Added ondelete="CASCADE" to deployment FK
    deployment_id = Column(String(36), ForeignKey("lti_deployments.id", ondelete="CASCADE"), nullable=False, index=True)

    # LTI user information
    lti_user_id = Column(String(255), nullable=False, index=True)  # User ID from Moodle
    lti_user_name = Column(String(255), nullable=True)
    lti_user_email = Column(String(255), nullable=True)

    # LTI context (course)
    lti_context_id = Column(String(255), nullable=True)  # Course ID from Moodle
    lti_context_label = Column(String(100), nullable=True)  # Course code
    lti_context_title = Column(String(255), nullable=True)  # Course name

    # LTI resource link (activity within course)
    resource_link_id = Column(String(255), nullable=False, index=True)

    # Mapped to AI-Native session
    # DB-7 NOTE: session_id is intentionally nullable. An LTI launch from Moodle
    # creates an LTISessionDB first, before an AI-Native SessionDB is created.
    # The cascade="all, delete-orphan" on SessionDB.lti_sessions ensures cleanup
    # when the parent Session is deleted (correct parent->child direction).
    # FIX 1.7 Cortez6: Added ondelete="SET NULL" to session FK
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Launch metadata
    launch_token = Column(Text, nullable=True)  # JWT token from LTI launch (for AGS)
    locale = Column(String(10), nullable=True)  # User's locale (e.g., "es_AR")

    # Relationships
    deployment = relationship("LTIDeploymentDB", back_populates="lti_sessions")
    session = relationship("SessionDB", back_populates="lti_sessions")

    # Composite indexes
    __table_args__ = (
        # Query: Get LTI sessions for a user
        Index('idx_lti_session_user', 'lti_user_id'),
        # Query: Get LTI sessions for a resource
        Index('idx_lti_session_resource', 'resource_link_id'),
        # Query: Get LTI session by AI-Native session
        Index('idx_lti_session_native', 'session_id'),
    )
