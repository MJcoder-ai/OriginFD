#!/bin/bash
# Startup script for OriginFD main application with Cloud Run PORT support

# Get PORT from environment, default to 8080
PORT=${PORT:-8080}

echo "Starting OriginFD main application on port $PORT"

# Start gunicorn with proper configuration
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app