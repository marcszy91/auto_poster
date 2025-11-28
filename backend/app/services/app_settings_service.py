"""Service for managing application settings stored in database."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_settings import AppSettings

logger = logging.getLogger(__name__)


class AppSettingsService:
    """Service for managing persistent application settings."""

    @staticmethod
    async def get_setting(db: AsyncSession, key: str) -> Optional[str]:
        """
        Get a setting value by key.

        Args:
            db: Database session
            key: Setting key

        Returns:
            Setting value or None if not found
        """
        result = await db.execute(select(AppSettings).where(AppSettings.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else None

    @staticmethod
    async def set_setting(
        db: AsyncSession, key: str, value: str, description: Optional[str] = None
    ) -> AppSettings:
        """
        Set a setting value (create or update).

        Args:
            db: Database session
            key: Setting key
            value: Setting value
            description: Optional description

        Returns:
            AppSettings object
        """
        # Check if setting exists
        result = await db.execute(select(AppSettings).where(AppSettings.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            # Update existing
            setting.value = value
            if description:
                setting.description = description
        else:
            # Create new
            setting = AppSettings(key=key, value=value, description=description)
            db.add(setting)

        await db.commit()
        await db.refresh(setting)
        return setting

    @staticmethod
    async def delete_setting(db: AsyncSession, key: str) -> bool:
        """
        Delete a setting by key.

        Args:
            db: Database session
            key: Setting key

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(select(AppSettings).where(AppSettings.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            await db.delete(setting)
            await db.commit()
            return True

        return False
