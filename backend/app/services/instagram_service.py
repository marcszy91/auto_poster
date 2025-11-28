"""Instagram posting service using instagrapi."""

import os
from typing import Optional, Tuple

from instagrapi import Client
from instagrapi.exceptions import LoginRequired

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class InstagramServiceError(Exception):
    """Custom exception for Instagram service errors."""

    pass


class InstagramService:
    """Service for posting content to Instagram."""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """
        Initialize Instagram service.

        Args:
            username: Instagram username (required)
            password: Instagram password (required)
        """
        self.username = username
        self.password = password
        self.client: Optional[Client] = None

    def login(self) -> None:
        """
        Login to Instagram.

        Raises:
            InstagramServiceError: If login fails
        """
        if not self.username or not self.password:
            raise InstagramServiceError("Instagram credentials not configured")

        try:
            self.client = Client()
            self.client.login(self.username, self.password)
        except LoginRequired:
            raise InstagramServiceError("Instagram login failed - check credentials")
        except Exception as e:
            raise InstagramServiceError(f"Instagram login error: {str(e)}")

    def post_photo(self, image_path: str, caption: str) -> Tuple[str, str]:
        """
        Post photo to Instagram.

        Args:
            image_path: Path to image file
            caption: Post caption

        Returns:
            Tuple[str, str]: Post ID and URL

        Raises:
            InstagramServiceError: If posting fails
        """
        if not self.client:
            self.login()

        if not os.path.exists(image_path):
            raise InstagramServiceError(f"Image file not found: {image_path}")

        try:
            media = self.client.photo_upload(path=image_path, caption=caption)  # type: ignore
            post_id = str(media.pk)
            post_url = f"https://www.instagram.com/p/{media.code}/"
            return post_id, post_url

        except Exception as e:
            raise InstagramServiceError(f"Failed to post photo: {str(e)}")

    def post_reel(
        self, video_path: str, caption: str, thumbnail_path: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Post Reel to Instagram.

        Args:
            video_path: Path to video file
            caption: Post caption
            thumbnail_path: Optional path to thumbnail image

        Returns:
            Tuple[str, str]: Post ID and URL

        Raises:
            InstagramServiceError: If posting fails
        """
        if not self.client:
            self.login()

        if not os.path.exists(video_path):
            raise InstagramServiceError(f"Video file not found: {video_path}")

        try:
            # Use video_upload instead of clip_upload for better compatibility with custom audio
            media = self.client.video_upload(  # type: ignore
                path=video_path,
                caption=caption,
                thumbnail=thumbnail_path if thumbnail_path else None,
            )
            post_id = str(media.pk)
            # Video posts still appear in feed, but with custom audio they work better
            post_url = f"https://www.instagram.com/p/{media.code}/"
            return post_id, post_url

        except Exception as e:
            raise InstagramServiceError(f"Failed to post reel: {str(e)}")

    def post_story(self, video_path: str) -> Tuple[str, str]:
        """
        Post Story to Instagram.

        Args:
            video_path: Path to video file

        Returns:
            Tuple[str, str]: Story ID and URL

        Raises:
            InstagramServiceError: If posting fails
        """
        if not self.client:
            self.login()

        if not os.path.exists(video_path):
            raise InstagramServiceError(f"Video file not found: {video_path}")

        try:
            media = self.client.video_upload_to_story(path=video_path)  # type: ignore
            story_id = str(media.pk)
            story_url = f"https://www.instagram.com/stories/{self.username}/"
            return story_id, story_url

        except Exception as e:
            raise InstagramServiceError(f"Failed to post story: {str(e)}")

    async def post_content(
        self,
        image_path: str,
        caption: str,
        video_path: Optional[str] = None,
        post_feed: bool = True,
        post_reel: bool = True,
        post_story: bool = True,
    ) -> Tuple[str, str]:
        """
        Post content to Instagram (selectively: photo feed, reel, and/or story).

        Args:
            image_path: Path to image file
            caption: Post caption
            video_path: Optional path to video file for Reel and Story
            post_feed: Whether to post to feed
            post_reel: Whether to post reel
            post_story: Whether to post story

        Returns:
            Tuple[str, str]: Primary post ID and URL (from first successful post)

        Raises:
            InstagramServiceError: If all enabled posts fail
        """
        primary_id = None
        primary_url = None

        # 1. Post photo to feed (if enabled)
        if post_feed:
            try:
                photo_id, photo_url = self.post_photo(image_path, caption)
                logger.info(f"Instagram Feed posted: {photo_url}")
                if not primary_id:
                    primary_id, primary_url = photo_id, photo_url
            except Exception as e:
                logger.warning(f"Failed to post feed: {e}")

        # 2. Post reel (if enabled and video exists)
        if post_reel and video_path and os.path.exists(video_path):
            try:
                reel_id, reel_url = self.post_reel(
                    video_path=video_path,
                    caption=caption,
                    thumbnail_path=image_path,
                )
                logger.info(f"Instagram Reel posted: {reel_url}")
                if not primary_id:
                    primary_id, primary_url = reel_id, reel_url
            except Exception as e:
                logger.warning(f"Failed to post reel: {e}")

        # 3. Post story (if enabled and video exists)
        if post_story and video_path and os.path.exists(video_path):
            try:
                story_id, story_url = self.post_story(video_path=video_path)
                logger.info(f"Instagram Story posted: {story_url}")
                if not primary_id:
                    primary_id, primary_url = story_id, story_url
            except Exception as e:
                logger.warning(f"Failed to post story: {e}")

        if not primary_id:
            raise InstagramServiceError("All Instagram posts failed")

        return primary_id, primary_url

    def logout(self) -> None:
        """Logout from Instagram."""
        if self.client:
            try:
                self.client.logout()
            except Exception:
                pass
