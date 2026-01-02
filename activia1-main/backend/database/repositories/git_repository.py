"""
Git Trace Repository - N2-level Git traceability operations.

Cortez46: Extracted from repositories.py (5,134 lines)

SPRINT 5 - HU-SYS-008: Integración Git
"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import GitTraceDB
from .base import BaseRepository

logger = logging.getLogger(__name__)


class GitTraceRepository(BaseRepository):
    """
    Repository for Git N2-level traceability operations.

    SPRINT 5 - HU-SYS-008: Integración Git
    """

    def create(
        self,
        session_id: str,
        student_id: str,
        activity_id: str,
        event_type: str,
        commit_hash: str,
        commit_message: str,
        author_name: str,
        author_email: str,
        timestamp: datetime,
        branch_name: str,
        parent_commits: List[str],
        files_changed: List[dict],
        total_lines_added: int = 0,
        total_lines_deleted: int = 0,
        diff: str = "",
        is_merge: bool = False,
        is_revert: bool = False,
        detected_patterns: Optional[List[str]] = None,
        complexity_delta: Optional[int] = None,
        related_cognitive_traces: Optional[List[str]] = None,
        cognitive_state_during_commit: Optional[str] = None,
        time_since_last_interaction_minutes: Optional[int] = None,
        repo_path: Optional[str] = None,
        remote_url: Optional[str] = None,
    ) -> GitTraceDB:
        """
        Create a new Git trace.

        Args:
            session_id: Session ID
            student_id: Student ID
            activity_id: Activity ID
            event_type: GitEventType (commit, branch_create, merge, etc.)
            commit_hash: SHA-1 hash (40 chars)
            commit_message: Commit message
            author_name: Author name
            author_email: Author email
            timestamp: Commit timestamp
            branch_name: Branch name
            parent_commits: List of parent commit hashes
            files_changed: List of GitFileChange dicts
            total_lines_added: Total lines added
            total_lines_deleted: Total lines deleted
            diff: Full diff output
            is_merge: True if merge commit
            is_revert: True if revert commit
            detected_patterns: List of CodePattern strings
            complexity_delta: Change in cyclomatic complexity
            related_cognitive_traces: Related N4 trace IDs
            cognitive_state_during_commit: Cognitive state from nearest N4 trace
            time_since_last_interaction_minutes: Minutes since last interaction
            repo_path: Repository local path
            remote_url: Repository remote URL

        Returns:
            Created GitTraceDB instance
        """
        git_trace = GitTraceDB(
            id=str(uuid4()),
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            event_type=event_type,
            commit_hash=commit_hash,
            commit_message=commit_message,
            author_name=author_name,
            author_email=author_email,
            timestamp=timestamp,
            branch_name=branch_name,
            parent_commits=parent_commits,
            files_changed=files_changed,
            total_lines_added=total_lines_added,
            total_lines_deleted=total_lines_deleted,
            diff=diff,
            is_merge=is_merge,
            is_revert=is_revert,
            detected_patterns=detected_patterns or [],
            complexity_delta=complexity_delta,
            related_cognitive_traces=related_cognitive_traces or [],
            cognitive_state_during_commit=cognitive_state_during_commit,
            time_since_last_interaction_minutes=time_since_last_interaction_minutes,
            repo_path=repo_path,
            remote_url=remote_url,
        )
        self.db.add(git_trace)
        self.db.commit()
        self.db.refresh(git_trace)

        logger.info(
            "Git trace created: %s for session %s",
            git_trace.id,
            session_id,
            extra={
                "trace_id": git_trace.id,
                "session_id": session_id,
                "commit_hash": commit_hash,
                "event_type": event_type,
            },
        )
        return git_trace

    def get_by_id(self, trace_id: str) -> Optional[GitTraceDB]:
        """Get Git trace by ID."""
        return self.db.query(GitTraceDB).filter(GitTraceDB.id == trace_id).first()

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[GitTraceDB]:
        """
        Get all Git traces for a session ordered by timestamp.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        return (
            self.db.query(GitTraceDB)
            .filter(GitTraceDB.session_id == session_id)
            .order_by(GitTraceDB.timestamp)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_student(
        self, student_id: str, limit: Optional[int] = None
    ) -> List[GitTraceDB]:
        """Get Git traces by student ordered by timestamp."""
        query = (
            self.db.query(GitTraceDB)
            .filter(GitTraceDB.student_id == student_id)
            .order_by(desc(GitTraceDB.timestamp))
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_by_commit_hash(self, commit_hash: str) -> Optional[GitTraceDB]:
        """Get Git trace by commit hash."""
        return (
            self.db.query(GitTraceDB)
            .filter(GitTraceDB.commit_hash == commit_hash)
            .first()
        )

    def get_by_student_activity(
        self,
        student_id: str,
        activity_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[GitTraceDB]:
        """
        Get Git traces for student + activity ordered by timestamp.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        return (
            self.db.query(GitTraceDB)
            .filter(
                GitTraceDB.student_id == student_id,
                GitTraceDB.activity_id == activity_id,
            )
            .order_by(GitTraceDB.timestamp)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_by_student(self, student_id: str) -> int:
        """Count total commits by student."""
        return (
            self.db.query(GitTraceDB)
            .filter(GitTraceDB.student_id == student_id)
            .count()
        )

    def count_by_session(self, session_id: str) -> int:
        """Count total commits in a session."""
        return (
            self.db.query(GitTraceDB)
            .filter(GitTraceDB.session_id == session_id)
            .count()
        )
