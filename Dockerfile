# Multi-stage build for Section 8 AppFolio Agent
FROM node:18-alpine AS frontend-build

# Build frontend
WORKDIR /app
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --only=production; fi
RUN npm run build

# Python backend with Playwright
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm-dev \
    libxcomposite-dev \
    libxdamage-dev \
    libxrandr-dev \
    libgbm-dev \
    libxss-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./backend/
COPY worker/requirements.txt ./worker/
RUN pip install --no-cache-dir -r backend/requirements.txt -r worker/requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY backend/ ./backend/
COPY worker/ ./worker/
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Create necessary directories
RUN mkdir -p uploads screenshots job_results

# Set environment variables
ENV PYTHONPATH="/app/worker:/app/backend"
ENV PLAYWRIGHT_BROWSERS_PATH="/ms-playwright"

# Expose port
EXPOSE 8000

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]