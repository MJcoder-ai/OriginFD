# OriginFD Main Application Dockerfile - Multi-stage optimized build
# This Dockerfile provides significant size reduction through multi-stage builds

# =====================================
# Builder stage - Contains build tools and dependencies
# =====================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies only in builder stage
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better layer caching
COPY requirements.txt .

# Create virtual environment to isolate dependencies
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =====================================
# Runtime stage - Minimal production image
# =====================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy the application code (excluding unnecessary files via .dockerignore)
COPY . .

# Set proper ownership for non-root user and make start script executable
RUN chmod +x start.sh && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Add health check with dynamic port support for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health/ || exit 1

# Use production-grade gunicorn with dynamic PORT support for Cloud Run
CMD ["./start.sh"]
