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

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# No additional runtime packages needed for workers

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

# No port exposure needed for Celery workers

# Health check using Redis connection
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os; import redis; r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0')); r.ping()" || exit 1

# Start the Celery workers
ENTRYPOINT ["python", "main.py"]