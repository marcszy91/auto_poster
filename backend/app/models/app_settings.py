"""Application settings model for persistent configuration."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSettings(Base):
    """
    Application settings stored in database.

    This table stores system-wide configuration that needs to persist
    across container restarts, such as the JWT secret key.
    """

    __tablename__ = "app_settings"

    # Use setting key as primary key (e.g., "jwt_secret_key")
    key: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Setting value (encrypted sensitive values)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional description of what this setting does
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        """String representation of AppSettings."""
        return f"<AppSettings(key={self.key})>"
