# OriginFD Workers Service Dockerfile - Multi-stage build

# Builder stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt ./shared-requirements.txt
COPY services/workers/requirements.txt ./service-requirements.txt

# Create virtual environment and install dependencies
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r shared-requirements.txt && \
    pip install --no-cache-dir -r service-requirements.txt

# Verify critical dependencies are importable
RUN python -c "import psycopg2; print('psycopg2 imported successfully')" && \
    python -c "import sqlalchemy; print('sqlalchemy imported successfully')" && \
    python -c "import celery; print('celery imported successfully')"

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy the workers service code
COPY services/workers/ ./
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for health check web server
EXPOSE 8080

# Health check using the new FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start the workers service (includes both health server and Celery worker)
ENTRYPOINT ["python", "main.py"]
