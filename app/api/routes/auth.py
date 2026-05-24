"""
app/api/routes/auth.py
───────────────────────
Auth endpoints:
    POST /auth/register       → create account
    POST /auth/login          → get access + refresh tokens
    POST /auth/refresh        → exchange refresh token for new access token
    GET  /auth/me             → get current user profile
    PUT  /auth/me/password    → change password
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from app.core.logging import get_logger
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    change_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_user_by_id,
    register_user,
)

router   = APIRouter(prefix="/auth", tags=["Authentication"])
logger   = get_logger(__name__)
settings = get_settings()

# ── POST /auth/register ────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """
    Create a new candidate or recruiter account.
    Returns the created user (no token yet — user must login separately).
    """
    try:
        user = register_user(db, payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return RegisterResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )

# ── POST /auth/login ───────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate with email + password.
    Returns a short-lived access token and a long-lived refresh token.
    """
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token  = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)
    
    logger.info("User logged in: id=%d role=%s", user.id, user.role)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )

# ── POST /auth/refresh ─────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access token + refresh token pair.
    Old refresh token is implicitly invalidated by issuing a new one.
    """
    try:
        user_id = decode_refresh_token(payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated.",
        )

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )

# ── GET /auth/me ───────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)

# ── PUT /auth/me/password ──────────────────────────────────────────────────────
@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
)
def update_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change the authenticated user's password."""
    try:
        change_password(db, current_user, payload.current_password, payload.new_password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"message": "Password updated successfully."}