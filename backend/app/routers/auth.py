"""Authentication endpoints for registration, login, and email verification."""

import logging
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    EmailVerification,
    Token,
    TokenRefresh,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.

    - **email**: User email address (must be unique)
    - **password**: User password (min 8 chars, must contain uppercase, lowercase, digit)

    Returns the created user object. A verification email will be sent.
    """
    user = await AuthService.register_user(db, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login with email and password.

    - **email**: User email address
    - **password**: User password

    Returns JWT tokens in httpOnly cookies and response body.
    """
    # Authenticate user
    user = await AuthService.authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token, refresh_token = await AuthService.create_tokens(user)

    # Set httpOnly cookies for tokens (secure for production)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=1800,  # 30 minutes
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=604800,  # 7 days
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(response: Response) -> dict:
    """
    Logout the current user.

    Clears authentication cookies.
    """
    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    token_data: Optional[TokenRefresh] = None,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Refresh access token using refresh token.

    Can provide refresh token either in cookie or request body.
    Returns new access token.
    """
    # Get refresh token from cookie or body
    refresh_token = refresh_token_cookie
    if token_data:
        refresh_token = token_data.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    # Create new access token
    access_token = await AuthService.refresh_access_token(db, refresh_token)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=1800,  # 30 minutes
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify user email with verification token.

    - **token**: Email verification token (sent via email)

    Returns success message if verification successful.
    """
    success = await AuthService.verify_email(db, token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Resend email verification.

    - **email**: User email address

    Returns success message if email sent.
    """
    success = await AuthService.resend_verification_email(db, email)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or already verified",
        )

    return {"message": "Verification email sent"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid access token in cookie.
    """
    return UserResponse.model_validate(current_user)


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for authentication service."""
    return {"status": "healthy", "service": "auth"}
