"""Posts router for handling social media post creation and retrieval."""

import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.logging_config import get_logger
from app.models.post import PlatformStatus, Post
from app.models.user import User
from app.schemas.post import PostListResponse, PostResponse
from app.services.ai_text_service import AITextService, AITextServiceError
from app.services.instagram_service import InstagramService, InstagramServiceError
from app.services.makerworld_scraper import MakerWorldScraper, MakerWorldScraperError
from app.services.template_service import TemplateService
from app.services.user_service import UserService
from app.services.video_service import VideoService
from app.services.youtube_service import YouTubeService, YouTubeServiceError

router = APIRouter()
logger = get_logger(__name__)


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """
    Save uploaded file to destination.

    Args:
        upload_file: Uploaded file
        destination: Destination path

    Returns:
        str: Saved file path
    """
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    with open(destination, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)

    return destination


async def process_platform_posts(
    post_id: int,
    user_id: int,
    main_image_path: str,
    caption: str,
    title: str,
    db: AsyncSession,
    post_instagram_feed: bool = True,
    post_instagram_reel: bool = True,
    post_instagram_story: bool = True,
    post_youtube_short: bool = True,
) -> None:
    """
    Background task to process posts to selected platforms.

    Args:
        post_id: Database post ID
        main_image_path: Path to main image
        caption: Post caption
        title: Post title
        db: Database session
        post_instagram_feed: Whether to post to Instagram feed
        post_instagram_reel: Whether to post Instagram reel
        post_instagram_story: Whether to post Instagram story
        post_youtube_short: Whether to post YouTube short
    """
    # Get post and user from database
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        return

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return

    # Get user credentials
    instagram_creds = UserService.get_decrypted_instagram_credentials(user)
    youtube_creds = UserService.get_decrypted_youtube_credentials(user)

    # Initialize services with user credentials
    video_service = VideoService(temp_dir=settings.temp_dir)

    # Initialize services with user credentials (or None if not configured)
    instagram_service = None
    if instagram_creds:
        instagram_service = InstagramService(
            username=instagram_creds[0], password=instagram_creds[1]
        )

    youtube_service = None
    if youtube_creds:
        youtube_service = YouTubeService(
            client_id=youtube_creds["client_id"],
            client_secret=youtube_creds["client_secret"],
            refresh_token=youtube_creds["refresh_token"],
        )

    # Create video only if needed (reel, story, or YouTube short)
    video_path = None
    need_video = post_instagram_reel or post_instagram_story or post_youtube_short

    if need_video:
        try:
            # Generate video (9:16 format, 15 seconds)
            video_path = video_service.create_instagram_reel(
                main_image_path, title, settings.video_duration
            )
        except Exception as e:
            logger.error(f"Error creating video: {e}", exc_info=True)

    # Post to Instagram (selectively: Feed, Reel, Story)
    any_instagram = post_instagram_feed or post_instagram_reel or post_instagram_story

    if any_instagram:
        if not instagram_service:
            post.instagram_status = PlatformStatus.FAILED
            post.instagram_error = "Instagram credentials not configured in user settings"
            await db.commit()
            logger.warning(f"User {user_id} attempted to post to Instagram without credentials")
        else:
            try:
                post.instagram_status = PlatformStatus.PROCESSING
                await db.commit()

                post_id_ig, post_url = await instagram_service.post_content(
                    image_path=main_image_path,
                    caption=caption,
                    video_path=video_path,
                    post_feed=post_instagram_feed,
                    post_reel=post_instagram_reel,
                    post_story=post_instagram_story,
                )

                post.instagram_status = PlatformStatus.SUCCESS
                post.instagram_post_id = post_id_ig
                post.instagram_posted_at = datetime.utcnow()
                await db.commit()

            except InstagramServiceError as e:
                post.instagram_status = PlatformStatus.FAILED
                post.instagram_error = str(e)
                await db.commit()
            except Exception as e:
                post.instagram_status = PlatformStatus.FAILED
                post.instagram_error = f"Unexpected error: {str(e)}"
                await db.commit()
    else:
        post.instagram_status = PlatformStatus.SKIPPED
        post.instagram_error = "Not selected for posting"
        await db.commit()

    # Post to YouTube Shorts (if enabled)
    if post_youtube_short:
        if not youtube_service:
            post.youtube_status = PlatformStatus.FAILED
            post.youtube_error = "YouTube credentials not configured in user settings"
            await db.commit()
            logger.warning(f"User {user_id} attempted to post to YouTube without credentials")
        else:
            try:
                if video_path and os.path.exists(video_path):
                    post.youtube_status = PlatformStatus.PROCESSING
                    await db.commit()

                    video_id, video_url = await youtube_service.upload_content(
                        video_path=video_path,
                        title=title,
                        description=caption,
                    )

                    post.youtube_status = PlatformStatus.SUCCESS
                    post.youtube_video_id = video_id
                    post.youtube_posted_at = datetime.utcnow()
                    await db.commit()
                else:
                    post.youtube_status = PlatformStatus.SKIPPED
                    post.youtube_error = "Video file not created"
                    await db.commit()

            except YouTubeServiceError as e:
                post.youtube_status = PlatformStatus.FAILED
                post.youtube_error = str(e)
                await db.commit()
            except Exception as e:
                post.youtube_status = PlatformStatus.FAILED
                post.youtube_error = f"Unexpected error: {str(e)}"
                await db.commit()
    else:
        post.youtube_status = PlatformStatus.SKIPPED
        post.youtube_error = "Not selected for posting"
        await db.commit()

    logger.info(
        "Posting configuration",
        extra={
            "instagram_feed": post_instagram_feed,
            "instagram_reel": post_instagram_reel,
            "instagram_story": post_instagram_story,
            "youtube_short": post_youtube_short,
            "instagram_status": post.instagram_status,
            "youtube_status": post.youtube_status,
        },
    )

    # Clean up temporary video file
    if video_path:
        video_service.cleanup_temp_files([video_path])


