#!/bin/bash
# Startup script for OriginFD Orchestrator service with Cloud Run PORT support

# Get PORT from environment, default to 8001
PORT=${PORT:-8001}

echo "Starting OriginFD Orchestrator service on port $PORT"

# Start gunicorn with proper configuration
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app