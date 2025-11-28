"""FastAPI main application entry point."""

import os
import secrets
import subprocess
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.config import settings
from app.database import async_session_maker, close_db
from app.logging_config import get_logger, setup_logging
from app.models.user import User
from app.routers import auth, health, posts, users
from app.services.app_settings_service import AppSettingsService
from app.utils.security import hash_password

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def ensure_jwt_secret() -> None:
    """
    Ensure JWT secret key is set. Always load from database or generate new one.

    The JWT secret is ALWAYS stored in the database for persistence across
    container restarts. Never uses environment variables.

    Behavior:
    1. Try to load from database
    2. If not found: Generate new and save to database
    3. If database error: Use temporary key with warning
    """
    logger.info("Loading JWT secret key from database...")

    # Always load from database
    async with async_session_maker() as db:
        try:
            jwt_secret = await AppSettingsService.get_setting(db, "jwt_secret_key")

            if jwt_secret:
                logger.info("✓ JWT secret key loaded from database")
                settings.jwt_secret_key = jwt_secret
                return

            # Generate new secret and save to database
            logger.info("JWT secret not found in database, generating new one...")
            new_secret = secrets.token_hex(32)

            await AppSettingsService.set_setting(
                db,
                key="jwt_secret_key",
                value=new_secret,
                description="JWT secret key for token signing (auto-generated)",
            )

            settings.jwt_secret_key = new_secret
            logger.info("✓ Generated and saved new JWT secret key to database")
            logger.info("   This key will persist across container restarts")

        except Exception as e:
            logger.error(f"Failed to load/save JWT secret from database: {str(e)}")
            logger.error("=" * 80)
            logger.error("  DATABASE ERROR - CANNOT LOAD JWT SECRET")
            logger.error("=" * 80)
            logger.error("Using a TEMPORARY JWT secret key for this session.")
            logger.error("")
            logger.error("  WARNING: This key will change on every restart!")
            logger.error("   → All users will be logged out after container restart")
            logger.error("")
            logger.error(" FIX: Ensure database is accessible and migrations have run")
            logger.error("=" * 80)

            # Use temporary key for this session only (as last resort)
            settings.jwt_secret_key = secrets.token_hex(32)


async def run_migrations() -> None:
    """Run Alembic migrations on startup."""
    try:
        logger.info("Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Migrations completed successfully")
        logger.debug(f"Migration output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error("Alembic not found. Migrations cannot run.")
        raise


async def initialize_admin_user() -> None:
    """Initialize admin user from environment variables if configured."""
    if not settings.admin_email or not settings.admin_password:
        logger.info("Admin user not configured in environment variables, skipping initialization")
        return

    async with async_session_maker() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(select(User).where(User.email == settings.admin_email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"Admin user already exists: {settings.admin_email}")
                return

            # Create admin user
            admin_user = User(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                is_active=True,
                is_verified=True,  # Admin is pre-verified
                is_admin=True,
            )

            session.add(admin_user)
            await session.commit()
            logger.info(f"Admin user created successfully: {settings.admin_email}")

        except Exception as e:
            logger.error(f"Failed to initialize admin user: {str(e)}")
            await session.rollback()
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting up application...")

    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.temp_dir, exist_ok=True)
    logger.debug(f"Created directories: {settings.upload_dir}, {settings.temp_dir}")

    # Run database migrations FIRST (needed for AppSettings table)
    await run_migrations()

    # Ensure JWT secret is configured (load from DB or generate)
    await ensure_jwt_secret()

    # Initialize admin user
    await initialize_admin_user()

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Auto Poster API",
    description="Backend service for automated social media posting",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(posts.router, prefix="/api", tags=["Posts"])

# Serve frontend static files (must be last)
# Check if static directory exists (production build)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:

    @app.get("/")
    async def root() -> dict[str, str]:
        """
        Root endpoint (development mode - no static files).

        Returns:
            dict: Welcome message
        """
        return {
            "message": "Auto Poster API",
            "version": "0.1.0",
            "docs": "/docs",
        }
