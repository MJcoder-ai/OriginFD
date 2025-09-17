# OriginFD API Service Dockerfile - Multi-stage build

# Builder stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies with optimization
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt ./shared-requirements.txt
COPY services/api/requirements.txt ./service-requirements.txt

# Create virtual environment and install dependencies
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r shared-requirements.txt && \
    pip install --no-cache-dir -r service-requirements.txt

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies with cleanup
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy the API service code
COPY services/api/ ./
RUN chmod +x start.sh && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check with dynamic port support
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Start the FastAPI application with production-grade gunicorn
CMD ["./start.sh"]