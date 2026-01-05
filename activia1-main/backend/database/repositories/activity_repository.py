"""
Activity Repository - Activity database operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)

Provides:
- ActivityRepository: CRUD operations for activities
- Batch loading to prevent N+1 queries
- Status management (draft, active, archived)
"""
from typing import List, Optional, Dict
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, select

from ..models import ActivityDB
from backend.core.constants import utc_now

logger = logging.getLogger(__name__)


class ActivityRepository:
    """Repository for activity operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(
        self,
        activity_id: str,
        title: str,
        instructions: str,
        teacher_id: str,
        policies: dict,
        description: Optional[str] = None,
        evaluation_criteria: Optional[List[str]] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        estimated_duration_minutes: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> ActivityDB:
        """
        Create a new activity.

        Args:
            activity_id: Unique activity identifier
            title: Activity title
            instructions: Activity instructions
            teacher_id: Teacher who created the activity
            policies: Pedagogical policies
            description: Optional description
            evaluation_criteria: Optional list of criteria
            subject: Optional subject
            difficulty: Optional difficulty level
            estimated_duration_minutes: Optional duration
            tags: Optional tags

        Returns:
            Created ActivityDB instance

        Raises:
            ValueError: If activity_id already exists
        """
        existing = self.get_by_activity_id(activity_id)
        if existing:
            raise ValueError(f"Activity with ID '{activity_id}' already exists")

        activity = ActivityDB(
            id=str(uuid4()),
            activity_id=activity_id,
            title=title,
            description=description,
            instructions=instructions,
            evaluation_criteria=evaluation_criteria or [],
            teacher_id=teacher_id,
            policies=policies,
            subject=subject,
            difficulty=difficulty,
            estimated_duration_minutes=estimated_duration_minutes,
            tags=tags or [],
            status="draft",
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_by_id(self, id: str) -> Optional[ActivityDB]:
        """
        Get activity by internal UUID (ActivityDB.id).

        Args:
            id: Internal UUID (primary key)

        Returns:
            ActivityDB or None

        Note:
            Use get_by_activity_id() for business key lookup.
        """
        return self.db.query(ActivityDB).filter(ActivityDB.id == id).first()

    def get_by_activity_id(self, activity_id: str) -> Optional[ActivityDB]:
        """
        Get activity by business key (ActivityDB.activity_id).

        Args:
            activity_id: Business key (e.g., "ACT-001")

        Returns:
            ActivityDB or None

        Note:
            Use get_by_id() for internal UUID lookup.
        """
        return self.db.query(ActivityDB).filter(ActivityDB.activity_id == activity_id).first()

    def get_by_teacher(
        self, teacher_id: str, status: Optional[str] = None
    ) -> List[ActivityDB]:
        """Get all activities created by a teacher."""
        query = self.db.query(ActivityDB).filter(ActivityDB.teacher_id == teacher_id)
        if status:
            query = query.filter(ActivityDB.status == status)
        return query.order_by(desc(ActivityDB.created_at)).all()

    def get_all(
        self,
        status: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 100,
    ) -> List[ActivityDB]:
        """Get all activities with optional filters."""
        query = self.db.query(ActivityDB)

        if status:
            query = query.filter(ActivityDB.status == status)
        if subject:
            query = query.filter(ActivityDB.subject == subject)
        if difficulty:
            query = query.filter(ActivityDB.difficulty == difficulty)

        return query.order_by(desc(ActivityDB.created_at)).limit(limit).all()

    def update(
        self,
        activity_id: str,
        **kwargs,
    ) -> Optional[ActivityDB]:
        """
        Update activity fields.

        Only allows updating safe, user-modifiable fields via whitelist.

        FIX Cortez75 HIGH-REPO-001: Added SELECT FOR UPDATE to prevent race conditions.

        Args:
            activity_id: Activity ID to update
            **kwargs: Fields to update

        Returns:
            Updated ActivityDB if found, None otherwise

        Raises:
            ValueError: If attempting to update a protected field or invalid value
            TypeError: If field value has incorrect type
        """
        UPDATEABLE_FIELDS = {
            "title": str,
            "description": str,
            "instructions": str,
            "difficulty": str,
            "tags": list,
            "learning_objectives": list,
            "evaluation_criteria": dict,
            "estimated_duration_minutes": int,
            "max_ai_assistance": float,
        }

        # FIX Cortez75 HIGH-REPO-001: Use SELECT FOR UPDATE to prevent race conditions
        try:
            stmt = select(ActivityDB).where(ActivityDB.activity_id == activity_id).with_for_update()
            activity = self.db.execute(stmt).scalar_one_or_none()
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to lock activity %s for update: %s", activity_id, e, exc_info=True)
            raise

        if not activity:
            return None

        for key, value in kwargs.items():
            if key not in UPDATEABLE_FIELDS:
                raise ValueError(
                    f"Cannot update field '{key}'. "
                    f"Allowed fields: {', '.join(UPDATEABLE_FIELDS.keys())}"
                )

            if value is not None:
                expected_type = UPDATEABLE_FIELDS[key]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Invalid type for field '{key}': "
                        f"expected {expected_type.__name__}, got {type(value).__name__}"
                    )

                # Validate ranges/values
                if key == "max_ai_assistance":
                    if not (0.0 <= value <= 1.0):
                        raise ValueError(
                            f"max_ai_assistance must be in range [0.0, 1.0], got {value}"
                        )
                elif key == "estimated_duration_minutes":
                    if value <= 0:
                        raise ValueError(
                            f"estimated_duration_minutes must be positive, got {value}"
                        )
                elif key == "difficulty":
                    VALID_DIFFICULTIES = ["INICIAL", "INTERMEDIO", "AVANZADO"]
                    if value not in VALID_DIFFICULTIES:
                        raise ValueError(
                            f"difficulty must be one of {VALID_DIFFICULTIES}, got '{value}'"
                        )
                elif key == "title":
                    if not (3 <= len(value) <= 200):
                        raise ValueError(
                            f"title length must be between 3 and 200 characters, got {len(value)}"
                        )
                elif key == "description":
                    if len(value) > 2000:
                        raise ValueError(
                            f"description length must be <= 2000 characters, got {len(value)}"
                        )
                elif key == "tags":
                    if len(value) == 0:
                        raise ValueError("tags list cannot be empty")
                    if not all(isinstance(tag, str) for tag in value):
                        raise TypeError("tags must be a list of strings")
                    if not all(len(tag) >= 2 for tag in value):
                        raise ValueError("each tag must have at least 2 characters")

                setattr(activity, key, value)

        try:
            activity.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update activity %s: %s", activity_id, e, exc_info=True)
            raise

    def publish(self, activity_id: str) -> Optional[ActivityDB]:
        """
        Publish an activity (change status from draft to active).

        Args:
            activity_id: Activity ID to publish

        Returns:
            Updated ActivityDB if found, None otherwise
        """
        try:
            stmt = select(ActivityDB).where(ActivityDB.activity_id == activity_id).with_for_update()
            activity = self.db.execute(stmt).scalar_one_or_none()

            if not activity:
                return None

            activity.status = "active"
            activity.published_at = utc_now()
            activity.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to publish activity %s: %s", activity_id, e, exc_info=True)
            raise

    def archive(self, activity_id: str) -> Optional[ActivityDB]:
        """
        Archive an activity.

        Args:
            activity_id: Activity ID to archive

        Returns:
            Updated ActivityDB if found, None otherwise
        """
        try:
            stmt = select(ActivityDB).where(ActivityDB.activity_id == activity_id).with_for_update()
            activity = self.db.execute(stmt).scalar_one_or_none()

            if not activity:
                return None

            activity.status = "archived"
            activity.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to archive activity %s: %s", activity_id, e, exc_info=True)
            raise

    def delete(self, activity_id: str) -> bool:
        """
        Delete an activity (soft delete by archiving).

        Args:
            activity_id: Activity ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(ActivityDB).where(ActivityDB.activity_id == activity_id).with_for_update()
            activity = self.db.execute(stmt).scalar_one_or_none()

            if not activity:
                return False

            activity.status = "archived"
            activity.updated_at = utc_now()
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete activity %s: %s", activity_id, e, exc_info=True)
            raise

    def get_by_ids(self, activity_ids: List[str]) -> Dict[str, ActivityDB]:
        """
        Get multiple activities by IDs in a single query (batch loading).

        Args:
            activity_ids: List of activity IDs to fetch

        Returns:
            Dictionary mapping activity_id to ActivityDB
        """
        if not activity_ids:
            return {}

        activities = (
            self.db.query(ActivityDB)
            .filter(ActivityDB.activity_id.in_(activity_ids))
            .all()
        )
        return {activity.activity_id: activity for activity in activities}

    # =========================================================================
    # LTI/Moodle Integration Methods (Cortez65.1)
    # =========================================================================

    def get_by_moodle_context(
        self,
        moodle_course_id: str,
        moodle_resource_name: str,
    ) -> Optional[ActivityDB]:
        """
        Find an activity by Moodle course and resource name.

        This is used during LTI launch to automatically find the matching
        AI-Native activity configured by the teacher.

        Args:
            moodle_course_id: The context_id from Moodle LTI claims
            moodle_resource_name: The resource_link_title from Moodle LTI claims

        Returns:
            Matching ActivityDB if found, None otherwise
        """
        return (
            self.db.query(ActivityDB)
            .filter(
                ActivityDB.moodle_course_id == moodle_course_id,
                ActivityDB.moodle_resource_name == moodle_resource_name,
                ActivityDB.status == "active",
            )
            .first()
        )

    def get_by_moodle_resource_name(
        self,
        moodle_resource_name: str,
    ) -> Optional[ActivityDB]:
        """
        Find an activity by Moodle resource name only.

        Fallback when course_id matching doesn't find a result.
        Useful when the same activity name is used across courses.

        Args:
            moodle_resource_name: The resource_link_title from Moodle LTI claims

        Returns:
            Matching ActivityDB if found, None otherwise
        """
        return (
            self.db.query(ActivityDB)
            .filter(
                ActivityDB.moodle_resource_name == moodle_resource_name,
                ActivityDB.status == "active",
            )
            .first()
        )

    def link_to_moodle(
        self,
        activity_id: str,
        moodle_course_id: str,
        moodle_course_name: str,
        moodle_course_label: Optional[str] = None,
        moodle_resource_name: Optional[str] = None,
    ) -> Optional[ActivityDB]:
        """
        Link an existing activity to a Moodle course/resource.

        This is called by the teacher when configuring the LTI integration.

        Args:
            activity_id: AI-Native activity ID to link
            moodle_course_id: The context_id from Moodle
            moodle_course_name: The context_title (course name)
            moodle_course_label: The context_label (commission code)
            moodle_resource_name: The resource_link_title (activity name in Moodle)

        Returns:
            Updated ActivityDB if found, None otherwise
        """
        try:
            # FIX Cortez70 CRIT-DB-001: Use SELECT FOR UPDATE to prevent race conditions
            stmt = select(ActivityDB).where(ActivityDB.activity_id == activity_id).with_for_update()
            activity = self.db.execute(stmt).scalar_one_or_none()

            if not activity:
                return None

            activity.moodle_course_id = moodle_course_id
            activity.moodle_course_name = moodle_course_name
            activity.moodle_course_label = moodle_course_label
            activity.moodle_resource_name = moodle_resource_name
            activity.updated_at = utc_now()

            self.db.commit()
            self.db.refresh(activity)
            logger.info(
                "Linked activity '%s' to Moodle course '%s' resource '%s'",
                activity_id,
                moodle_course_id,
                moodle_resource_name,
            )
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to link activity %s to Moodle: %s", activity_id, e, exc_info=True)
            raise

    def unlink_from_moodle(self, activity_id: str) -> Optional[ActivityDB]:
        """
        Remove Moodle link from an activity.

        Args:
            activity_id: AI-Native activity ID to unlink

        Returns:
            Updated ActivityDB if found, None otherwise
        """
        try:
            # FIX Cortez70 CRIT-DB-002: Use SELECT FOR UPDATE to prevent race conditions
            stmt = select(ActivityDB).where(ActivityDB.activity_id == activity_id).with_for_update()
            activity = self.db.execute(stmt).scalar_one_or_none()

            if not activity:
                return None

            activity.moodle_course_id = None
            activity.moodle_course_name = None
            activity.moodle_course_label = None
            activity.moodle_resource_name = None
            activity.updated_at = utc_now()

            self.db.commit()
            self.db.refresh(activity)
            logger.info("Unlinked activity '%s' from Moodle", activity_id)
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to unlink activity %s from Moodle: %s", activity_id, e, exc_info=True)
            raise

    def get_moodle_linked_activities(
        self,
        teacher_id: Optional[str] = None,
    ) -> List[ActivityDB]:
        """
        Get all activities that are linked to Moodle.

        Args:
            teacher_id: Optional filter by teacher

        Returns:
            List of activities with Moodle links
        """
        query = self.db.query(ActivityDB).filter(
            ActivityDB.moodle_course_id.isnot(None),
        )

        if teacher_id:
            query = query.filter(ActivityDB.teacher_id == teacher_id)

        return query.order_by(desc(ActivityDB.updated_at)).all()
