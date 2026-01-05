"""
LTI Repositories - LTI Deployment and Session operations.

Cortez46: Extracted from repositories.py (5,134 lines)
FIX Cortez83: Added try/except with rollback for database operations

SPRINT 6 - HU-SYS-010: Integración LTI con Moodle
"""
from typing import List, Optional
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from backend.core.constants import utc_now
from ..models import LTIDeploymentDB, LTISessionDB
from .base import BaseRepository

logger = logging.getLogger(__name__)


class LTIDeploymentRepository(BaseRepository):
    """
    Repository for LTI deployment operations.

    SPRINT 6 - HU-SYS-010: Integración LTI con Moodle
    """

    def create(
        self,
        platform_name: str,
        issuer: str,
        client_id: str,
        deployment_id: str,
        auth_login_url: str,
        auth_token_url: str,
        public_keyset_url: str,
        access_token_url: Optional[str] = None,
    ) -> LTIDeploymentDB:
        """
        Create a new LTI deployment.

        Args:
            platform_name: Platform name (Moodle, Canvas, etc.)
            issuer: LTI issuer URL
            client_id: OAuth2 client ID
            deployment_id: LTI deployment ID
            auth_login_url: OIDC auth login URL
            auth_token_url: OAuth2 token URL
            public_keyset_url: JWKS URL
            access_token_url: Optional access token URL

        Returns:
            Created LTIDeploymentDB instance
        """
        deployment = LTIDeploymentDB(
            id=str(uuid4()),
            platform_name=platform_name,
            issuer=issuer,
            client_id=client_id,
            deployment_id=deployment_id,
            auth_login_url=auth_login_url,
            auth_token_url=auth_token_url,
            public_keyset_url=public_keyset_url,
            access_token_url=access_token_url,
            is_active=True,
        )
        # FIX Cortez83: Added try/except with rollback
        try:
            self.db.add(deployment)
            self.db.commit()
            self.db.refresh(deployment)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create LTI deployment: %s", str(e), exc_info=True)
            raise

        logger.info(
            "LTI deployment created: %s (%s)",
            deployment.id,
            platform_name,
            extra={
                "deployment_db_id": deployment.id,
                "platform_name": platform_name,
                "issuer": issuer,
                "deployment_id": deployment_id,
            },
        )
        return deployment

    def get_by_id(self, deployment_db_id: str) -> Optional[LTIDeploymentDB]:
        """Get deployment by database ID."""
        return (
            self.db.query(LTIDeploymentDB)
            .filter(LTIDeploymentDB.id == deployment_db_id)
            .first()
        )

    def get_by_issuer_and_deployment(
        self, issuer: str, deployment_id: str
    ) -> Optional[LTIDeploymentDB]:
        """Get deployment by issuer + deployment_id (unique constraint)."""
        return (
            self.db.query(LTIDeploymentDB)
            .filter(
                LTIDeploymentDB.issuer == issuer,
                LTIDeploymentDB.deployment_id == deployment_id,
            )
            .first()
        )

    def get_active_deployments(self) -> List[LTIDeploymentDB]:
        """Get all active LTI deployments."""
        # FIX Cortez84 MED-REPO-007: Use .is_(True) instead of == True
        return (
            self.db.query(LTIDeploymentDB)
            .filter(LTIDeploymentDB.is_active.is_(True))
            .order_by(LTIDeploymentDB.platform_name)
            .all()
        )

    def deactivate(self, deployment_db_id: str) -> Optional[LTIDeploymentDB]:
        """Deactivate an LTI deployment."""
        deployment = self.get_by_id(deployment_db_id)
        if not deployment:
            return None

        deployment.is_active = False
        deployment.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(deployment)

        logger.info(
            "LTI deployment deactivated: %s",
            deployment.id,
            extra={"deployment_db_id": deployment.id},
        )
        return deployment


class LTISessionRepository(BaseRepository):
    """
    Repository for LTI session operations.

    SPRINT 6 - HU-SYS-010: Integración LTI con Moodle
    """

    def create(
        self,
        deployment_id: str,
        lti_user_id: str,
        resource_link_id: str,
        lti_user_name: Optional[str] = None,
        lti_user_email: Optional[str] = None,
        lti_context_id: Optional[str] = None,
        lti_context_label: Optional[str] = None,
        lti_context_title: Optional[str] = None,
        session_id: Optional[str] = None,
        launch_token: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> LTISessionDB:
        """
        Create a new LTI session.

        Args:
            deployment_id: LTI deployment ID (FK)
            lti_user_id: User ID from Moodle
            resource_link_id: Resource link ID from LTI launch
            lti_user_name: Optional user name
            lti_user_email: Optional user email
            lti_context_id: Optional course ID
            lti_context_label: Optional course code
            lti_context_title: Optional course name
            session_id: Mapped AI-Native session ID
            launch_token: JWT token from LTI launch
            locale: User's locale

        Returns:
            Created LTISessionDB instance
        """
        lti_session = LTISessionDB(
            id=str(uuid4()),
            deployment_id=deployment_id,
            lti_user_id=lti_user_id,
            lti_user_name=lti_user_name,
            lti_user_email=lti_user_email,
            lti_context_id=lti_context_id,
            lti_context_label=lti_context_label,
            lti_context_title=lti_context_title,
            resource_link_id=resource_link_id,
            session_id=session_id,
            launch_token=launch_token,
            locale=locale,
        )
        # FIX Cortez83: Added try/except with rollback
        try:
            self.db.add(lti_session)
            self.db.commit()
            self.db.refresh(lti_session)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create LTI session: %s", str(e), exc_info=True)
            raise

        logger.info(
            "LTI session created: %s for user %s",
            lti_session.id,
            lti_user_id,
            extra={
                "lti_session_id": lti_session.id,
                "lti_user_id": lti_user_id,
                "session_id": session_id,
            },
        )
        return lti_session

    def get_by_id(self, lti_session_id: str) -> Optional[LTISessionDB]:
        """Get LTI session by ID."""
        return (
            self.db.query(LTISessionDB)
            .filter(LTISessionDB.id == lti_session_id)
            .first()
        )

    def get_by_session_id(self, session_id: str) -> Optional[LTISessionDB]:
        """Get LTI session by AI-Native session ID."""
        return (
            self.db.query(LTISessionDB)
            .filter(LTISessionDB.session_id == session_id)
            .first()
        )

    def get_by_lti_user(self, lti_user_id: str) -> List[LTISessionDB]:
        """Get all LTI sessions for a user."""
        return (
            self.db.query(LTISessionDB)
            .filter(LTISessionDB.lti_user_id == lti_user_id)
            .order_by(desc(LTISessionDB.created_at))
            .all()
        )

    def link_to_session(
        self, lti_session_id: str, session_id: str
    ) -> Optional[LTISessionDB]:
        """Link LTI session to AI-Native session."""
        lti_session = self.get_by_id(lti_session_id)
        if not lti_session:
            return None

        lti_session.session_id = session_id
        lti_session.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(lti_session)

        logger.info(
            "LTI session linked to AI-Native session: %s -> %s",
            lti_session.id,
            session_id,
            extra={"lti_session_id": lti_session.id, "session_id": session_id},
        )
        return lti_session
