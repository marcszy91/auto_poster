# Auto Poster

Automated social media management tool for 3D printing content. Upload your prints, add optional AI-generated descriptions, and post to multiple platforms with custom templates and background music.

## Features

- Multi-platform posting (Instagram Feed/Reel/Story, YouTube Shorts)
- AI-powered text generation (Groq)
- Custom video templates with background music
- Platform-selective posting with toggle switches
- Real-time status dashboard
- Mobile-friendly responsive UI
- Docker deployment ready

## Tech Stack

**Backend:** Python 3.13, FastAPI, SQLAlchemy, MoviePy, Playwright
**Frontend:** React 18, TypeScript, Vite, TailwindCSS
**Database:** PostgreSQL or SQLite
**AI:** Groq API (Llama 3.3)

## Quick Start (Docker)

### Prerequisites

- Docker and Docker Compose
- Instagram account
- YouTube OAuth credentials (optional)
- Groq API key (optional, for AI text generation)

### Setup

1. Clone and navigate to repository

2. Create `.env` file in project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/auto_poster

# API / URLs (for email links & CORS)
DEBUG=false
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# SMTP (required for verification emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=Auto Poster
SMTP_USE_TLS=false
SMTP_START_TLS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

3. Start services:

```bash
docker-compose up -d
```

4. Access application at `http://localhost`

The application runs as a single container with the frontend served by the FastAPI backend on port 80.

## YouTube Setup

YouTube requires OAuth2 credentials. See [docs/YOUTUBE_SETUP.md](docs/YOUTUBE_SETUP.md) for detailed instructions.

Quick summary:
1. Create Google Cloud project
2. Enable YouTube Data API v3
3. Create OAuth Desktop credentials
4. Generate refresh token using provided script
5. Add credentials to `.env`

## Configuration

### Environment Variables

**Core:**
- `DATABASE_URL` - Database connection string (PostgreSQL recommended)
- `DEBUG` - Debug mode (default: false)
- `BACKEND_URL` - Public backend URL (used in email links)
- `FRONTEND_URL` - Public frontend URL (used for redirects; in Docker set same as backend)

**SMTP (email verification):**
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`
- `SMTP_USE_TLS` (implicit TLS, e.g., port 465), `SMTP_START_TLS` (STARTTLS, e.g., port 587)

**Logging & Video:**
- `LOG_LEVEL`, `LOG_FORMAT`
- `VIDEO_DURATION`, `SHORTS_DURATION`

**Where to put platform/API credentials now?**
- Instagram, YouTube, Groq API key etc. are configured per user inside the app (Settings → Credentials). They are stored in the database, not in environment variables.

### Custom Templates

**Video Template:** Place image at `backend/templates/new_post_template.png`
**Background Music:** Place audio at `backend/templates/good for the ghost - Alge.mp3`
**Caption Template:** Edit `backend/templates/instagram_post.txt`

Available caption variables:
- `{title}` - Product title
- `{designer_name}` - Designer name
- `{print_duration}` - Print time
- `{material}` - Material type
- `{material_amount}` - Material amount
- `{full_text}` - AI-generated or custom text

## Usage

1. Enter MakerWorld model ID or URL
2. Upload main image
3. Select platforms (toggle switches)
4. Optional: Generate AI description from keywords
5. Create post

The system automatically:
- Scrapes model information from MakerWorld
- Generates video with template and music
- Posts to selected platforms
- Tracks status in dashboard

## Local Development

### Initial Setup

```bash
# Install dependencies
npm install
pip install pre-commit

# Setup pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Backend

```bash
cd backend
poetry install
poetry run playwright install chromium
# Edit .env in project root with your credentials
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Code Quality

Pre-commit hooks automatically run:
- Black, isort, flake8 for Python
- Prettier for TypeScript
- Conventional commit message validation

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## Production Deployment

### Docker Compose (Recommended)

1. Configure `.env` with production settings:
   - Set `DEBUG=false`
   - Use PostgreSQL for `DATABASE_URL`
   - Set `BACKEND_URL`/`FRONTEND_URL` to your public domain (identical when frontend is served by backend)
   - Configure SMTP for email verification
   - Configure `CORS_ORIGINS` for your domain

2. Deploy:
```bash
docker-compose up -d
```

### NAS/Portainer Deployment

1. Pull image from GitHub Container Registry:
   ```bash
   docker pull ghcr.io/marcszy91/auto-poster:latest
   ```

2. Create stack in Portainer using this docker-compose.yml:
   ```yaml
   version: '3.8'
   services:
     db:
       image: postgres:16-alpine
       environment:
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: postgres
         POSTGRES_DB: auto_poster
       volumes:
         - postgres_data:/var/lib/postgresql/data

     app:
       image: ghcr.io/marcszy91/auto-poster:latest
       depends_on:
         - db
       ports:
         - "80:8000"
       environment:
         - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/auto_poster
         - DEBUG=false
         - BACKEND_URL=http://your-domain-or-ip
         - FRONTEND_URL=http://your-domain-or-ip
         - SMTP_HOST=${SMTP_HOST}
         - SMTP_PORT=${SMTP_PORT}
         - SMTP_USERNAME=${SMTP_USERNAME}
         - SMTP_PASSWORD=${SMTP_PASSWORD}
         - SMTP_FROM_EMAIL=${SMTP_FROM_EMAIL}
         - SMTP_FROM_NAME=${SMTP_FROM_NAME}
         - SMTP_USE_TLS=${SMTP_USE_TLS}
         - SMTP_START_TLS=${SMTP_START_TLS}
       volumes:
         - ./uploads:/app/uploads
         - ./temp:/app/temp
         - ./templates:/app/templates

   volumes:
     postgres_data:
   ```

3. Add environment variables in Portainer UI
4. Deploy stack
5. Access at `http://your-nas-ip` or via domain (e.g., `http://autoposter.username.synology.me`)

## API Documentation

Interactive API docs available at `http://localhost:8000/docs` when backend is running.

## Project Structure

```
auto_poster/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── models/      # Database models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── main.py      # Application entry
│   ├── templates/       # Video template and caption
│   └── pyproject.toml   # Dependencies
├── frontend/            # React TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   └── services/    # API client
│   └── package.json     # Dependencies
├── docs/                # Documentation
│   ├── SETUP.md         # Production setup guide
│   ├── CONTRIBUTING.md  # Development guidelines
│   └── YOUTUBE_SETUP.md # YouTube API setup
├── Dockerfile           # Unified Docker image
├── docker-compose.yml   # Docker orchestration
└── .github/             # CI/CD workflows
```

## Troubleshooting

**Instagram Login Fails:**
- Verify credentials are correct
- Check for 2FA requirements
- Review backend logs

**YouTube Upload Fails:**
- Verify all OAuth credentials are set
- Check refresh token is valid
- Review quota limits (10,000 units/day)

**Video Generation Fails:**
- Ensure template image exists
- Verify FFmpeg is available
- Check background music file

**AI Text Generation Fails:**
- Verify Groq API key is valid
- Check API quotas
- Review backend logs

## License

MIT

## Support

Open an issue on GitHub for questions or bug reports.
