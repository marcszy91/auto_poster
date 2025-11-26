"""Pydantic schemas for post request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    """Schema for creating a new post."""

    makerworld_id: str = Field(..., description="MakerWorld model ID")


class MakerWorldData(BaseModel):
    """Schema for MakerWorld scraped data."""

    title: str
    designer_name: str
    profile_title: str
    profile_designer: str
    print_duration: str
    materials: List[str]
    material_amount: str


class PlatformStatusDetail(BaseModel):
    """Schema for individual platform status."""

    status: str
    post_id: Optional[str] = None
    error: Optional[str] = None
    posted_at: Optional[datetime] = None


class PostResponse(BaseModel):
    """Schema for post response."""

    id: int
    makerworld_id: str
    title: Optional[str] = None
    designer_name: Optional[str] = None
    profile_title: Optional[str] = None
    profile_designer: Optional[str] = None
    print_duration: Optional[str] = None
    materials: Optional[List[str]] = None
    material_amount: Optional[str] = None
    caption: Optional[str] = None
    main_image_path: str
    additional_images: List[str] = []

    # Platform statuses
    instagram: PlatformStatusDetail
    youtube: PlatformStatusDetail

    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True

    @classmethod
    def from_orm_model(cls, post) -> "PostResponse":  # type: ignore # noqa: F821
        """
        Create PostResponse from ORM Post model.

        Args:
            post: Post ORM model

        Returns:
            PostResponse instance
        """
        return cls(
            id=post.id,
            makerworld_id=post.makerworld_id,
            title=post.title,
            designer_name=post.designer_name,
            profile_title=post.profile_title,
            profile_designer=post.profile_designer,
            print_duration=post.print_duration,
            materials=post.materials,
            material_amount=post.material_amount,
            caption=post.caption,
            main_image_path=post.main_image_path,
            additional_images=post.additional_images or [],
            instagram=PlatformStatusDetail(
                status=post.instagram_status,
                post_id=post.instagram_post_id,
                error=post.instagram_error,
                posted_at=post.instagram_posted_at,
            ),
            youtube=PlatformStatusDetail(
                status=post.youtube_status,
                post_id=post.youtube_video_id,
                error=post.youtube_error,
                posted_at=post.youtube_posted_at,
            ),
            created_at=post.created_at,
            updated_at=post.updated_at,
        )


class PostListResponse(BaseModel):
    """Schema for list of posts."""

    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
