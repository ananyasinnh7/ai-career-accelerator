"""
app/core/dependencies.py
─────────────────────────
Reusable FastAPI dependencies for authentication and authorisation.

Usage in any route
──────────────────
    from app.core.dependencies import get_current_user, require_role

    # Any authenticated user:
    @router.get("/me")
    def me(user: User = Depends(get_current_user)):
        ...

    # Recruiter only:
    @router.post("/jobs")
    def create_job(user: User = Depends(require_role(UserRole.recruiter))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenError, InsufficientPermissionsError
from app.core.logging import get_logger
from app.db.models import User, UserRole
from app.db.session import get_db
from app.services.auth_service import decode_access_token, get_user_by_id

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer token, return the authenticated User.
    Raises HTTP 401 if the token is missing, invalid, or the user no longer exists.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_role(*roles: UserRole):
    """
    Dependency factory that restricts a route to specific roles.

    Example
    -------
        Depends(require_role(UserRole.recruiter))
        Depends(require_role(UserRole.recruiter, UserRole.admin))
    """
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{', '.join(r.value for r in roles)}. "
                    f"Your role: {user.role.value}."
                ),
            )
        return user
    return _check