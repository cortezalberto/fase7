"""
LTI 1.3 Router - Learning Tools Interoperability endpoints.

HU-SYS-010: Integracion con Moodle via LTI 1.3

This router implements the LTI 1.3 protocol for integration with
Learning Management Systems like Moodle, Canvas, and Blackboard.

IMPORTANT: This router is NOT registered in main.py yet.
To enable LTI integration, add to main.py:
    from backend.api.routers import lti
    app.include_router(lti.router, prefix="/api/v1/lti", tags=["lti"])

Endpoints:
- POST /login: OIDC login initiation (Step 1)
- POST /launch: LTI launch callback (Step 2)
- GET /jwks: Public key set for token validation
- POST /deployments: Create new deployment (admin)
- GET /deployments: List deployments (admin)
- DELETE /deployments/{id}: Deactivate deployment (admin)

Security:
- Uses RSA key pairs for JWT signing/verification
- Implements state/nonce for OIDC security
- Validates platform JWKS for token verification

FIX Cortez67: Replaced unbounded caches with TTLCache to prevent memory leaks.
"""
import hashlib
import hmac
import logging
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError, jwt
from jose.constants import ALGORITHMS
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from backend.api.config import SECRET_KEY
from backend.api.deps import get_db, get_current_user, require_role
from backend.api.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseOperationError,
    ValidationError,
)
from backend.database.repositories.lti_repository import (
    LTIDeploymentRepository,
    LTISessionRepository,
)
from backend.database.repositories.session_repository import SessionRepository
from backend.database.repositories.user_repository import UserRepository
from backend.database.repositories.activity_repository import ActivityRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Configuration Constants
# =============================================================================

# LTI state expiration (10 minutes for OIDC flow)
LTI_STATE_EXPIRATION_MINUTES = int(os.getenv("LTI_STATE_EXPIRATION_MINUTES", "10"))

# LTI nonce expiration (1 hour to prevent replay attacks)
LTI_NONCE_EXPIRATION_HOURS = int(os.getenv("LTI_NONCE_EXPIRATION_HOURS", "1"))

# Cache TTL for platform JWKS (1 hour)
JWKS_CACHE_TTL_SECONDS = int(os.getenv("LTI_JWKS_CACHE_TTL_SECONDS", "3600"))

# FIX Cortez67: Cache size limits to prevent memory exhaustion
LTI_STATE_CACHE_MAXSIZE = int(os.getenv("LTI_STATE_CACHE_MAXSIZE", "10000"))
LTI_NONCE_CACHE_MAXSIZE = int(os.getenv("LTI_NONCE_CACHE_MAXSIZE", "100000"))
LTI_JWKS_CACHE_MAXSIZE = int(os.getenv("LTI_JWKS_CACHE_MAXSIZE", "100"))

# FIX Cortez67: Thread-safe TTL caches with size limits
# These automatically evict entries after TTL expires and when size limit is reached
_state_cache: TTLCache = TTLCache(
    maxsize=LTI_STATE_CACHE_MAXSIZE,
    ttl=LTI_STATE_EXPIRATION_MINUTES * 60  # Convert to seconds
)
_nonce_cache: TTLCache = TTLCache(
    maxsize=LTI_NONCE_CACHE_MAXSIZE,
    ttl=LTI_NONCE_EXPIRATION_HOURS * 3600  # Convert to seconds
)
_jwks_cache: TTLCache = TTLCache(
    maxsize=LTI_JWKS_CACHE_MAXSIZE,
    ttl=JWKS_CACHE_TTL_SECONDS
)
_cache_lock = threading.Lock()

logger.info(
    "LTI caches initialized: state(max=%d, ttl=%dm), nonce(max=%d, ttl=%dh), jwks(max=%d, ttl=%ds)",
    LTI_STATE_CACHE_MAXSIZE, LTI_STATE_EXPIRATION_MINUTES,
    LTI_NONCE_CACHE_MAXSIZE, LTI_NONCE_EXPIRATION_HOURS,
    LTI_JWKS_CACHE_MAXSIZE, JWKS_CACHE_TTL_SECONDS
)


