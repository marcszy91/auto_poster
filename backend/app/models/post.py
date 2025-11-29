"""Database models for posts and their status tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlatformStatus(str, Enum):
    """Status enum for platform posting."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Post(Base):
    """
    Post model representing a social media post with multi-platform status tracking.

    Attributes:
        id: Primary key
        makerworld_id: MakerWorld model ID
        title: Print model title from MakerWorld
        designer_name: Designer name from MakerWorld
        profile_title: Print profile title from selected configuration
        profile_designer: Profile designer name (may differ from model designer)
        print_duration: Print duration in hours
        materials: List of material types (e.g., ["PLA", "PETG"])
        material_amount: Material amount in grams
        caption: Generated caption for the post
        main_image_path: Path to the main uploaded image
        additional_images: JSON array of additional image paths
        instagram_status: Status of Instagram post
        instagram_post_id: Instagram post ID if successful
        instagram_error: Error message if Instagram post failed
        youtube_status: Status of YouTube Shorts upload
        youtube_video_id: YouTube video ID if successful
        youtube_error: Error message if YouTube upload failed
        created_at: Timestamp of post creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "posts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User relationship
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="posts")  # noqa: F821

    # MakerWorld data
    makerworld_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    designer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_designer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    print_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    materials: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    material_amount: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Post content
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    main_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    additional_images: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)

    # Instagram status
    instagram_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=PlatformStatus.PENDING
    )
    instagram_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    instagram_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instagram_posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # YouTube status
    youtube_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=PlatformStatus.PENDING
    )
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    youtube_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String representation of Post."""
        return f"<Post(id={self.id}, makerworld_id={self.makerworld_id}, title={self.title})>"
