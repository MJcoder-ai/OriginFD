# OriginFD Workers Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt ./shared-requirements.txt
COPY services/workers/requirements.txt ./service-requirements.txt
RUN pip install --no-cache-dir -r shared-requirements.txt && \
    pip install --no-cache-dir -r service-requirements.txt

# Copy the workers service code
COPY services/workers/ ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# No port exposure needed for Celery workers

# Health check using Celery inspect
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c \"import os; import redis; r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0')); r.ping()\" || exit 1"

# Start the Celery workers
CMD ["python", "main.py"]