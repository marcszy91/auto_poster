"""User model for authentication and settings."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """User model with authentication and encrypted credentials."""

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Authentication Fields
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Email Verification
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # User Credentials (Encrypted in Application Layer)
    # These will be encrypted before saving and decrypted when reading
    instagram_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instagram_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_client_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_client_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    groq_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        "Post", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"
