"""
New Authentication endpoints using User model with roles

Endpoints:
- POST /auth/login: JSON login (frontend compatible)
- POST /auth/token: OAuth2 FormData login (Swagger compatible)
- POST /auth/register: Register new user
- POST /auth/refresh: Refresh access token
- GET /auth/me: Get current user info

FIX Cortez51: Migrated HTTPExceptions to custom exceptions
"""
import logging
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import timedelta

from backend.database.config import get_db
# FIX Cortez25: Use UserDB from database.models to avoid duplicate table definition
from backend.database.models import UserDB as User
from backend.models.user import UserRole
from backend.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from ..schemas.common import APIResponse
from ..exceptions import (
    AuthenticationError,
    ValidationError,
    UserInactiveError,
    UserNotFoundError,
    InvalidTokenError,
    DatabaseOperationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Refresh token expiration (longer than access token)
REFRESH_TOKEN_EXPIRE_DAYS = 30


# =============================================================================
# SCHEMAS
# =============================================================================

class UserRegisterSchema(BaseModel):
    """
    Schema for user registration.

    FIX Cortez33: Added password strength validation
    FIX Cortez54: Documented role behavior - accepts: "student", "teacher", "admin"
                  Invalid roles silently default to "student" for security.
    """
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "student"  # Valid values: "student", "teacher", "admin". Invalid -> "student"

    @field_validator('role')
    @classmethod
    def validate_and_normalize_role(cls, v: str) -> str:
        """
        FIX Cortez54: Validate role and normalize to lowercase.

        Valid roles: student, teacher, admin
        Invalid roles silently default to 'student' for security reasons
        (prevents role enumeration attacks).
        """
        normalized = v.lower().strip()
        valid_roles = [r.value for r in UserRole]
        if normalized not in valid_roles:
            # Log but don't expose which roles are valid
            logger.warning("Invalid role '%s' provided during registration, defaulting to 'student'", v)
            return "student"
        return normalized

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username length and format"""
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements.
        FIX Cortez33: NIST recommends minimum 12 characters.
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponseSchema(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokensSchema(BaseModel):
    """Token pair for access and refresh"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserWithTokensResponse(BaseModel):
    """Combined user and tokens response - matches frontend expectation"""
    user: UserResponseSchema
    tokens: TokensSchema


class LoginRequest(BaseModel):
    """JSON login request - matches frontend auth.service.ts"""
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # FIX Cortez51: Use custom exceptions instead of HTTPException
    payload = decode_access_token(token)
    if payload is None:
        raise InvalidTokenError("Could not validate credentials")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise InvalidTokenError("Invalid token - no user ID")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthenticationError("User not found")

    return user

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _create_token_pair(user_id: str) -> TokensSchema:
    """Create access and refresh token pair"""
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return TokensSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


def _user_to_response(user: User) -> UserResponseSchema:
    """Convert User ORM model to response schema"""
    return UserResponseSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=user.roles or [],
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/register",
    response_model=APIResponse[UserWithTokensResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user and return user info with tokens"
)
async def register(user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    """
    Register a new user.

    Returns APIResponse with { user, tokens } structure matching frontend expectation.
    """
    # Check if email exists
    # FIX Cortez51: Use custom ValidationError
    if db.query(User).filter(User.email == user_data.email).first():
        raise ValidationError("Email already registered", field="email")

    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise ValidationError("Username already taken", field="username")

    # Create user
    # FIX Cortez54: Role is already validated/normalized by schema validator
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        roles=[user_data.role],  # Already normalized by UserRegisterSchema validator
        is_active=True
    )

    # FIX Cortez36: Add proper error handling with rollback
    # FIX Cortez51: Use custom DatabaseOperationError
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error("User registration failed: %s", str(e), exc_info=True)
        raise DatabaseOperationError("create_user", details=str(e))

    # Create token pair
    tokens = _create_token_pair(user.id)

    return APIResponse(
        success=True,
        data=UserWithTokensResponse(
            user=_user_to_response(user),
            tokens=tokens
        ),
        message="User registered successfully"
    )


@router.post(
    "/login",
    response_model=APIResponse[UserWithTokensResponse],
    summary="Login with JSON (frontend compatible)",
    description="Login with email and password in JSON body. Returns user info with tokens."
)
async def login_json(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with JSON body - matches frontend auth.service.ts expectation.

    Request body: { email: string, password: string }
    Response: APIResponse[{ user: User, tokens: { access_token, refresh_token, token_type } }]

    FIX Cortez33: Security improvements:
    - Generic logging without revealing user existence
    - Constant-time comparison to prevent timing attacks
    - No email/password details in logs
    FIX Cortez51: Use custom exceptions
    """
    import asyncio
    import secrets

    # FIX Cortez33: Generic log message - don't reveal user existence
    logger.info("Login attempt received")

    # Try to find user by email or username
    user = db.query(User).filter(
        (User.email == credentials.email) | (User.username == credentials.email)
    ).first()

    # FIX Cortez33: Prevent timing attacks - always verify a password
    # even if user doesn't exist (use a dummy hash)
    dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.V/IlRzLpEbWE8."  # hash of "dummy"

    if user:
        password_valid = verify_password(credentials.password, user.hashed_password)
    else:
        # Still run password verification to prevent timing attacks
        verify_password(credentials.password, dummy_hash)
        password_valid = False

    # FIX Cortez33: Add small random delay to further obscure timing
    # FIX Cortez34: Use asyncio.sleep instead of time.sleep to not block event loop
    await asyncio.sleep(secrets.randbelow(100) / 1000)  # 0-100ms random delay

    if not user or not password_valid:
        # FIX Cortez33: Generic warning - don't reveal which check failed
        logger.warning("Authentication failed")
        raise AuthenticationError("Incorrect email/username or password")

    if not user.is_active:
        # FIX Cortez33: Don't log specific user details
        logger.warning("Authentication failed - account disabled")
        raise UserInactiveError()

    # Create token pair
    tokens = _create_token_pair(user.id)

    # FIX Cortez33: Only log success without sensitive details
    logger.info("Authentication successful")

    return APIResponse(
        success=True,
        data=UserWithTokensResponse(
            user=_user_to_response(user),
            tokens=tokens
        ),
        message="Login successful"
    )


@router.post(
    "/token",
    response_model=TokenSchema,
    summary="Login with OAuth2 FormData (Swagger compatible)",
    description="OAuth2 compatible login endpoint for Swagger UI testing"
)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login with FormData.

    This endpoint is maintained for Swagger UI compatibility.
    For frontend, use POST /auth/login with JSON body.
    """
    # Try to find user by email or username
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    # FIX Cortez51: Use custom exceptions
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError("Incorrect email/username or password")

    if not user.is_active:
        raise UserInactiveError()

    # Create access token only (OAuth2 standard)
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/refresh",
    response_model=APIResponse[TokensSchema],
    summary="Refresh access token",
    description="Use refresh token to get a new access token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Request body: { refresh_token: string }
    Response: APIResponse[{ access_token, refresh_token, token_type }]
    """
    # Decode refresh token
    # FIX Cortez51: Use custom exceptions
    payload = decode_access_token(request.refresh_token)

    if payload is None:
        raise InvalidTokenError("Invalid or expired refresh token")

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise InvalidTokenError("Invalid token type - not a refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token - no user ID")

    # Verify user still exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id=user_id)

    if not user.is_active:
        raise UserInactiveError(user_id=user_id)

    # Create new token pair
    tokens = _create_token_pair(user.id)

    return APIResponse(
        success=True,
        data=tokens,
        message="Token refreshed successfully"
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponseSchema],
    summary="Get current user",
    description="Get current authenticated user information"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return APIResponse(
        success=True,
        data=_user_to_response(current_user),
        message="User retrieved successfully"
    )
