"""
app/schemas/auth.py
────────────────────
Pydantic v2 schemas for all auth endpoints.
These are the public API contract — keep stable.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from app.db.models import UserRole

# ── Register ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email:     EmailStr
    password:  str = Field(..., min_length=8, description="Minimum 8 characters.")
    full_name: str = Field(..., min_length=2, max_length=255)
    role:      UserRole = UserRole.candidate

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class RegisterResponse(BaseModel):
    id:        int
    email:     EmailStr
    full_name: str
    role:      UserRole
    message:   str = "Account created successfully."
    
    model_config = {"from_attributes": True}


# ── Login ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int  # seconds


# ── Refresh ────────────────────────────────────────────────────────────────────
class RefreshRequest(BaseModel):
    refresh_token: str


# ── Current user ───────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id:          int
    email:       EmailStr
    full_name:   str
    role:        UserRole
    is_active:   bool
    is_verified: bool
    
    model_config = {"from_attributes": True}


# ── Change password ────────────────────────────────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password:     str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v