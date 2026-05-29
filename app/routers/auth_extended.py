"""
Phase 3 – Step 1 & 2: Email Verification + Password Reset
Drop this file into app/routers/ and include the router in app/main.py:
    from app.routers.auth_extended import router as auth_ext_router
    app.include_router(auth_ext_router, prefix="/auth", tags=["auth"])
"""

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db          # adjust import path as needed
from app.models import User              # adjust import path as needed
from app.core.email import send_email    # see app/core/email.py below
from app.core.security import hash_password, verify_password  # adjust as needed

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ---------------------------------------------------------------------------
# Step 1 – Email Verification
# ---------------------------------------------------------------------------

@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    """GET /auth/verify?token=xxx  — confirms the email."""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    if user.is_verified:
        return {"message": "Email already verified."}

    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully. You may now log in."}


def send_verification_email(user: User, db: Session, background_tasks: BackgroundTasks):
    """Call this right after creating a new user during /auth/register."""
    token = secrets.token_urlsafe(32)
    user.verification_token = token
    db.commit()

    verify_url = f"http://localhost:8000/auth/verify?token={token}"
    send_email(
        to=user.email,
        subject="Verify your AI Career Accelerator account",
        html=f"""
        <p>Hi {user.full_name or user.email},</p>
        <p>Click the link below to verify your email address:</p>
        <p><a href="{verify_url}">{verify_url}</a></p>
        <p>This link is valid for 24 hours.</p>
        """,
        background_tasks=background_tasks,
    )


# ---------------------------------------------------------------------------
# Step 2 – Password Reset
# ---------------------------------------------------------------------------

@router.post("/forgot-password", status_code=202)
def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """POST /auth/forgot-password — sends reset link to email."""
    user = db.query(User).filter(User.email == body.email).first()
    # Always return 202 to avoid leaking whether the email exists
    if not user:
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=2)
    db.commit()

    reset_url = f"http://localhost:3000/reset-password?token={token}"
    send_email(
        to=user.email,
        subject="Reset your AI Career Accelerator password",
        html=f"""
        <p>Hi {user.full_name or user.email},</p>
        <p>You requested a password reset. Click the link below (expires in 2 hours):</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>If you did not request this, ignore this email.</p>
        """,
        background_tasks=background_tasks,
    )
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """POST /auth/reset-password — accepts token + new password."""
    user = (
        db.query(User)
        .filter(User.reset_token == body.token)
        .filter(User.reset_token_expires > datetime.utcnow())
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    user.hashed_password = hash_password(body.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Password reset successfully. You may now log in."}
