"""
User Repository - User authentication and authorization operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)

Provides:
- UserRepository: CRUD operations for users
- Role management
- Authentication utilities (password, login tracking)
"""
from typing import List, Optional
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, text, exists

from ..models import UserDB
from backend.core.constants import utc_now

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user authentication and authorization operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        student_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
    ) -> UserDB:
        """
        Create a new user.

        Args:
            email: User email (unique)
            username: Username (unique)
            hashed_password: Bcrypt hashed password
            full_name: Optional full name
            student_id: Optional student ID (for linking to StudentProfileDB)
            roles: List of roles (default: ["student"])

        Returns:
            Created UserDB instance
        """
        if roles is None:
            roles = ["student"]

        try:
            user = UserDB(
                id=str(uuid4()),
                email=email.lower(),
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                student_id=student_id,
                roles=roles,
                is_active=True,
                is_verified=False,
                login_count=0,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(
                "User created successfully",
                extra={"user_id": user.id, "email": user.email, "roles": user.roles},
            )
            return user
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create user: %s", e, extra={"email": email}, exc_info=True)
            raise

    def get_by_id(self, user_id: str) -> Optional[UserDB]:
        """Get user by ID."""
        return self.db.query(UserDB).filter(UserDB.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserDB]:
        """Get user by email (case-insensitive)."""
        return (
            self.db.query(UserDB)
            .filter(UserDB.email == email.lower())
            .first()
        )

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email without loading full object."""
        return self.db.query(
            exists().where(UserDB.email == email.lower())
        ).scalar()

    def get_by_username(self, username: str) -> Optional[UserDB]:
        """Get user by username."""
        return (
            self.db.query(UserDB)
            .filter(UserDB.username == username)
            .first()
        )

    def get_by_student_id(self, student_id: str) -> Optional[UserDB]:
        """Get user by student_id."""
        return (
            self.db.query(UserDB)
            .filter(UserDB.student_id == student_id)
            .first()
        )

    def get_all(
        self,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserDB]:
        """
        Get all users with pagination.

        Args:
            include_inactive: If True, include inactive users
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of UserDB instances
        """
        query = self.db.query(UserDB).order_by(desc(UserDB.created_at))
        if not include_inactive:
            query = query.filter(UserDB.is_active == True)
        return query.limit(limit).offset(offset).all()

    def get_by_role(self, role: str) -> List[UserDB]:
        """
        Get all users with a specific role.

        Uses database-specific optimizations:
        - PostgreSQL: ARRAY contains operator (@>) with GIN index
        - SQLite: LIKE on JSON for reasonable performance

        Args:
            role: Role name (e.g., "student", "instructor", "admin")

        Returns:
            List of UserDB instances with the role
        """
        dialect_name = self.db.bind.dialect.name if self.db.bind else "unknown"

        if dialect_name == "postgresql":
            return (
                self.db.query(UserDB)
                .filter(UserDB.is_active == True)
                .filter(text("roles @> ARRAY[:role]::varchar[]"))
                .params(role=role)
                .all()
            )
        elif dialect_name == "sqlite":
            return (
                self.db.query(UserDB)
                .filter(UserDB.is_active == True)
                .filter(text("roles LIKE :pattern"))
                .params(pattern=f'%"{role}"%')
                .all()
            )
        else:
            all_users = self.db.query(UserDB).filter(UserDB.is_active == True).all()
            return [user for user in all_users if role in user.roles]

    def update_password(self, user_id: str, new_hashed_password: str) -> Optional[UserDB]:
        """
        Update user password.

        Args:
            user_id: User ID
            new_hashed_password: New bcrypt hashed password

        Returns:
            Updated UserDB if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.hashed_password = new_hashed_password
        user.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(user)

        logger.info("User password updated", extra={"user_id": user.id})
        return user

    def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> Optional[UserDB]:
        """
        Update user profile.

        Args:
            user_id: User ID
            full_name: New full name (optional)
            student_id: New student ID (optional)

        Returns:
            Updated UserDB if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        if full_name is not None:
            user.full_name = full_name
        if student_id is not None:
            user.student_id = student_id

        user.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(user)

        logger.info("User profile updated", extra={"user_id": user.id})
        return user

    def add_role(self, user_id: str, role: str) -> Optional[UserDB]:
        """
        Add role to user.

        Args:
            user_id: User ID
            role: Role to add

        Returns:
            Updated UserDB if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        if role not in user.roles:
            user.roles = user.roles + [role]
            user.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(user)

            logger.info(
                "Role added to user", extra={"user_id": user.id, "role": role}
            )

        return user

    def delete_role(self, user_id: str, role: str) -> Optional[UserDB]:
        """
        Delete role from user.

        Args:
            user_id: User ID
            role: Role to delete

        Returns:
            Updated UserDB if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        if role in user.roles:
            user.roles = [r for r in user.roles if r != role]
            user.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(user)

            logger.info(
                "Role removed from user", extra={"user_id": user.id, "role": role}
            )

        return user

    def update_last_login(self, user_id: str) -> Optional[UserDB]:
        """
        Update last login timestamp and increment login count (atomic).

        Args:
            user_id: User ID

        Returns:
            Updated UserDB if found, None otherwise
        """
        try:
            rows_updated = self.db.query(UserDB).filter(UserDB.id == user_id).update(
                {
                    UserDB.last_login: utc_now(),
                    UserDB.login_count: UserDB.login_count + 1
                },
                synchronize_session='fetch'
            )

            if rows_updated == 0:
                return None

            self.db.commit()
            user = self.get_by_id(user_id)

            logger.info(
                "User login recorded",
                extra={"user_id": user_id, "login_count": user.login_count if user else 0},
            )
            return user
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update last login for user %s: %s", user_id, e, exc_info=True)
            raise

    def verify_user(self, user_id: str) -> Optional[UserDB]:
        """
        Mark user as verified (after email verification).

        Args:
            user_id: User ID

        Returns:
            Updated UserDB if found, None otherwise
        """
        try:
            rows_updated = self.db.query(UserDB).filter(UserDB.id == user_id).update(
                {
                    UserDB.is_verified: True,
                    UserDB.updated_at: utc_now()
                },
                synchronize_session='fetch'
            )

            if rows_updated == 0:
                return None

            self.db.commit()
            user = self.get_by_id(user_id)
            logger.info("User verified", extra={"user_id": user_id})
            return user
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to verify user %s: %s", user_id, e, exc_info=True)
            raise

    def deactivate_user(self, user_id: str) -> Optional[UserDB]:
        """
        Deactivate user account.

        Args:
            user_id: User ID

        Returns:
            Updated UserDB if found, None otherwise
        """
        try:
            rows_updated = self.db.query(UserDB).filter(UserDB.id == user_id).update(
                {
                    UserDB.is_active: False,
                    UserDB.updated_at: utc_now()
                },
                synchronize_session='fetch'
            )

            if rows_updated == 0:
                return None

            self.db.commit()
            user = self.get_by_id(user_id)
            logger.info("User deactivated", extra={"user_id": user_id})
            return user
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to deactivate user %s: %s", user_id, e, exc_info=True)
            raise

    def reactivate_user(self, user_id: str) -> Optional[UserDB]:
        """
        Reactivate user account.

        Args:
            user_id: User ID

        Returns:
            Updated UserDB if found, None otherwise
        """
        try:
            rows_updated = self.db.query(UserDB).filter(UserDB.id == user_id).update(
                {
                    UserDB.is_active: True,
                    UserDB.updated_at: utc_now()
                },
                synchronize_session='fetch'
            )

            if rows_updated == 0:
                return None

            self.db.commit()
            user = self.get_by_id(user_id)
            logger.info("User reactivated", extra={"user_id": user_id})
            return user
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to reactivate user %s: %s", user_id, e, exc_info=True)
            raise

    def delete(self, user_id: str) -> bool:
        """
        Delete user (hard delete - use with caution!).

        Note: In production, consider soft delete (deactivate_user) instead.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()

        logger.warning("User deleted (hard delete)", extra={"user_id": user.id})
        return True
