# Multi-stage build for Auto Poster (Frontend + Backend)

# Stage 1: Build Frontend
FROM node:20-alpine as frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Build Backend with Frontend
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.2.1

# Set working directory
WORKDIR /app

# Copy backend dependency files
COPY backend/pyproject.toml ./

# Install backend dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main --with postgres

# Install Playwright and browsers
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy backend application code
COPY backend/ ./

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /frontend/dist ./static

# Create directories for uploads and temp files
RUN mkdir -p /app/uploads /app/temp /app/templates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
