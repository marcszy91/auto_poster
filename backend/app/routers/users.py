"""User management endpoints for settings and credentials."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.user import (
    UserCredentialsResponse,
    UserCredentialsUpdate,
    UserPasswordChange,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_verified_user),
) -> UserResponse:
    """
    Get current user profile.

    Requires authenticated and verified user.
    """
    return UserResponse.model_validate(current_user)


@router.get("/me/credentials", response_model=UserCredentialsResponse)
async def get_my_credentials(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> UserCredentialsResponse:
    """
    Get current user credentials (masked for security).

    Returns which credentials are set without exposing the actual values.
    Shows Instagram username but masks passwords and API keys.
    """
    return await UserService.get_user_credentials(db, current_user)


@router.put("/me/credentials", response_model=UserCredentialsResponse)
async def update_my_credentials(
    credentials: UserCredentialsUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> UserCredentialsResponse:
    """
    Update current user credentials.

    - **instagram_username**: Instagram username (optional)
    - **instagram_password**: Instagram password (optional, encrypted)
    - **youtube_client_id**: YouTube OAuth client ID (optional, encrypted)
    - **youtube_client_secret**: YouTube OAuth client secret (optional, encrypted)
    - **youtube_refresh_token**: YouTube refresh token (optional, encrypted)
    - **groq_api_key**: Groq API key (optional, encrypted)

    All fields are optional. Only provided fields will be updated.
    Credentials are encrypted before storage.
    """
    await UserService.update_user_credentials(db, current_user, credentials)
    return await UserService.get_user_credentials(db, current_user)


@router.post("/me/change-password")
async def change_my_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Change current user password.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, must contain uppercase, lowercase, digit)

    Returns success message if password changed.
    """
    success = await AuthService.change_password(
        db,
        current_user,
        password_data.current_password,
        password_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    return {"message": "Password changed successfully"}