@router.post("/generate-text")
async def generate_text(
    keywords: str = Form(...),
    product_title: str = Form(default=""),
    designer_name: str = Form(default=""),
    print_duration: str = Form(default=""),
    materials: str = Form(default=""),
    current_user: User = Depends(get_current_verified_user),
) -> dict:
    """
    Generate AI description text based on keywords.

    Args:
        keywords: German keywords/themes for the description
        product_title: Optional product title for context
        designer_name: Optional designer name
        print_duration: Optional print duration
        materials: Optional materials (comma-separated)

    Returns:
        dict: Generated text

    Raises:
        HTTPException: If text generation fails
    """
    if not keywords or not keywords.strip():
        raise HTTPException(status_code=400, detail="Keywords are required")

    try:
        # Get user's Groq API key
        groq_api_key = UserService.get_decrypted_groq_api_key(current_user)

        # Use user's API key if available, otherwise fall back to settings
        ai_service = AITextService(api_key=groq_api_key if groq_api_key else None)
        materials_list = [m.strip() for m in materials.split(",")] if materials else None

        generated_text = await ai_service.generate_product_description(
            keywords=keywords.strip(),
            product_title=product_title if product_title else None,
            designer_name=designer_name if designer_name else None,
            print_duration=print_duration if print_duration else None,
            materials=materials_list,
        )

        return {"generated_text": generated_text}

    except AITextServiceError as e:
        raise HTTPException(status_code=500, detail=f"AI text generation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    background_tasks: BackgroundTasks,
    makerworld_id: str = Form(...),
    main_image: UploadFile = File(...),
    additional_images: List[UploadFile] = File(default=[]),
    generated_text: str = Form(default=""),
    post_instagram_feed: bool = Form(default=True),
    post_instagram_reel: bool = Form(default=True),
    post_instagram_story: bool = Form(default=True),
    post_youtube_short: bool = Form(default=True),
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Create a new social media post.

    Args:
        background_tasks: FastAPI background tasks
        makerworld_id: MakerWorld model ID
        main_image: Main image file
        additional_images: Additional image files
        db: Database session

    Returns:
        PostResponse: Created post data

    Raises:
        HTTPException: If post creation fails
    """
    # Scrape MakerWorld data
    try:
        async with MakerWorldScraper(headless=settings.headless_browser) as scraper:
            makerworld_data = await scraper.scrape_model_data(makerworld_id)
    except MakerWorldScraperError as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape MakerWorld: {str(e)}")

    # DEBUG: Print parsed MakerWorld data
    logger.info(
        "Parsed MakerWorld data",
        extra={
            "title": makerworld_data.title,
            "designer": makerworld_data.designer_name,
            "profile_title": makerworld_data.profile_title,
            "profile_designer": makerworld_data.profile_designer,
            "print_duration": makerworld_data.print_duration,
            "materials": makerworld_data.materials,
            "material_amount": makerworld_data.material_amount,
        },
    )

    # Use provided generated text (if any)
    full_text = None
    if generated_text and generated_text.strip():
        full_text = generated_text.strip()
        logger.debug(f"Using provided generated text: {full_text[:100]}...")

    # Generate caption from template
    template_service = TemplateService()
    caption = template_service.render_instagram_caption(makerworld_data, full_text=full_text)

    logger.info(f"Generated caption (length: {len(caption)} chars)")
    logger.debug(f"Caption preview: {caption[:200]}...")

    # Save main image
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    main_image_filename = f"{timestamp}_main_{main_image.filename}"
    main_image_path = os.path.join(settings.upload_dir, main_image_filename)
    await save_upload_file(main_image, main_image_path)

    # Save additional images
    additional_image_paths = []
    for idx, img in enumerate(additional_images):
        if img.filename:
            filename = f"{timestamp}_additional_{idx}_{img.filename}"
            filepath = os.path.join(settings.upload_dir, filename)
            await save_upload_file(img, filepath)
            additional_image_paths.append(filepath)

    # Create post in database
    post = Post(
        user_id=current_user.id,
        makerworld_id=makerworld_id,
        title=makerworld_data.title,
        designer_name=makerworld_data.designer_name,
        profile_title=makerworld_data.profile_title,
        profile_designer=makerworld_data.profile_designer,
        print_duration=makerworld_data.print_duration,
        materials=makerworld_data.materials,
        material_amount=makerworld_data.material_amount,
        caption=caption,
        main_image_path=main_image_path,
        additional_images=additional_image_paths,
        instagram_status=PlatformStatus.PENDING,
        youtube_status=PlatformStatus.PENDING,
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)

    # Schedule background task to post to selected platforms
    background_tasks.add_task(
        process_platform_posts,
        post.id,
        current_user.id,
        main_image_path,
        caption,
        makerworld_data.title,
        db,
        post_instagram_feed,
        post_instagram_reel,
        post_instagram_story,
        post_youtube_short,
    )

    return PostResponse.from_orm_model(post)


@router.get("/posts", response_model=PostListResponse)
async def get_posts(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> PostListResponse:
    """
    Get list of posts with pagination (filtered by current user).

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        PostListResponse: List of posts with pagination info
    """
    # Get total count for current user
    count_result = await db.execute(select(Post).where(Post.user_id == current_user.id))
    total = len(count_result.scalars().all())

    # Get paginated posts for current user
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Post)
        .where(Post.user_id == current_user.id)
        .order_by(desc(Post.created_at))
        .limit(page_size)
        .offset(offset)
    )
    posts = result.scalars().all()

    return PostListResponse(
        posts=[PostResponse.from_orm_model(post) for post in posts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Get single post by ID (only if owned by current user).

    Args:
        post_id: Post ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        PostResponse: Post data

    Raises:
        HTTPException: If post not found or not owned by user
    """
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=404, detail="Post not found or you don't have permission to access it"
        )

    return PostResponse.from_orm_model(post)
