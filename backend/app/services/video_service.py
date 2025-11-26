"""Video processing service for creating social media videos from images."""

import os
from pathlib import Path
from typing import List, Tuple

from moviepy.editor import AudioFileClip, ImageClip
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Workaround for Pillow >= 10.0.0 compatibility with moviepy
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from app.logging_config import get_logger

logger = get_logger(__name__)


class VideoService:
    """Service for creating videos from images for social media platforms."""

    def __init__(self, temp_dir: str = "./temp") -> None:
        """
        Initialize video service.

        Args:
            temp_dir: Directory for temporary video files
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def create_instagram_reel(self, image_path: str, title: str, duration: int = 15) -> str:
        """
        Create Instagram Reel video from image.

        Args:
            image_path: Path to source image
            title: Title text to overlay
            duration: Video duration in seconds

        Returns:
            str: Path to generated video file
        """
        output_path = os.path.join(self.temp_dir, f"instagram_reel_{Path(image_path).stem}.mp4")

        # Instagram Reels aspect ratio: 9:16 (1080x1920)
        target_size = (1080, 1920)

        self._create_video_from_image(
            image_path=image_path,
            title=title,
            duration=duration,
            target_size=target_size,
            output_path=output_path,
        )

        return output_path

    def _create_video_from_image(
        self,
        image_path: str,
        title: str,
        duration: int,
        target_size: Tuple[int, int],
        output_path: str,
    ) -> str:
        """
        Create video from image with effects using template.

        Args:
            image_path: Path to source image
            title: Title text to overlay
            duration: Video duration in seconds
            target_size: Target video size (width, height)
            output_path: Output video path

        Returns:
            str: Path to generated video
        """
        try:
            # Load template
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "templates",
                "new_post_template.png",
            )
            template = Image.open(template_path)
            template = template.resize(target_size, Image.Resampling.LANCZOS)

            # Load image and fix orientation based on EXIF data
            img = Image.open(image_path)
            img = ImageOps.exif_transpose(img)  # Auto-rotate based on EXIF orientation

            # Combine template with image and title
            img_with_template = self._add_image_to_template(template, img, title, target_size)

            # Save image with template temporarily with high quality
            temp_image_path = os.path.join(self.temp_dir, f"temp_{Path(image_path).name}")
            img_with_template.save(temp_image_path, quality=100, optimize=False)

            # Create image clip
            image_clip = ImageClip(temp_image_path, duration=duration)

            # Apply smooth oscillating zoom effect
            # Zoom in for 5 seconds, out for 5 seconds, in again for 5 seconds
            zoom_strength = 0.10  # Reduced to 10% to keep everything visible

            def make_frame(t):
                """Generate frame at time t with oscillating zoom effect."""
                # Calculate zoom factor based on time with oscillation
                # 0-5s: zoom from 1.0 to 1.1 (zoom in)
                # 5-10s: zoom from 1.1 to 1.0 (zoom out)
                # 10-15s: zoom from 1.0 to 1.1 (zoom in)

                cycle_duration = 5.0  # 5 seconds per cycle
                current_cycle = int(t / cycle_duration)
                progress_in_cycle = (t % cycle_duration) / cycle_duration

                if current_cycle % 2 == 0:
                    # Even cycles (0, 2): zoom in
                    zoom = 1 + (zoom_strength * progress_in_cycle)
                else:
                    # Odd cycles (1): zoom out
                    zoom = 1 + zoom_strength - (zoom_strength * progress_in_cycle)

                # Get the original frame
                frame = image_clip.get_frame(t)

                # Convert to PIL Image for high-quality resizing
                pil_frame = Image.fromarray(frame)

                # Calculate new size after zoom
                new_width = int(target_size[0] * zoom)
                new_height = int(target_size[1] * zoom)

                # Resize with high quality
                zoomed = pil_frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Crop to center to maintain target size
                left = (new_width - target_size[0]) // 2
                top = (new_height - target_size[1]) // 2
                right = left + target_size[0]
                bottom = top + target_size[1]

                cropped = zoomed.crop((left, top, right, bottom))

                # Convert back to numpy array
                import numpy as np

                return np.array(cropped)

            # Create new clip with the zoom effect
            from moviepy.editor import VideoClip

            final_clip = VideoClip(make_frame, duration=duration)
            final_clip = final_clip.set_fps(30)

            # Add background music
            audio_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "templates",
                "good for the ghost - Alge.mp3",
            )

            if os.path.exists(audio_path):
                try:
                    # Load audio and trim to video duration
                    audio = AudioFileClip(audio_path)
                    audio = audio.subclip(0, min(duration, audio.duration))

                    # Reduce volume to 30% (0.3) for background music
                    audio = audio.volumex(0.3)

                    # Add audio to video
                    final_clip = final_clip.set_audio(audio)
                    logger.info(f"Background music added: {os.path.basename(audio_path)}")
                except Exception as e:
                    logger.warning(f"Could not add background music: {e}")

            # Write video file with high quality settings
            final_clip.write_videofile(
                output_path,
                fps=30,
                codec="libx264",
                audio=True,  # Changed to True to include audio
                preset="slow",
                bitrate="8000k",
                threads=4,
            )

            # Clean up temporary image
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

            return output_path

        except Exception as e:
            raise Exception(f"Failed to create video: {str(e)}")

    def _add_image_to_template(
        self, template: Image.Image, img: Image.Image, title: str, target_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Add image to template and overlay title text in footer.

        Args:
            template: Template image with header and footer
            img: User image to place in center
            title: Title text to add in footer
            target_size: Target video size (width, height)

        Returns:
            Image: Composite image with template, user image, and title
        """
        # Create a copy of template
        result = template.copy()

        # Define content area (middle section between header and footer)
        # Header is approximately first 240px, footer is approximately last 300px
        header_height = 240
        footer_height = 300
        content_height = target_size[1] - header_height - footer_height
        content_width = target_size[0]

        # Resize user image to fit in content area while maintaining aspect ratio
        img_resized = self._resize_image_for_content_area(img, (content_width, content_height))

        # Calculate position to paste user image (centered in content area)
        paste_x = (content_width - img_resized.width) // 2
        paste_y = header_height + (content_height - img_resized.height) // 2

        # Paste user image onto template
        result.paste(img_resized, (paste_x, paste_y))

        # Add title text in footer
        draw = ImageDraw.Draw(result)

        # Try to load font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
        except Exception:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50
                )
            except Exception:
                font = ImageFont.load_default()

        # Prepare title text (limit length)
        title_text = title[:50] if len(title) > 50 else title

        # Get text bounding box for centering
        try:
            bbox = draw.textbbox((0, 0), title_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except Exception:
            text_width, text_height = draw.textsize(title_text, font=font)

        # Position text centered in footer area
        x_pos = (target_size[0] - text_width) // 2
        y_pos = target_size[1] - footer_height + (footer_height - text_height) // 2

        # Draw text with outline for better visibility
        outline_range = 2
        for adj_x in range(-outline_range, outline_range + 1):
            for adj_y in range(-outline_range, outline_range + 1):
                draw.text((x_pos + adj_x, y_pos + adj_y), title_text, font=font, fill="black")

        # Draw main text
        draw.text((x_pos, y_pos), title_text, font=font, fill="white")

        return result

    def _resize_image_for_content_area(
        self, img: Image.Image, content_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Resize image to fit in content area while maintaining aspect ratio.

        Args:
            img: PIL Image to resize
            content_size: Size of content area (width, height)

        Returns:
            Image: Resized image
        """
        content_width, content_height = content_size
        img_width, img_height = img.size

        # Calculate scaling factor to fit
        width_ratio = content_width / img_width
        height_ratio = content_height / img_height
        scale_factor = min(width_ratio, height_ratio)

        # Calculate new size
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        # Resize image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img_resized

    def _resize_image_to_fit(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize image to fit target size while maintaining aspect ratio (letterbox/pillarbox).

        Args:
            img: PIL Image
            target_size: Target size (width, height)

        Returns:
            Image: Resized image with black bars if needed
        """
        target_width, target_height = target_size
        img_width, img_height = img.size

        # Calculate scaling factor to fit (not crop)
        width_ratio = target_width / img_width
        height_ratio = target_height / img_height
        scale_factor = min(width_ratio, height_ratio)  # Changed from max to min

        # Calculate new size
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        # Resize image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create new image with target size and paste resized image
        result = Image.new("RGB", target_size, (0, 0, 0))

        # Calculate position to paste (center)
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2

        result.paste(img_resized, (paste_x, paste_y))

        return result

    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        Clean up temporary video files.

        Args:
            file_paths: List of file paths to remove
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary file {file_path}: {e}")
