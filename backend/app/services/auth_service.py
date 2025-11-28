"""Authentication service for user registration, login, and verification."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserRegister
from app.services.email_service import EmailService
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    generate_verification_token,
    hash_password,
    verify_password,
    verify_token,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling user authentication operations."""

    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> Optional[User]:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user object or None if email already exists
        """
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            return None

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Generate verification token
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)

        # Create new user
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,  # Require email verification
            verification_token=verification_token,
            verification_token_expires=verification_expires,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Send verification email
        await EmailService.send_verification_email(user_data.email, verification_token)

        logger.info(f"New user registered: {user_data.email}")
        return new_user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {email}")
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        logger.info(f"User authenticated successfully: {email}")
        return user

    @staticmethod
    async def create_tokens(user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for a user.

        Args:
            user: User object

        Returns:
            Tuple of (access_token, refresh_token)
        """
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        return access_token, refresh_token

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Optional[str]:
        """
        Create a new access token from a refresh token.

        Args:
            db: Database session
            refresh_token: JWT refresh token

        Returns:
            New access token or None if refresh token is invalid
        """
        # Verify refresh token
        email = verify_token(refresh_token, token_type="refresh")
        if not email:
            return None

        # Get user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        # Create new access token
        access_token = create_access_token(data={"sub": user.email})
        return access_token

    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> bool:
        """
        Verify user email with verification token.

        Args:
            db: Database session
            token: Email verification token

        Returns:
            True if verification successful, False otherwise
        """
        # Find user with this verification token
        result = await db.execute(
            select(User).where(User.verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("Email verification attempted with invalid token")
            return False

        # Check if token is expired
        if (
            user.verification_token_expires
            and user.verification_token_expires < datetime.utcnow()
        ):
            logger.warning(f"Email verification attempted with expired token for: {user.email}")
            return False

        # Verify user
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        await db.commit()

        logger.info(f"Email verified successfully for user: {user.email}")
        return True

    @staticmethod
    async def resend_verification_email(db: AsyncSession, email: str) -> bool:
        """
        Resend verification email to user.

        Args:
            db: Database session
            email: User email

        Returns:
            True if email sent successfully, False otherwise
        """
        # Get user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Verification email resend requested for non-existent user: {email}")
            return False

        if user.is_verified:
            logger.info(f"Verification email resend requested for already verified user: {email}")
            return False

        # Generate new verification token
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)

        user.verification_token = verification_token
        user.verification_token_expires = verification_expires
        await db.commit()

        # Send verification email
        await EmailService.send_verification_email(email, verification_token)

        logger.info(f"Verification email resent to: {email}")
        return True

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            db: Database session
            email: User email

        Returns:
            User object or None if not found
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def change_password(
        db: AsyncSession, user: User, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            db: Database session
            user: User object
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully, False otherwise
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            logger.warning(f"Password change failed: incorrect current password for {user.email}")
            return False

        # Hash and set new password
        user.hashed_password = hash_password(new_password)
        await db.commit()

        logger.info(f"Password changed successfully for user: {user.email}")
        return True