# =============================================================================
# Pydantic Schemas
# =============================================================================

class LTIDeploymentCreate(BaseModel):
    """Schema for creating a new LTI deployment."""
    platform_name: str = Field(..., min_length=1, max_length=100)
    issuer: str = Field(..., min_length=1, description="LTI issuer URL")
    client_id: str = Field(..., min_length=1, description="OAuth2 client ID")
    deployment_id: str = Field(..., min_length=1, description="LTI deployment ID")
    auth_login_url: HttpUrl = Field(..., description="OIDC auth login URL")
    auth_token_url: HttpUrl = Field(..., description="OAuth2 token URL")
    public_keyset_url: HttpUrl = Field(..., description="JWKS URL")
    access_token_url: Optional[HttpUrl] = Field(None, description="AGS token URL")


class LTIDeploymentResponse(BaseModel):
    """Schema for LTI deployment responses."""
    id: str
    platform_name: str
    issuer: str
    client_id: str
    deployment_id: str
    auth_login_url: str
    auth_token_url: str
    public_keyset_url: str
    access_token_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class LTILaunchResponse(BaseModel):
    """Schema for successful LTI launch."""
    success: bool = True
    session_id: str
    lti_session_id: str
    user_name: Optional[str]  # Nombre completo del estudiante
    user_email: Optional[str]
    context_title: Optional[str]  # Nombre del curso
    context_label: Optional[str]  # Comision (ej: "PROG1-A")
    resource_link_id: str
    resource_link_title: Optional[str]  # Nombre de la actividad
    redirect_url: str
    # Activity matching (Cortez65.1)
    activity_id: Optional[str] = None  # AI-Native activity ID if matched
    activity_title: Optional[str] = None  # AI-Native activity title if matched
    activity_matched: bool = False  # True if Moodle resource was matched to an AI-Native activity


class MoodleLinkRequest(BaseModel):
    """Schema for linking an activity to Moodle."""
    activity_id: str = Field(..., description="AI-Native activity ID to link")
    moodle_course_id: str = Field(..., description="Moodle context_id")
    moodle_course_name: str = Field(..., description="Moodle course name")
    moodle_course_label: Optional[str] = Field(None, description="Moodle commission code")
    moodle_resource_name: Optional[str] = Field(None, description="Moodle activity name to match")


# =============================================================================
# Helper Functions
# =============================================================================

def _generate_state() -> str:
    """Generate cryptographically secure state parameter for OIDC."""
    return secrets.token_urlsafe(32)


def _generate_nonce() -> str:
    """Generate cryptographically secure nonce for replay protection."""
    return secrets.token_urlsafe(32)


def _store_state(state: str, data: Dict[str, Any]) -> None:
    """
    Store state data for OIDC flow verification.

    FIX Cortez67: Thread-safe with TTLCache (automatic expiration).
    """
    # FIX Cortez67: TTLCache handles expiration automatically
    with _cache_lock:
        _state_cache[state] = {"data": data}
    logger.debug("Stored OIDC state: %s", state[:8])


def _verify_and_consume_state(state: str) -> Optional[Dict[str, Any]]:
    """
    Verify state parameter and consume it (one-time use).

    FIX Cortez67: Thread-safe access to TTLCache.

    Returns:
        State data if valid, None if invalid or expired.
    """
    with _cache_lock:
        if state not in _state_cache:
            logger.warning("State not found in cache: %s", state[:8] if state else "None")
            return None

        # FIX Cortez67: pop() is atomic with TTLCache
        cached = _state_cache.pop(state)  # Consume (one-time use)
        # TTLCache automatically expires entries, no need to check manually
        return cached["data"]


