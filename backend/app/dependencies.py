"""FastAPI dependencies for authentication and authorization."""

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.security import verify_token


async def get_current_user(
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token in cookie.

    Args:
        access_token: JWT access token from httpOnly cookie
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not access_token:
        raise credentials_exception

    # Verify token
    email = verify_token(access_token, token_type="access")
    if email is None:
        raise credentials_exception

    # Get user from database
    user = await AuthService.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current verified user (email must be verified).

    Args:
        current_user: Current authenticated user

    Returns:
        Current verified user

    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )

    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


# Optional: dependency that doesn't raise exception if user not authenticated
async def get_current_user_optional(
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.

    Args:
        access_token: JWT access token from httpOnly cookie
        db: Database session

    Returns:
        Current user object or None if not authenticated
    """
    if not access_token:
        return None

    email = verify_token(access_token, token_type="access")
    if email is None:
        return None

    user = await AuthService.get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None

    return user
