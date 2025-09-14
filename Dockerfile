# Python backend with Playwright
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./backend/
COPY worker/requirements.txt ./worker/
RUN pip install --no-cache-dir -r backend/requirements.txt -r worker/requirements.txt

# Install Playwright browsers with system dependencies
RUN python -m playwright install-deps chromium && \
    python -m playwright install chromium && \
    python -c "import playwright; print('Playwright version:', playwright.__version__)" && \
    # Create and set permissions for browser directories
    mkdir -p /ms-playwright && \
    chmod -R 755 /ms-playwright /root/.cache/ms-playwright || true && \
    # Verify browser was installed
    find /root/.cache/ms-playwright -name "*chromium*" -type d | head -3 || true && \
    find /ms-playwright -name "*chromium*" -type d | head -3 || true

# Copy application code
COPY backend/ ./backend/
COPY worker/ ./worker/
# Copy frontend static files (if they exist)
COPY frontend/ ./frontend/

# Create necessary directories
RUN mkdir -p uploads screenshots job_results

# Set environment variables
ENV PYTHONPATH="/app/worker:/app/backend"
ENV PLAYWRIGHT_BROWSERS_PATH="/ms-playwright"
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD="false"

# Expose port
EXPOSE 8000

# curl is already installed above

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]