def _store_nonce(nonce: str) -> None:
    """
    Store nonce to prevent replay attacks.

    FIX Cortez67: Thread-safe with TTLCache (automatic expiration).
    """
    with _cache_lock:
        _nonce_cache[nonce] = True  # Value doesn't matter, just need the key


def _verify_nonce(nonce: str) -> bool:
    """
    Verify nonce hasn't been used before (replay protection).

    FIX Cortez67: Thread-safe access to TTLCache.

    Returns:
        True if nonce is valid and unused, False otherwise.
    """
    with _cache_lock:
        if nonce in _nonce_cache:
            # Nonce already used - potential replay attack
            logger.warning("Nonce reuse detected: %s", nonce[:8])
            return False
    return True


def _cleanup_expired_caches() -> None:
    """
    Clean up expired entries from caches.

    FIX Cortez67: TTLCache handles expiration automatically via its internal
    mechanism. This function now just triggers cache expiration and logs stats.
    """
    # FIX Cortez67: TTLCache automatically expires entries on access
    # We just need to trigger expire() to clean up
    with _cache_lock:
        # TTLCache.expire() removes all expired entries
        _state_cache.expire()
        _nonce_cache.expire()
        _jwks_cache.expire()

    # Log cache stats for monitoring
    logger.debug(
        "LTI cache stats: states=%d, nonces=%d, jwks=%d",
        len(_state_cache), len(_nonce_cache), len(_jwks_cache)
    )


async def _fetch_platform_jwks(jwks_url: str) -> Dict[str, Any]:
    """
    Fetch and cache platform's JWKS for token verification.

    FIX Cortez67: Thread-safe access with TTLCache (automatic expiration).

    Args:
        jwks_url: URL of the platform's JWKS endpoint

    Returns:
        JWKS dictionary with keys

    Raises:
        AuthenticationError: If JWKS cannot be fetched
    """
    # FIX Cortez67: Thread-safe check of TTLCache
    with _cache_lock:
        if jwks_url in _jwks_cache:
            # TTLCache automatically expires entries, so if it's here it's valid
            return _jwks_cache[jwks_url]

    # Fetch fresh JWKS
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
    except httpx.HTTPError as e:
        logger.error("Failed to fetch JWKS from %s: %s", jwks_url, str(e))
        raise AuthenticationError(
            message="Failed to verify platform credentials",
            auth_type="lti_jwks"
        )

    # FIX Cortez67: Thread-safe cache update (TTL handles expiration)
    with _cache_lock:
        _jwks_cache[jwks_url] = jwks

    return jwks


async def _verify_lti_token(
    id_token: str,
    deployment: Any,
) -> Dict[str, Any]:
    """
    Verify LTI 1.3 JWT token from platform.

    Args:
        id_token: The JWT token from the platform
        deployment: LTIDeploymentDB instance with platform config

    Returns:
        Decoded token claims

    Raises:
        AuthenticationError: If token is invalid
    """
    # Fetch platform's JWKS
    jwks = await _fetch_platform_jwks(deployment.public_keyset_url)

    try:
        # Decode and verify the token
        # Note: jose library handles JWKS key lookup automatically
        claims = jwt.decode(
            id_token,
            jwks,
            algorithms=[ALGORITHMS.RS256],
            audience=deployment.client_id,
            issuer=deployment.issuer,
            options={
                "verify_at_hash": False,  # LTI doesn't use at_hash
            }
        )

        # Verify LTI-specific claims
        required_claims = [
            "https://purl.imsglobal.org/spec/lti/claim/message_type",
            "https://purl.imsglobal.org/spec/lti/claim/version",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id",
            "https://purl.imsglobal.org/spec/lti/claim/resource_link",
        ]

        for claim in required_claims:
            if claim not in claims:
                raise AuthenticationError(
                    message=f"Missing required LTI claim: {claim}",
                    auth_type="lti_claims"
                )

        # Verify deployment ID matches
        token_deployment_id = claims.get(
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
        )
        if token_deployment_id != deployment.deployment_id:
            raise AuthenticationError(
                message="Deployment ID mismatch",
                auth_type="lti_deployment"
            )

        return claims

    except JWTError as e:
        logger.error("JWT verification failed: %s", str(e))
        raise AuthenticationError(
            message="Invalid LTI token",
            auth_type="lti_jwt"
        )


