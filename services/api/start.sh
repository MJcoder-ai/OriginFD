#!/bin/bash
# Startup script for OriginFD API service with Cloud Run PORT support

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

echo "Starting OriginFD API service on port $PORT"

# Start gunicorn with proper configuration
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app