# Production Release Setup

This document outlines the complete setup for production deployment with CI/CD.

## Prerequisites

1. GitHub repository initialized
2. Docker and Docker Compose installed
3. Instagram account
4. (Optional) YouTube OAuth credentials
5. (Optional) Groq API key

## Initial Configuration

### 1. Update Repository URL

Edit `package.json` and update the repository URL:

```json
"repository": {
  "type": "git",
  "url": "https://github.com/marcszy91/auto_poster.git"
}
```

### 2. Initialize Git Repository

```bash
git init
git add .
git commit -m "feat: initial project setup"
git branch -M main
git remote add origin https://github.com/marcszy91/auto_poster.git
git push -u origin main
```

### 3. Create Development Branch

```bash
git checkout -b dev
git push -u origin dev
```

## Development Setup

### Install Pre-commit Hooks

```bash
npm install
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

This installs:
- Black (Python formatter)
- isort (Python import sorter)
- Flake8 (Python linter)
- Prettier (TypeScript formatter)
- Conventional commit message validator

### Test Pre-commit Hooks

```bash
# Make a test change
echo "# Test" >> test.md
git add test.md
git commit -m "test: verify pre-commit hooks"
```

If hooks are working, you should see output from the various checkers.

## CI/CD Pipeline

### GitHub Actions Workflow

Located at `.github/workflows/release.yml`, this workflow:

1. **Semantic Release Job:**
   - Analyzes commit messages
   - Determines version bump
   - Generates CHANGELOG.md
   - Creates GitHub release
   - Triggers on push to `main` or `dev` branches

2. **Docker Build Job:**
   - Builds backend and frontend Docker images
   - Pushes to GitHub Container Registry (GHCR)
   - Tags with version and `latest`

### Enable GitHub Actions

1. Go to repository Settings > Actions > General
2. Enable "Read and write permissions" for workflows
3. Enable "Allow GitHub Actions to create and approve pull requests"

### First Release

```bash
# From dev branch
git add .
git commit -m "feat: initial release setup"
git push origin dev

# Merge to main for production release
git checkout main
git merge dev
git push origin main
```

This will trigger the workflow and:
- Create version 1.0.0 (based on feat commits)
- Generate CHANGELOG.md
- Build and push Docker images to GHCR

## Docker Images

After the first successful release, the image will be available at:

```
ghcr.io/marcszy91/auto-poster:latest
```

This is a unified image containing both frontend and backend.

### Pull Image

```bash
docker pull ghcr.io/marcszy91/auto-poster:latest
```

## NAS/Portainer Deployment

### 1. Create Stack

In Portainer:
1. Go to Stacks
2. Click "Add stack"
3. Name it "auto-poster"

### 2. Docker Compose Configuration

Update the `docker-compose.yml` to use GHCR image:

```yaml
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
      # ... other env vars
    volumes:
      - ./uploads:/app/uploads
      - ./temp:/app/temp
      - ./templates:/app/templates

volumes:
  postgres_data:
```

### 3. Environment Variables

Add these in Portainer's environment variables section:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/auto_poster
DEBUG=false
BACKEND_URL=https://hostname:port
FRONTEND_URL=https://hostname:port
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=Auto Poster
SMTP_USE_TLS=false
SMTP_START_TLS=true
LOG_LEVEL=INFO
LOG_FORMAT=text
```

### 4. Deploy Stack

Click "Deploy the stack" and wait for containers to start.

### 5. Access Application

Navigate to `https://hostname:port` in your browser.

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

### Types

- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `perf:` - Performance improvement (patch version bump)
- `refactor:` - Code refactoring (patch version bump)
- `docs:` - Documentation only
- `style:` - Code style changes
- `test:` - Adding tests
- `build:` - Build system changes
- `ci:` - CI configuration changes
- `chore:` - Other changes

### Examples

```bash
git commit -m "feat(instagram): add carousel post support"
git commit -m "fix(video): resolve audio sync issue"
git commit -m "docs: update YouTube setup guide"
```

### Breaking Changes

For major version bump:

```bash
git commit -m "feat(api): redesign post creation endpoint

BREAKING CHANGE: POST /api/posts now requires platform parameter"
```

## Release Workflow

### Development Release (Prerelease)

```bash
git checkout dev
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin dev
```

This creates a prerelease version: `1.1.0-dev.1`

### Production Release

```bash
git checkout main
git merge dev
git push origin main
```

This creates a production version: `1.1.0`

## Verification

### Check Release

1. Go to GitHub repository
2. Click "Releases"
3. Verify new release is created
4. Check CHANGELOG.md is updated

### Check Docker Images

```bash
# List images
docker images | grep auto-poster

# Or check GHCR
# Go to: https://github.com/marcszy91?tab=packages
```

### Test Deployment

```bash
docker-compose pull
docker-compose up -d
docker-compose logs -f
```

## Troubleshooting

### Semantic Release Fails

- Verify commit messages follow conventional format
- Check GitHub token has correct permissions
- Review workflow logs in Actions tab

### Docker Build Fails

- Check Dockerfile syntax
- Verify all dependencies are specified
- Review build logs in Actions tab

### Pre-commit Hooks Fail

- Read error messages
- Fix issues (or let auto-fix run)
- Stage changes and commit again

### Images Not Updating

- Check if release was actually created
- Verify workflow completed successfully
- Try pulling with specific version tag instead of `latest`

## Maintenance

### Update Dependencies

Backend:
```bash
cd backend
poetry update
```

Frontend:
```bash
cd frontend
npm update
```

### Update Pre-commit Hooks

```bash
pre-commit autoupdate
```

### Re-run Failed Workflow

1. Go to Actions tab
2. Select failed workflow
3. Click "Re-run jobs"

## Security Notes

- Never commit `.env` files
- Use strong passwords for production
- Keep API keys secure
- Regularly update dependencies
- Monitor GitHub security alerts
- Use private repository for sensitive projects

## Support

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
See [README.md](README.md) for general documentation.
