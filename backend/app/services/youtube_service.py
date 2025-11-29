"""YouTube Shorts upload service using Google API."""

import os
from typing import Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class YouTubeServiceError(Exception):
    """Custom exception for YouTube service errors."""

    pass


class YouTubeService:
    """Service for uploading YouTube Shorts videos."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        """
        Initialize YouTube service.

        Args:
            client_id: YouTube API client ID (required)
            client_secret: YouTube API client secret (required)
            refresh_token: YouTube API refresh token (required)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = None

    def authenticate(self) -> None:
        """
        Authenticate with YouTube API.

        Raises:
            YouTubeServiceError: If authentication fails
        """
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise YouTubeServiceError("YouTube API credentials not configured")

        try:
            credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            self.youtube = build("youtube", "v3", credentials=credentials)

        except Exception as e:
            raise YouTubeServiceError(f"YouTube authentication failed: {str(e)}")

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list[str]] = None,
    ) -> Tuple[str, str]:
        """
        Upload video as YouTube Short.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: Optional list of tags

        Returns:
            Tuple[str, str]: Video ID and URL

        Raises:
            YouTubeServiceError: If upload fails
        """
        if not self.youtube:
            self.authenticate()

        if not os.path.exists(video_path):
            raise YouTubeServiceError(f"Video file not found: {video_path}")

        # Prepare request body
        body = {
            "snippet": {
                "title": title[:100],  # YouTube title limit
                "description": description,
                "tags": tags or ["3d printing", "shorts", "bambu lab"],
                "categoryId": "28",  # Science & Technology
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        try:
            # Create media upload
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype="video/mp4",
            )

            # Execute upload
            request = self.youtube.videos().insert(  # type: ignore
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = request.execute()

            video_id = response["id"]
            video_url = f"https://www.youtube.com/shorts/{video_id}"

            return video_id, video_url

        except HttpError as e:
            raise YouTubeServiceError(f"YouTube upload failed: {str(e)}")
        except Exception as e:
            raise YouTubeServiceError(f"Unexpected error during upload: {str(e)}")

    async def upload_content(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list[str]] = None,
    ) -> Tuple[str, str]:
        """
        Upload YouTube Short (async wrapper).

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: Optional list of tags

        Returns:
            Tuple[str, str]: Video ID and URL

        Raises:
            YouTubeServiceError: If upload fails
        """
        return self.upload_short(video_path, title, description, tags)