def _extract_lti_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user and context information from LTI claims.

    Args:
        claims: Decoded JWT claims

    Returns:
        Dictionary with extracted user/context info
    """
    # User information
    user_id = claims.get("sub", "")
    user_name = claims.get("name", claims.get("given_name", ""))
    user_email = claims.get("email")

    # Context (course) information
    context = claims.get("https://purl.imsglobal.org/spec/lti/claim/context", {})
    context_id = context.get("id")
    context_label = context.get("label")
    context_title = context.get("title")

    # Resource link (activity) information
    resource_link = claims.get(
        "https://purl.imsglobal.org/spec/lti/claim/resource_link", {}
    )
    resource_link_id = resource_link.get("id", "")
    resource_link_title = resource_link.get("title", "")  # Activity name

    # Roles
    roles = claims.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])
    is_instructor = any("Instructor" in role for role in roles)
    is_student = any("Learner" in role for role in roles)

    # Locale
    locale = claims.get("locale")

    return {
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email,
        "context_id": context_id,
        "context_label": context_label,
        "context_title": context_title,
        "resource_link_id": resource_link_id,
        "resource_link_title": resource_link_title,
        "roles": roles,
        "is_instructor": is_instructor,
        "is_student": is_student,
        "locale": locale,
    }


# =============================================================================
# OIDC Endpoints (LTI Launch Flow)
# =============================================================================

@router.post("/login", response_class=HTMLResponse)
async def lti_login_initiation(
    request: Request,
    iss: str = Form(..., description="Issuer identifier"),
    login_hint: str = Form(..., description="Platform login hint"),
    target_link_uri: str = Form(..., description="Target launch URL"),
    lti_message_hint: Optional[str] = Form(None, description="LTI message hint"),
    client_id: Optional[str] = Form(None, description="Client ID (optional)"),
    lti_deployment_id: Optional[str] = Form(None, description="Deployment ID"),
    db: Session = Depends(get_db),
) -> Response:
    """
    LTI 1.3 OIDC Login Initiation (Step 1).

    This endpoint receives the initial login request from the LMS (Moodle).
    It generates state/nonce and redirects to the platform's auth endpoint.

    Flow:
    1. Platform (Moodle) POSTs to this endpoint with iss, login_hint
    2. We generate state/nonce for security
    3. We redirect user to platform's auth_login_url
    4. Platform authenticates user and POSTs back to /launch
    """
    logger.info(
        "LTI login initiation from issuer: %s",
        iss,
        extra={"issuer": iss, "target_link_uri": target_link_uri}
    )

    # Clean up expired cache entries
    _cleanup_expired_caches()

    # Find the deployment configuration
    lti_deployment_repo = LTIDeploymentRepository(db)

    # Try to find deployment by issuer + deployment_id
    deployment = None
    if lti_deployment_id:
        deployment = lti_deployment_repo.get_by_issuer_and_deployment(iss, lti_deployment_id)

    # If not found, try to find any active deployment for this issuer
    if not deployment:
        deployments = lti_deployment_repo.get_active_deployments()
        deployment = next((d for d in deployments if d.issuer == iss), None)

    if not deployment:
        logger.error("No LTI deployment found for issuer: %s", iss)
        raise AuthenticationError(
            message="Unknown LTI platform",
            auth_type="lti_deployment"
        )

    if not deployment.is_active:
        raise AuthenticationError(
            message="LTI deployment is disabled",
            auth_type="lti_deployment"
        )

    # Generate security parameters
    state = _generate_state()
    nonce = _generate_nonce()

    # Store state for verification in /launch
    _store_state(state, {
        "deployment_id": deployment.id,
        "target_link_uri": target_link_uri,
        "nonce": nonce,
    })

    # Store nonce for replay protection
    _store_nonce(nonce)

    # Build OIDC auth request URL
    auth_params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "client_id": deployment.client_id,
        "redirect_uri": target_link_uri,
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
    }

    if lti_message_hint:
        auth_params["lti_message_hint"] = lti_message_hint

    # Build query string
    query_string = "&".join(f"{k}={v}" for k, v in auth_params.items())
    auth_url = f"{deployment.auth_login_url}?{query_string}"

    logger.debug("Redirecting to platform auth: %s", deployment.auth_login_url)

    # Return redirect response
    return RedirectResponse(url=auth_url, status_code=302)


@router.post("/launch")
async def lti_launch(
    request: Request,
    id_token: str = Form(..., description="JWT token from platform"),
    state: str = Form(..., description="State parameter for verification"),
    db: Session = Depends(get_db),
) -> LTILaunchResponse:
    """
    LTI 1.3 Launch Callback (Step 2).

    This endpoint receives the authenticated launch from the LMS.
    It verifies the JWT token and creates an AI-Native session.

    Flow:
    1. Platform redirects user here with id_token and state
    2. We verify state matches what we stored
    3. We verify JWT signature using platform's JWKS
    4. We extract user/context claims
    5. We create LTI session and AI-Native session
    6. We return redirect URL to frontend
    """
    logger.info("LTI launch callback received")

    # Verify state parameter
    state_data = _verify_and_consume_state(state)
    if not state_data:
        raise AuthenticationError(
            message="Invalid or expired state parameter",
            auth_type="lti_state"
        )

    deployment_id = state_data["deployment_id"]
    stored_nonce = state_data["nonce"]

    # Get deployment
    lti_deployment_repo = LTIDeploymentRepository(db)
    deployment = lti_deployment_repo.get_by_id(deployment_id)

    if not deployment:
        raise AuthenticationError(
            message="Deployment not found",
            auth_type="lti_deployment"
        )

    # Verify the JWT token
    claims = await _verify_lti_token(id_token, deployment)

    # Verify nonce from token matches stored nonce
    token_nonce = claims.get("nonce")
    if token_nonce != stored_nonce:
        logger.warning("Nonce mismatch: expected %s, got %s", stored_nonce[:8], token_nonce[:8] if token_nonce else "None")
        raise AuthenticationError(
            message="Invalid nonce",
            auth_type="lti_nonce"
        )

    # Verify nonce hasn't been used before (replay protection)
    if not _verify_nonce(token_nonce):
        raise AuthenticationError(
            message="Nonce already used - possible replay attack",
            auth_type="lti_replay"
        )

    # Extract user and context information
    lti_info = _extract_lti_claims(claims)

    logger.info(
        "LTI launch verified for user: %s in context: %s",
        lti_info["user_id"],
        lti_info["context_title"],
        extra={
            "lti_user_id": lti_info["user_id"],
            "context_id": lti_info["context_id"],
            "resource_link_id": lti_info["resource_link_id"],
        }
    )

    # Create or find AI-Native user
    user_repo = UserRepository(db)

    # Try to find existing user by LTI user ID (stored in external_id)
    # For now, create a deterministic user_id from LTI info
    lti_user_hash = hashlib.sha256(
        f"{deployment.issuer}:{lti_info['user_id']}".encode()
    ).hexdigest()[:32]

    user = user_repo.get_by_id(lti_user_hash)
    if not user:
        # Create new user from LTI info
        try:
            user = user_repo.create(
                email=lti_info["user_email"] or f"lti_{lti_user_hash}@lti.local",
                hashed_password="",  # LTI users don't have passwords
                name=lti_info["user_name"] or "LTI User",
                role="teacher" if lti_info["is_instructor"] else "student",
            )
            # Update the user ID to our hash for consistency
            user.id = lti_user_hash
            db.commit()
            logger.info("Created new user from LTI: %s", lti_user_hash)
        except Exception as e:
            logger.error("Failed to create user from LTI: %s", str(e))
            db.rollback()
            raise DatabaseOperationError(
                operation="create_lti_user",
                details=str(e)
            )

    # Try to find matching AI-Native activity (Cortez65.1)
    activity_repo = ActivityRepository(db)
    matched_activity = None

    # Strategy 1: Match by course_id + resource_name (most specific)
    if lti_info["context_id"] and lti_info["resource_link_title"]:
        matched_activity = activity_repo.get_by_moodle_context(
            moodle_course_id=lti_info["context_id"],
            moodle_resource_name=lti_info["resource_link_title"],
        )

    # Strategy 2: Match by resource_name only (fallback)
    if not matched_activity and lti_info["resource_link_title"]:
        matched_activity = activity_repo.get_by_moodle_resource_name(
            moodle_resource_name=lti_info["resource_link_title"],
        )

    # Determine activity_id for session
    if matched_activity:
        session_activity_id = matched_activity.activity_id
        logger.info(
            "Matched Moodle resource '%s' to AI-Native activity '%s'",
            lti_info["resource_link_title"],
            matched_activity.activity_id,
        )
    else:
        # Use Moodle resource_link_id as fallback activity identifier
        session_activity_id = lti_info["resource_link_id"]
        logger.info(
            "No matching AI-Native activity for Moodle resource '%s', using resource_link_id",
            lti_info["resource_link_title"],
        )

    # Create AI-Native session
    session_repo = SessionRepository(db)
    try:
        session = session_repo.create_session(
            student_id=lti_user_hash,
            activity_id=session_activity_id,
            mode="tutor",  # Default to tutor mode for LTI launches
        )
        logger.info("Created AI-Native session: %s", session.id)
    except Exception as e:
        logger.error("Failed to create session: %s", str(e))
        db.rollback()
        raise DatabaseOperationError(
            operation="create_lti_session",
            details=str(e)
        )

    # Create LTI session record
    lti_session_repo = LTISessionRepository(db)
    try:
        lti_session = lti_session_repo.create(
            deployment_id=deployment.id,
            lti_user_id=lti_info["user_id"],
            resource_link_id=lti_info["resource_link_id"],
            resource_link_title=lti_info["resource_link_title"],  # Activity name
            lti_user_name=lti_info["user_name"],
            lti_user_email=lti_info["user_email"],
            lti_context_id=lti_info["context_id"],
            lti_context_label=lti_info["context_label"],
            lti_context_title=lti_info["context_title"],
            session_id=session.id,
            launch_token=id_token,  # Store for AGS later
            locale=lti_info["locale"],
        )
        logger.info("Created LTI session: %s", lti_session.id)
    except Exception as e:
        logger.error("Failed to create LTI session record: %s", str(e))
        db.rollback()
        raise DatabaseOperationError(
            operation="create_lti_session_record",
            details=str(e)
        )

    # Build frontend redirect URL
    # The frontend will detect LTI mode and render appropriately
    frontend_base_url = request.headers.get("Origin", "http://localhost:3000")
    redirect_url = f"{frontend_base_url}/tutor?session_id={session.id}&lti=true"

    return LTILaunchResponse(
        session_id=session.id,
        lti_session_id=lti_session.id,
        user_name=lti_info["user_name"],
        user_email=lti_info["user_email"],
        context_title=lti_info["context_title"],
        context_label=lti_info["context_label"],
        resource_link_id=lti_info["resource_link_id"],
        resource_link_title=lti_info["resource_link_title"],
        redirect_url=redirect_url,
        # Activity matching info (Cortez65.1)
        activity_id=matched_activity.activity_id if matched_activity else None,
        activity_title=matched_activity.title if matched_activity else None,
        activity_matched=matched_activity is not None,
    )


# =============================================================================
# JWKS Endpoint (for platform to verify our tokens)
# =============================================================================

@router.get("/jwks")
async def get_jwks() -> Dict[str, Any]:
    """
    Get AI-Native's public key set (JWKS).

    This endpoint exposes our public keys so that platforms can
    verify tokens we sign (for LTI Advantage services like AGS).

    Note: For MVP, we don't sign tokens for AGS yet.
    This endpoint returns an empty keyset.
    """
    # TODO: Implement when adding LTI Advantage (AGS) support
    # For now, return empty keyset
    return {"keys": []}


# =============================================================================
# Deployment Management Endpoints (Admin)
# =============================================================================

@router.post("/deployments", response_model=LTIDeploymentResponse)
async def create_deployment(
    deployment_data: LTIDeploymentCreate,
    db: Session = Depends(get_db),
    # FIX Cortez68 (CRIT-003): Add teacher/admin authentication
    current_user: dict = Depends(require_role("teacher")),
) -> LTIDeploymentResponse:
    """
    Create a new LTI deployment configuration.

    This endpoint is for administrators to register new LMS platforms.
    Each deployment represents a connection to a specific LMS (Moodle instance).

    Requires teacher role.
    """
    logger.info(
        "Creating LTI deployment: %s (%s)",
        deployment_data.platform_name,
        deployment_data.issuer
    )

    lti_deployment_repo = LTIDeploymentRepository(db)

    # Check if deployment already exists
    existing = lti_deployment_repo.get_by_issuer_and_deployment(
        deployment_data.issuer,
        deployment_data.deployment_id
    )
    if existing:
        raise ValidationError(
            field="deployment",
            message="Deployment already exists for this issuer + deployment_id"
        )

    try:
        deployment = lti_deployment_repo.create(
            platform_name=deployment_data.platform_name,
            issuer=deployment_data.issuer,
            client_id=deployment_data.client_id,
            deployment_id=deployment_data.deployment_id,
            auth_login_url=str(deployment_data.auth_login_url),
            auth_token_url=str(deployment_data.auth_token_url),
            public_keyset_url=str(deployment_data.public_keyset_url),
            access_token_url=str(deployment_data.access_token_url) if deployment_data.access_token_url else None,
        )
    except Exception as e:
        logger.error("Failed to create deployment: %s", str(e))
        db.rollback()
        raise DatabaseOperationError(
            operation="create_lti_deployment",
            details=str(e)
        )

    return LTIDeploymentResponse.model_validate(deployment)


@router.get("/deployments", response_model=List[LTIDeploymentResponse])
async def list_deployments(
    db: Session = Depends(get_db),
    # FIX Cortez68 (CRIT-003): Add teacher/admin authentication
    current_user: dict = Depends(require_role("teacher")),
) -> List[LTIDeploymentResponse]:
    """
    List all LTI deployments.

    Returns both active and inactive deployments.
    Requires teacher role.
    """
    lti_deployment_repo = LTIDeploymentRepository(db)
    deployments = lti_deployment_repo.get_active_deployments()

    return [LTIDeploymentResponse.model_validate(d) for d in deployments]


@router.delete("/deployments/{deployment_id}")
async def deactivate_deployment(
    deployment_id: str,
    db: Session = Depends(get_db),
    # FIX Cortez68 (CRIT-003): Add teacher/admin authentication
    current_user: dict = Depends(require_role("teacher")),
) -> Dict[str, str]:
    """
    Deactivate an LTI deployment.

    This soft-deletes the deployment by setting is_active=False.
    Existing LTI sessions remain but new launches will fail.

    Requires teacher role.
    """
    logger.info("Deactivating LTI deployment: %s", deployment_id)

    lti_deployment_repo = LTIDeploymentRepository(db)
    deployment = lti_deployment_repo.deactivate(deployment_id)

    if not deployment:
        raise ValidationError(
            field="deployment_id",
            message="Deployment not found"
        )

    return {"message": f"Deployment {deployment_id} deactivated"}


# =============================================================================
# Activity-Moodle Linking Endpoints (Cortez65.1)
# =============================================================================

@router.post("/activities/link")
async def link_activity_to_moodle(
    link_data: MoodleLinkRequest,
    db: Session = Depends(get_db),
    # FIX Cortez68 (CRIT-003): Add teacher authentication
    current_user: dict = Depends(require_role("teacher")),
) -> Dict[str, Any]:
    """
    Link an AI-Native activity to a Moodle course/resource.

    This allows automatic activity matching when students launch from Moodle.
    The teacher configures which AI-Native activity corresponds to which
    Moodle activity.

    Args:
        link_data: Moodle course and resource information to link

    Returns:
        Updated activity information
    """
    logger.info(
        "Linking activity '%s' to Moodle course '%s' resource '%s'",
        link_data.activity_id,
        link_data.moodle_course_id,
        link_data.moodle_resource_name,
    )

    activity_repo = ActivityRepository(db)
    activity = activity_repo.link_to_moodle(
        activity_id=link_data.activity_id,
        moodle_course_id=link_data.moodle_course_id,
        moodle_course_name=link_data.moodle_course_name,
        moodle_course_label=link_data.moodle_course_label,
        moodle_resource_name=link_data.moodle_resource_name,
    )

    if not activity:
        raise ValidationError(
            field="activity_id",
            message=f"Activity '{link_data.activity_id}' not found"
        )

    return {
        "success": True,
        "message": f"Activity '{activity.title}' linked to Moodle",
        "activity_id": activity.activity_id,
        "moodle_course_id": activity.moodle_course_id,
        "moodle_course_name": activity.moodle_course_name,
        "moodle_course_label": activity.moodle_course_label,
        "moodle_resource_name": activity.moodle_resource_name,
    }


@router.delete("/activities/{activity_id}/link")
async def unlink_activity_from_moodle(
    activity_id: str,
    db: Session = Depends(get_db),
    # FIX Cortez68 (CRIT-003): Add teacher authentication
    current_user: dict = Depends(require_role("teacher")),
) -> Dict[str, str]:
    """
    Remove Moodle link from an AI-Native activity.

    Args:
        activity_id: AI-Native activity ID to unlink

    Returns:
        Success message
    """
    logger.info("Unlinking activity '%s' from Moodle", activity_id)

    activity_repo = ActivityRepository(db)
    activity = activity_repo.unlink_from_moodle(activity_id)

    if not activity:
        raise ValidationError(
            field="activity_id",
            message=f"Activity '{activity_id}' not found"
        )

    return {"message": f"Activity '{activity.title}' unlinked from Moodle"}


@router.get("/activities/linked")
async def get_moodle_linked_activities(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
    db: Session = Depends(get_db),
    # FIX Cortez68 (CRIT-003): Add teacher authentication
    current_user: dict = Depends(require_role("teacher")),
) -> List[Dict[str, Any]]:
    """
    Get all activities that are linked to Moodle.

    Args:
        teacher_id: Optional filter by teacher

    Returns:
        List of linked activities with their Moodle configuration
    """
    activity_repo = ActivityRepository(db)
    activities = activity_repo.get_moodle_linked_activities(teacher_id)

    return [
        {
            "activity_id": a.activity_id,
            "title": a.title,
            "status": a.status,
            "moodle_course_id": a.moodle_course_id,
            "moodle_course_name": a.moodle_course_name,
            "moodle_course_label": a.moodle_course_label,
            "moodle_resource_name": a.moodle_resource_name,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in activities
    ]


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def lti_health() -> Dict[str, Any]:
    """
    LTI integration health check.

    Returns status of LTI caches and configuration.
    """
    return {
        "status": "ok",
        "state_cache_size": len(_state_cache),
        "nonce_cache_size": len(_nonce_cache),
        "jwks_cache_size": len(_jwks_cache),
        "message": "LTI router loaded but NOT registered in main.py",
    }
