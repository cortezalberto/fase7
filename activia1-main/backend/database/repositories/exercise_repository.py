"""
Exercise Repository - Exercise database operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)
FIX Cortez52: Added batch loading methods to prevent N+1 queries

Provides:
- ExerciseRepository: CRUD operations for exercises
- ExerciseHintRepository: Hint management
- ExerciseTestRepository: Test management
- ExerciseAttemptRepository: Student attempts tracking
- RubricCriterionRepository: Rubric criteria management
- RubricLevelRepository: Rubric levels management
"""
from typing import List, Optional, Dict
from collections import defaultdict
from uuid import uuid4
import logging

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from ..models import (
    ExerciseDB, ExerciseHintDB, ExerciseTestDB,
    ExerciseAttemptDB, ExerciseRubricCriterionDB, RubricLevelDB
)
from backend.core.constants import utc_now

logger = logging.getLogger(__name__)


class ExerciseRepository:
    """Repository for Exercise operations with soft delete support."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, active_only: bool = True, include_deleted: bool = False) -> List[ExerciseDB]:
        """Get all exercises."""
        query = self.db.query(ExerciseDB)
        # FIX Cortez85 HIGH-ORM-002: Use .is_(True) for boolean comparisons
        if active_only:
            query = query.filter(ExerciseDB.is_active.is_(True))
        if not include_deleted:
            query = query.filter(ExerciseDB.deleted_at.is_(None))
        return query.order_by(ExerciseDB.unit, ExerciseDB.title).all()

    def get_by_id(self, exercise_id: str, include_deleted: bool = False) -> Optional[ExerciseDB]:
        """Get exercise by ID."""
        query = self.db.query(ExerciseDB).filter(ExerciseDB.id == exercise_id)
        if not include_deleted:
            query = query.filter(ExerciseDB.deleted_at.is_(None))
        return query.first()

    def get_by_subject(self, subject_code: str, active_only: bool = True) -> List[ExerciseDB]:
        """Get exercises by subject."""
        query = self.db.query(ExerciseDB).filter(
            ExerciseDB.subject_code == subject_code,
            ExerciseDB.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(ExerciseDB.is_active.is_(True))
        return query.order_by(ExerciseDB.unit, ExerciseDB.title).all()

    def get_by_unit(self, subject_code: str, unit: int, active_only: bool = True) -> List[ExerciseDB]:
        """Get exercises by subject and unit."""
        query = self.db.query(ExerciseDB).filter(
            ExerciseDB.subject_code == subject_code,
            ExerciseDB.unit == unit,
            ExerciseDB.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(ExerciseDB.is_active.is_(True))
        return query.order_by(ExerciseDB.title).all()

    def get_by_language_and_unit(
        self, language: str, unit_number: int, active_only: bool = True
    ) -> List[ExerciseDB]:
        """
        FIX Cortez54: Get exercises by programming language and unit number.

        This method was missing and caused training module to fail.

        Args:
            language: Programming language ('python', 'java')
            unit_number: Unit/lesson number (1-7)
            active_only: Only return active exercises

        Returns:
            List of exercises matching the criteria
        """
        query = self.db.query(ExerciseDB).filter(
            ExerciseDB.language == language.lower(),
            ExerciseDB.unit == unit_number,
            ExerciseDB.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(ExerciseDB.is_active.is_(True))
        return query.order_by(ExerciseDB.title).all()

    def get_by_language(self, language: str, active_only: bool = True) -> List[ExerciseDB]:
        """
        FIX Cortez54: Get all exercises for a programming language.

        Args:
            language: Programming language ('python', 'java')
            active_only: Only return active exercises

        Returns:
            List of exercises for the language
        """
        query = self.db.query(ExerciseDB).filter(
            ExerciseDB.language == language.lower(),
            ExerciseDB.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(ExerciseDB.is_active.is_(True))
        return query.order_by(ExerciseDB.unit, ExerciseDB.title).all()

    def get_languages_with_units(self) -> List[dict]:
        """
        FIX Cortez54: Get available languages with their unit counts.

        Returns list of dicts with language info for training module.
        Used by /training/lenguajes endpoint.

        Returns:
            List of language info dicts
        """
        from sqlalchemy import func, distinct

        results = (
            self.db.query(
                ExerciseDB.language,
                func.count(distinct(ExerciseDB.unit)).label('unit_count'),
                func.count(ExerciseDB.id).label('exercise_count')
            )
            .filter(
                ExerciseDB.deleted_at.is_(None),
                ExerciseDB.is_active.is_(True),
                ExerciseDB.unit.isnot(None)
            )
            .group_by(ExerciseDB.language)
            .all()
        )

        return [
            {
                'language': r.language,
                'unit_count': r.unit_count,
                'exercise_count': r.exercise_count
            }
            for r in results
        ]

    def get_with_hints(self, exercise_id: str) -> Optional[ExerciseDB]:
        """Get exercise with hints (eager loading)."""
        return (
            self.db.query(ExerciseDB)
            .options(selectinload(ExerciseDB.hints))
            .filter(
                ExerciseDB.id == exercise_id,
                ExerciseDB.deleted_at.is_(None)
            )
            .first()
        )

    def get_with_tests(self, exercise_id: str) -> Optional[ExerciseDB]:
        """Get exercise with tests (eager loading)."""
        return (
            self.db.query(ExerciseDB)
            .options(selectinload(ExerciseDB.tests))
            .filter(
                ExerciseDB.id == exercise_id,
                ExerciseDB.deleted_at.is_(None)
            )
            .first()
        )

    def get_with_details(self, exercise_id: str) -> Optional[ExerciseDB]:
        """Get exercise with hints, tests, and rubric (eager loading)."""
        return (
            self.db.query(ExerciseDB)
            .options(
                selectinload(ExerciseDB.hints),
                selectinload(ExerciseDB.tests),
                selectinload(ExerciseDB.rubric_criteria).selectinload(ExerciseRubricCriterionDB.levels)
            )
            .filter(
                ExerciseDB.id == exercise_id,
                ExerciseDB.deleted_at.is_(None)
            )
            .first()
        )

    def search(self, query_text: str, active_only: bool = True) -> List[ExerciseDB]:
        """Search exercises by title/description (case-insensitive)."""
        # FIX Cortez83: Sanitize LIKE pattern to prevent injection
        # Escape special LIKE characters before wrapping with %
        safe_text = query_text.replace("%", "\\%").replace("_", "\\_")
        search_pattern = f"%{safe_text}%"
        query = self.db.query(ExerciseDB).filter(
            (ExerciseDB.title.ilike(search_pattern, escape="\\")) |
            (ExerciseDB.description.ilike(search_pattern, escape="\\")),
            ExerciseDB.deleted_at.is_(None)
        )
        if active_only:
            query = query.filter(ExerciseDB.is_active.is_(True))
        return query.all()

    def create(self, exercise: ExerciseDB) -> ExerciseDB:
        """Create new exercise."""
        try:
            self.db.add(exercise)
            self.db.commit()
            self.db.refresh(exercise)
            logger.info("Exercise created: %s - %s", exercise.id, exercise.title)
            return exercise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating exercise %s: %s", exercise.id, e, exc_info=True)
            raise

    def update(self, exercise_id: str, updates: dict) -> Optional[ExerciseDB]:
        """Update exercise."""
        try:
            exercise = self.get_by_id(exercise_id)
            if not exercise:
                return None

            for key, value in updates.items():
                if hasattr(exercise, key):
                    setattr(exercise, key, value)

            exercise.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(exercise)
            logger.info("Exercise updated: %s", exercise_id)
            return exercise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error updating exercise %s: %s", exercise_id, e, exc_info=True)
            raise

    def soft_delete(self, exercise_id: str) -> bool:
        """Soft delete exercise (set deleted_at)."""
        try:
            exercise = self.get_by_id(exercise_id)
            if not exercise:
                return False

            exercise.deleted_at = utc_now()
            exercise.is_active = False
            self.db.commit()
            logger.warning("Exercise soft deleted: %s", exercise_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error soft deleting exercise %s: %s", exercise_id, e, exc_info=True)
            raise

    def restore(self, exercise_id: str) -> Optional[ExerciseDB]:
        """Restore soft-deleted exercise."""
        try:
            exercise = self.get_by_id(exercise_id, include_deleted=True)
            if not exercise or exercise.deleted_at is None:
                return None

            exercise.deleted_at = None
            exercise.is_active = True
            exercise.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(exercise)
            logger.info("Exercise restored: %s", exercise_id)
            return exercise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error restoring exercise %s: %s", exercise_id, e, exc_info=True)
            raise


class ExerciseHintRepository:
    """Repository for Exercise Hints operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_exercise(self, exercise_id: str) -> List[ExerciseHintDB]:
        """Get all hints for an exercise, ordered by hint_number."""
        return (
            self.db.query(ExerciseHintDB)
            .filter(ExerciseHintDB.exercise_id == exercise_id)
            .order_by(ExerciseHintDB.hint_number)
            .all()
        )

    def get_by_exercise_ids(self, exercise_ids: List[str]) -> Dict[str, List[ExerciseHintDB]]:
        """
        FIX Cortez52: Batch load hints for multiple exercises to prevent N+1 queries.

        Args:
            exercise_ids: List of exercise IDs

        Returns:
            Dictionary mapping exercise_id to list of hints
        """
        if not exercise_ids:
            return {}

        hints = (
            self.db.query(ExerciseHintDB)
            .filter(ExerciseHintDB.exercise_id.in_(exercise_ids))
            .order_by(ExerciseHintDB.exercise_id, ExerciseHintDB.hint_number)
            .all()
        )

        result: Dict[str, List[ExerciseHintDB]] = defaultdict(list)
        for hint in hints:
            result[hint.exercise_id].append(hint)

        return dict(result)

    def get_by_id(self, hint_id: str) -> Optional[ExerciseHintDB]:
        """Get hint by ID."""
        return self.db.query(ExerciseHintDB).filter(ExerciseHintDB.id == hint_id).first()

    def get_next_hint(self, exercise_id: str, current_hint_number: int) -> Optional[ExerciseHintDB]:
        """Get next available hint."""
        return (
            self.db.query(ExerciseHintDB)
            .filter(
                ExerciseHintDB.exercise_id == exercise_id,
                ExerciseHintDB.hint_number == current_hint_number + 1
            )
            .first()
        )

    def create(self, hint: ExerciseHintDB) -> ExerciseHintDB:
        """Create new hint."""
        try:
            self.db.add(hint)
            self.db.commit()
            self.db.refresh(hint)
            logger.info("Hint created: exercise %s, hint #%s", hint.exercise_id, hint.hint_number)
            return hint
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating hint: %s", e, exc_info=True)
            raise

    def create_batch(self, hints: List[ExerciseHintDB]) -> List[ExerciseHintDB]:
        """Create multiple hints at once."""
        try:
            self.db.add_all(hints)
            self.db.commit()
            for hint in hints:
                self.db.refresh(hint)
            logger.info("Batch created %s hints", len(hints))
            return hints
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error batch creating hints: %s", e, exc_info=True)
            raise

    def update(self, hint_id: str, updates: dict) -> Optional[ExerciseHintDB]:
        """Update hint."""
        try:
            hint = self.get_by_id(hint_id)
            if not hint:
                return None

            for key, value in updates.items():
                if hasattr(hint, key):
                    setattr(hint, key, value)

            self.db.commit()
            self.db.refresh(hint)
            logger.info("Hint updated: %s", hint_id)
            return hint
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error updating hint %s: %s", hint_id, e, exc_info=True)
            raise

    def delete(self, hint_id: str) -> bool:
        """Delete hint."""
        try:
            hint = self.get_by_id(hint_id)
            if not hint:
                return False

            self.db.delete(hint)
            self.db.commit()
            logger.warning("Hint deleted: %s", hint_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error deleting hint %s: %s", hint_id, e, exc_info=True)
            raise


class ExerciseTestRepository:
    """Repository for Exercise Tests operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_exercise(self, exercise_id: str) -> List[ExerciseTestDB]:
        """Get all tests for an exercise."""
        return (
            self.db.query(ExerciseTestDB)
            .filter(ExerciseTestDB.exercise_id == exercise_id)
            .order_by(ExerciseTestDB.test_number)
            .all()
        )

    def get_by_exercise_ids(self, exercise_ids: List[str]) -> Dict[str, List[ExerciseTestDB]]:
        """
        FIX Cortez52: Batch load tests for multiple exercises to prevent N+1 queries.

        Args:
            exercise_ids: List of exercise IDs

        Returns:
            Dictionary mapping exercise_id to list of tests
        """
        if not exercise_ids:
            return {}

        tests = (
            self.db.query(ExerciseTestDB)
            .filter(ExerciseTestDB.exercise_id.in_(exercise_ids))
            .order_by(ExerciseTestDB.exercise_id, ExerciseTestDB.test_number)
            .all()
        )

        result: Dict[str, List[ExerciseTestDB]] = defaultdict(list)
        for test in tests:
            result[test.exercise_id].append(test)

        return dict(result)

    def get_visible_tests(self, exercise_id: str) -> List[ExerciseTestDB]:
        """Get only visible tests (for students)."""
        return (
            self.db.query(ExerciseTestDB)
            .filter(
                ExerciseTestDB.exercise_id == exercise_id,
                ExerciseTestDB.is_hidden.is_(False)
            )
            .order_by(ExerciseTestDB.test_number)
            .all()
        )

    def get_hidden_tests(self, exercise_id: str) -> List[ExerciseTestDB]:
        """Get only hidden tests (for evaluation)."""
        return (
            self.db.query(ExerciseTestDB)
            .filter(
                ExerciseTestDB.exercise_id == exercise_id,
                ExerciseTestDB.is_hidden.is_(True)
            )
            .order_by(ExerciseTestDB.test_number)
            .all()
        )

    def get_by_id(self, test_id: str) -> Optional[ExerciseTestDB]:
        """Get test by ID."""
        return self.db.query(ExerciseTestDB).filter(ExerciseTestDB.id == test_id).first()

    def create(self, test: ExerciseTestDB) -> ExerciseTestDB:
        """Create new test."""
        try:
            self.db.add(test)
            self.db.commit()
            self.db.refresh(test)
            logger.info("Test created: exercise %s, test #%s", test.exercise_id, test.test_number)
            return test
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating test: %s", e, exc_info=True)
            raise

    def create_batch(self, tests: List[ExerciseTestDB]) -> List[ExerciseTestDB]:
        """Create multiple tests at once."""
        try:
            self.db.add_all(tests)
            self.db.commit()
            for test in tests:
                self.db.refresh(test)
            logger.info("Batch created %s tests", len(tests))
            return tests
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error batch creating tests: %s", e, exc_info=True)
            raise

    def update(self, test_id: str, updates: dict) -> Optional[ExerciseTestDB]:
        """Update test."""
        try:
            test = self.get_by_id(test_id)
            if not test:
                return None

            for key, value in updates.items():
                if hasattr(test, key):
                    setattr(test, key, value)

            self.db.commit()
            self.db.refresh(test)
            logger.info("Test updated: %s", test_id)
            return test
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error updating test %s: %s", test_id, e, exc_info=True)
            raise

    def delete(self, test_id: str) -> bool:
        """Delete test."""
        try:
            test = self.get_by_id(test_id)
            if not test:
                return False

            self.db.delete(test)
            self.db.commit()
            logger.warning("Test deleted: %s", test_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error deleting test %s: %s", test_id, e, exc_info=True)
            raise


class ExerciseAttemptRepository:
    """Repository for Exercise Attempt operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_exercise_and_student(
        self, exercise_id: str, student_id: str
    ) -> List[ExerciseAttemptDB]:
        """Get all attempts for an exercise by a student."""
        return (
            self.db.query(ExerciseAttemptDB)
            .filter(
                ExerciseAttemptDB.exercise_id == exercise_id,
                ExerciseAttemptDB.student_id == student_id
            )
            .order_by(ExerciseAttemptDB.attempt_number)
            .all()
        )

    def get_latest_attempt(
        self, exercise_id: str, student_id: str
    ) -> Optional[ExerciseAttemptDB]:
        """Get the latest attempt for an exercise by a student."""
        return (
            self.db.query(ExerciseAttemptDB)
            .filter(
                ExerciseAttemptDB.exercise_id == exercise_id,
                ExerciseAttemptDB.student_id == student_id
            )
            .order_by(ExerciseAttemptDB.attempt_number.desc())
            .first()
        )

    def get_by_id(self, attempt_id: str) -> Optional[ExerciseAttemptDB]:
        """Get attempt by ID."""
        return self.db.query(ExerciseAttemptDB).filter(ExerciseAttemptDB.id == attempt_id).first()

    def create(self, attempt: ExerciseAttemptDB) -> ExerciseAttemptDB:
        """Create new attempt."""
        try:
            self.db.add(attempt)
            self.db.commit()
            self.db.refresh(attempt)
            logger.info(
                "Attempt created: exercise %s, student %s, attempt #%s",
                attempt.exercise_id, attempt.student_id, attempt.attempt_number
            )
            return attempt
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating attempt: %s", e, exc_info=True)
            raise

    def update(self, attempt_id: str, updates: dict) -> Optional[ExerciseAttemptDB]:
        """Update attempt."""
        try:
            attempt = self.get_by_id(attempt_id)
            if not attempt:
                return None

            for key, value in updates.items():
                if hasattr(attempt, key):
                    setattr(attempt, key, value)

            attempt.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(attempt)
            logger.info("Attempt updated: %s", attempt_id)
            return attempt
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error updating attempt %s: %s", attempt_id, e, exc_info=True)
            raise

    def count_attempts(self, exercise_id: str, student_id: str) -> int:
        """Count attempts for an exercise by a student."""
        return (
            self.db.query(ExerciseAttemptDB)
            .filter(
                ExerciseAttemptDB.exercise_id == exercise_id,
                ExerciseAttemptDB.student_id == student_id
            )
            .count()
        )


class RubricCriterionRepository:
    """Repository for Exercise Rubric Criterion operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_exercise(self, exercise_id: str) -> List[ExerciseRubricCriterionDB]:
        """Get all criteria for an exercise."""
        return (
            self.db.query(ExerciseRubricCriterionDB)
            .options(selectinload(ExerciseRubricCriterionDB.levels))
            .filter(ExerciseRubricCriterionDB.exercise_id == exercise_id)
            .order_by(ExerciseRubricCriterionDB.order)
            .all()
        )

    def get_by_id(self, criterion_id: str) -> Optional[ExerciseRubricCriterionDB]:
        """Get criterion by ID."""
        return (
            self.db.query(ExerciseRubricCriterionDB)
            .options(selectinload(ExerciseRubricCriterionDB.levels))
            .filter(ExerciseRubricCriterionDB.id == criterion_id)
            .first()
        )

    def create(self, criterion: ExerciseRubricCriterionDB) -> ExerciseRubricCriterionDB:
        """Create new criterion."""
        try:
            self.db.add(criterion)
            self.db.commit()
            self.db.refresh(criterion)
            logger.info("Criterion created: %s - %s", criterion.id, criterion.name)
            return criterion
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating criterion: %s", e, exc_info=True)
            raise

    def delete(self, criterion_id: str) -> bool:
        """Delete criterion and its levels."""
        try:
            criterion = self.get_by_id(criterion_id)
            if not criterion:
                return False

            self.db.delete(criterion)
            self.db.commit()
            logger.warning("Criterion deleted: %s", criterion_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error deleting criterion %s: %s", criterion_id, e, exc_info=True)
            raise


class RubricLevelRepository:
    """Repository for Exercise Rubric Level operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_criterion(self, criterion_id: str) -> List[RubricLevelDB]:
        """Get all levels for a criterion."""
        return (
            self.db.query(RubricLevelDB)
            .filter(RubricLevelDB.criterion_id == criterion_id)
            .order_by(RubricLevelDB.level)
            .all()
        )

    def get_by_id(self, level_id: str) -> Optional[RubricLevelDB]:
        """Get level by ID."""
        return self.db.query(RubricLevelDB).filter(RubricLevelDB.id == level_id).first()

    def create(self, level: RubricLevelDB) -> RubricLevelDB:
        """Create new level."""
        try:
            self.db.add(level)
            self.db.commit()
            self.db.refresh(level)
            logger.info("Level created: criterion %s, level %s", level.criterion_id, level.level)
            return level
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating level: %s", e, exc_info=True)
            raise

    def delete(self, level_id: str) -> bool:
        """Delete level."""
        try:
            level = self.get_by_id(level_id)
            if not level:
                return False

            self.db.delete(level)
            self.db.commit()
            logger.warning("Level deleted: %s", level_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error deleting level %s: %s", level_id, e, exc_info=True)
            raise
