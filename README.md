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

# Instagram (required)
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# YouTube (optional)
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REFRESH_TOKEN=your_refresh_token

# Groq AI (optional)
GROQ_API_KEY=your_groq_api_key
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

**Required:**
- `INSTAGRAM_USERNAME` - Instagram account username
- `INSTAGRAM_PASSWORD` - Instagram account password

**Optional:**
- `YOUTUBE_CLIENT_ID` - YouTube OAuth client ID
- `YOUTUBE_CLIENT_SECRET` - YouTube OAuth client secret
- `YOUTUBE_REFRESH_TOKEN` - YouTube OAuth refresh token
- `GROQ_API_KEY` - Groq API key for AI text generation
- `DATABASE_URL` - Database connection string (default: PostgreSQL)
- `VIDEO_DURATION` - Video length in seconds (default: 15)
- `DEBUG` - Debug mode (default: false)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `LOG_FORMAT` - Log format: text or json (default: text, use json for Datadog/CloudWatch)

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
   - Set strong passwords
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
         - INSTAGRAM_USERNAME=${INSTAGRAM_USERNAME}
         - INSTAGRAM_PASSWORD=${INSTAGRAM_PASSWORD}
         - YOUTUBE_CLIENT_ID=${YOUTUBE_CLIENT_ID}
         - YOUTUBE_CLIENT_SECRET=${YOUTUBE_CLIENT_SECRET}
         - YOUTUBE_REFRESH_TOKEN=${YOUTUBE_REFRESH_TOKEN}
         - GROQ_API_KEY=${GROQ_API_KEY}
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
