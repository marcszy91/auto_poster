"""Pydantic schemas for user authentication and management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# ============================================================================
# Authentication Schemas
# ============================================================================


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenRefresh(BaseModel):
    """Schema for refreshing access token."""

    refresh_token: str = Field(..., description="JWT refresh token")


class EmailVerification(BaseModel):
    """Schema for email verification."""

    token: str = Field(..., description="Email verification token")


# ============================================================================
# User Response Schemas
# ============================================================================


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""

    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    is_admin: bool = Field(..., description="Whether user is admin")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = {"from_attributes": True}


# ============================================================================
# User Settings Schemas
# ============================================================================


class UserCredentialsUpdate(BaseModel):
    """Schema for updating user credentials (Instagram, YouTube, Groq)."""

    instagram_username: Optional[str] = Field(None, description="Instagram username")
    instagram_password: Optional[str] = Field(None, description="Instagram password")
    youtube_client_id: Optional[str] = Field(None, description="YouTube OAuth client ID")
    youtube_client_secret: Optional[str] = Field(None, description="YouTube OAuth client secret")
    youtube_refresh_token: Optional[str] = Field(None, description="YouTube refresh token")
    groq_api_key: Optional[str] = Field(None, description="Groq API key")


class UserCredentialsResponse(BaseModel):
    """Schema for reading user credentials (masked for security)."""

    instagram_username: Optional[str] = Field(None, description="Instagram username")
    instagram_password_set: bool = Field(..., description="Whether Instagram password is set")
    youtube_client_id_set: bool = Field(..., description="Whether YouTube client ID is set")
    youtube_client_secret_set: bool = Field(..., description="Whether YouTube client secret is set")
    youtube_refresh_token_set: bool = Field(..., description="Whether YouTube refresh token is set")
    groq_api_key_set: bool = Field(..., description="Whether Groq API key is set")


class UserPasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
