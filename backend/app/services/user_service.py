"""User service for managing user settings and credentials."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCredentialsResponse, UserCredentialsUpdate
from app.utils.security import decrypt_credential, encrypt_credential

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user settings and credentials."""

    @staticmethod
    async def get_user_credentials(db: AsyncSession, user: User) -> UserCredentialsResponse:
        """
        Get user credentials (masked for security).

        Args:
            db: Database session
            user: User object

        Returns:
            UserCredentialsResponse with masked credentials
        """
        return UserCredentialsResponse(
            instagram_username=decrypt_credential(user.instagram_username or ""),
            instagram_password_set=bool(user.instagram_password),
            youtube_client_id_set=bool(user.youtube_client_id),
            youtube_client_secret_set=bool(user.youtube_client_secret),
            youtube_refresh_token_set=bool(user.youtube_refresh_token),
            groq_api_key_set=bool(user.groq_api_key),
        )

    @staticmethod
    async def update_user_credentials(
        db: AsyncSession, user: User, credentials: UserCredentialsUpdate
    ) -> User:
        """
        Update user credentials with encryption.

        Args:
            db: Database session
            user: User object
            credentials: Credentials to update

        Returns:
            Updated user object
        """
        # Only update provided fields
        if credentials.instagram_username is not None:
            user.instagram_username = encrypt_credential(credentials.instagram_username)

        if credentials.instagram_password is not None:
            user.instagram_password = encrypt_credential(credentials.instagram_password)

        if credentials.youtube_client_id is not None:
            user.youtube_client_id = encrypt_credential(credentials.youtube_client_id)

        if credentials.youtube_client_secret is not None:
            user.youtube_client_secret = encrypt_credential(credentials.youtube_client_secret)

        if credentials.youtube_refresh_token is not None:
            user.youtube_refresh_token = encrypt_credential(credentials.youtube_refresh_token)

        if credentials.groq_api_key is not None:
            user.groq_api_key = encrypt_credential(credentials.groq_api_key)

        await db.commit()
        await db.refresh(user)

        logger.info(f"Credentials updated for user: {user.email}")
        return user

    @staticmethod
    def get_decrypted_instagram_credentials(user: User) -> Optional[tuple[str, str]]:
        """
        Get decrypted Instagram credentials for a user.

        Args:
            user: User object

        Returns:
            Tuple of (username, password) or None if not set
        """
        if not user.instagram_username or not user.instagram_password:
            return None

        username = decrypt_credential(user.instagram_username)
        password = decrypt_credential(user.instagram_password)

        if not username or not password:
            return None

        return username, password

    @staticmethod
    def get_decrypted_youtube_credentials(user: User) -> Optional[dict[str, str]]:
        """
        Get decrypted YouTube credentials for a user.

        Args:
            user: User object

        Returns:
            Dict with client_id, client_secret, refresh_token or None if not set
        """
        if (
            not user.youtube_client_id
            or not user.youtube_client_secret
            or not user.youtube_refresh_token
        ):
            return None

        client_id = decrypt_credential(user.youtube_client_id)
        client_secret = decrypt_credential(user.youtube_client_secret)
        refresh_token = decrypt_credential(user.youtube_refresh_token)

        if not client_id or not client_secret or not refresh_token:
            return None

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def get_decrypted_groq_api_key(user: User) -> Optional[str]:
        """
        Get decrypted Groq API key for a user.

        Args:
            user: User object

        Returns:
            API key or None if not set
        """
        if not user.groq_api_key:
            return None

        api_key = decrypt_credential(user.groq_api_key)
        return api_key if api_key else None
