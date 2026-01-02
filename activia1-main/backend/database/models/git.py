"""
Git Trace Model - Git N2-level traceability.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- GitTraceDB: Database model for Git commit traceability
"""
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel


class GitTraceDB(Base, BaseModel):
    """
    Database model for Git N2-level traceability

    SPRINT 5 - HU-SYS-008: Integracion Git
    Captura eventos Git (commits, branches, merges) asociados a sesiones de aprendizaje.

    FIX 10.11 Cortez10: IMPORTANT - This model has TWO timestamps:
    - `timestamp`: When the git commit was made (external timestamp from git)
    - `created_at`: When this DB record was created (inherited from BaseModel)
    These are semantically different and should not be confused.
    """

    __tablename__ = "git_traces"

    # Session relationship - FIX 3.4: Add ondelete="CASCADE"
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=False)

    # Git metadata
    event_type = Column(String(20), nullable=False)  # GitEventType: commit, branch_create, merge, etc.
    # FIX 1.4 Cortez4: Removed unique=True - same commit can appear in multiple sessions
    # Composite unique constraint added to __table_args__ instead
    commit_hash = Column(String(40), nullable=False, index=True)  # SHA-1 hash (40 chars)
    commit_message = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=False)
    author_email = Column(String(255), nullable=False)
    # FIX 10.11 Cortez10: This is the GIT commit timestamp, NOT the DB record creation time
    # Use created_at (from BaseModel) for when this record was inserted
    timestamp = Column(DateTime, nullable=False)  # Git commit timestamp (when code was committed)
    branch_name = Column(String(255), nullable=False)
    parent_commits = Column(JSON, default=list)  # List of parent commit hashes

    # Code changes
    files_changed = Column(JSON, default=list)  # List of GitFileChange dicts
    total_lines_added = Column(Integer, default=0)
    total_lines_deleted = Column(Integer, default=0)
    diff = Column(Text, default="")  # Full diff output

    # Analysis
    # FIX 4.4 Cortez7: Added server_default for raw SQL compatibility
    is_merge = Column(Boolean, default=False, server_default='false')
    is_revert = Column(Boolean, default=False, server_default='false')
    detected_patterns = Column(JSON, default=list)  # List of CodePattern strings
    complexity_delta = Column(Integer, nullable=True)  # Change in cyclomatic complexity

    # Correlation with N3/N4 traces
    related_cognitive_traces = Column(JSON, default=list)  # List of trace IDs
    cognitive_state_during_commit = Column(String(50), nullable=True)  # From nearest N4 trace
    time_since_last_interaction_minutes = Column(Integer, nullable=True)

    # Repository metadata
    repo_path = Column(String(500), nullable=True)
    remote_url = Column(String(500), nullable=True)

    # Relationship - FIX DB-6: Add back_populates for bidirectional relationship
    session = relationship("SessionDB", back_populates="git_traces")

    # Composite indexes for common query patterns
    __table_args__ = (
        # Query: Get all git events for a session
        Index('idx_git_session_timestamp', 'session_id', 'timestamp'),
        # Query: Get commits by student ordered by time
        Index('idx_git_student_timestamp', 'student_id', 'timestamp'),
        # Query: Filter by event type and student
        Index('idx_git_student_event', 'student_id', 'event_type'),
        # Query: Get commits for student + activity
        Index('idx_git_student_activity', 'student_id', 'activity_id'),
        # FIX 1.4 Cortez4: Composite unique constraint allows same commit in multiple sessions
        UniqueConstraint('session_id', 'commit_hash', name='uq_git_trace_session_commit'),
        # FIX 2.14 Cortez6: Check constraint for valid event_type values
        CheckConstraint(
            "event_type IN ('commit', 'branch_create', 'branch_delete', 'merge', 'tag', 'revert', 'cherry_pick')",
            name='ck_git_event_type_valid'
        ),
    )
