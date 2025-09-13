# OriginFD Workers Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY services/workers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the workers service code
COPY services/workers/ ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for worker management
EXPOSE 8002

# No health check for workers service

# Start the background workers
CMD ["python", "main.py"]