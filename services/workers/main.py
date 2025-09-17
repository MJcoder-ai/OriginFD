"""
OriginFD Background Workers Service
Handles asynchronous tasks with idempotency, retry logic, and production-grade resilience.
"""

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis
import uvicorn
from celery import Celery
from celery.exceptions import Ignore, Retry
from celery.utils.log import get_task_logger
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_task_logger(__name__)

# Get configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))

# Initialize Redis client for idempotency tracking
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Initialize database connection for workers
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

# Initialize Celery app with production-grade configuration
app = Celery(
    "originfd_workers", broker=REDIS_URL, backend=REDIS_URL, include=["workers.tasks"]
)

# Configure Celery with production settings
app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Task routing and execution
    task_routes={
        "workers.tasks.*": {"queue": "default"},
        "workers.tasks.high_priority_*": {"queue": "high_priority"},
        "workers.tasks.low_priority_*": {"queue": "low_priority"},
    },
    # Result backend configuration
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry configuration
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    # Error handling
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
)

# =====================================
# Idempotency and Error Handling Utilities
# =====================================


def generate_idempotency_key(task_name: str, *args, **kwargs) -> str:
    """Generate idempotency key for task deduplication."""
    content = f"{task_name}:{json.dumps(args, sort_keys=True)}:{json.dumps(kwargs, sort_keys=True)}"
    return f"task_idempotent:{hashlib.sha256(content.encode()).hexdigest()}"


def is_task_completed(idempotency_key: str) -> Optional[Dict[str, Any]]:
    """Check if task was already completed successfully."""
    try:
        result = redis_client.get(idempotency_key)
        if result:
            return json.loads(result)
    except Exception as e:
        logger.warning(f"Error checking task completion: {e}")
    return None


def mark_task_completed(idempotency_key: str, result: Dict[str, Any], ttl: int = 3600):
    """Mark task as completed with result caching."""
    try:
        redis_client.setex(idempotency_key, ttl, json.dumps(result, default=str))
    except Exception as e:
        logger.warning(f"Error marking task completion: {e}")


def get_database_session():
    """Get database session for worker tasks."""
    if SessionLocal is None:
        raise RuntimeError("Database not configured for workers")
    return SessionLocal()


class TransientError(Exception):
    """Exception for transient errors that should be retried."""

    pass


class PermanentError(Exception):
    """Exception for permanent errors that should not be retried."""

    pass


# =====================================
# Enhanced Task Definitions
# =====================================


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def health_check(self):
    """Production-grade health check with dependency verification."""
    idempotency_key = generate_idempotency_key("health_check")

    # Check if already completed recently (cache for 5 minutes)
    existing_result = is_task_completed(idempotency_key)
    if existing_result:
        return existing_result

    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "worker_id": self.request.hostname,
            "checks": {},
        }

        # Check Redis connectivity
        try:
            redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check Database connectivity
        if SessionLocal:
            try:
                db = get_database_session()
                db.execute("SELECT 1")
                db.close()
                health_status["checks"]["database"] = "healthy"
            except Exception as e:
                health_status["checks"]["database"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"

        # Cache result for 5 minutes
        mark_task_completed(idempotency_key, health_status, ttl=300)
        return health_status

    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str, project_id: str):
    """Process document with idempotency and comprehensive error handling."""
    idempotency_key = generate_idempotency_key(
        "process_document", document_id, project_id
    )

    # Check if task already completed
    existing_result = is_task_completed(idempotency_key)
    if existing_result:
        logger.info(
            f"Document {document_id} already processed, returning cached result"
        )
        return existing_result

    try:
        logger.info(f"Processing document {document_id} for project {project_id}")

        # Verify inputs
        if not document_id or not project_id:
            raise PermanentError(
                "Missing required parameters: document_id or project_id"
            )

        # Check if document exists and is accessible
        db = get_database_session()
        try:
            # This would be actual document lookup logic
            # from models.document import Document
            # document = db.query(Document).filter(Document.id == document_id).first()
            # if not document:
            #     raise PermanentError(f"Document {document_id} not found")

            # Simulate document processing with potential failures
            processing_start = time.time()

            # Simulate network/external service calls that might fail transiently
            if time.time() % 10 < 1:  # Simulate 10% transient failure rate
                raise TransientError("Simulated external service timeout")

            time.sleep(2)  # Simulate processing time

            processing_duration = time.time() - processing_start

            result = {
                "document_id": document_id,
                "project_id": project_id,
                "status": "completed",
                "processing_duration_seconds": round(processing_duration, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "worker_id": self.request.hostname,
            }

            # Mark as completed before returning
            mark_task_completed(idempotency_key, result)

            logger.info(
                f"Document {document_id} processed successfully in {processing_duration:.2f}s"
            )
            return result

        finally:
            db.close()

    except PermanentError as exc:
        logger.error(f"Permanent error processing document {document_id}: {exc}")
        # Don't retry permanent errors
        raise Ignore()

    except TransientError as exc:
        logger.warning(f"Transient error processing document {document_id}: {exc}")
        # Retry with exponential backoff
        countdown = 2**self.request.retries * 60  # 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=countdown)

    except OperationalError as exc:
        logger.warning(f"Database error processing document {document_id}: {exc}")
        # Database issues are usually transient
        countdown = 2**self.request.retries * 30  # 30s, 60s, 120s
        raise self.retry(exc=exc, countdown=countdown)

    except Exception as exc:
        logger.error(f"Unexpected error processing document {document_id}: {exc}")
        # Treat unknown errors as transient with limited retries
        if self.request.retries >= 2:
            logger.error(f"Max retries exceeded for document {document_id}, giving up")
            raise Ignore()
        raise self.retry(exc=exc, countdown=120)


# Project initialization task
@app.task(bind=True)
def initialize_project(self, project_id: str, project_data: Dict[str, Any]):
    """Initialize a new project with AI analysis and knowledge graph creation."""
    try:
        logger.info(f"Initializing project {project_id}")
        # Placeholder for project initialization logic
        time.sleep(5)  # Simulate processing time
        return {
            "project_id": project_id,
            "status": "initialized",
            "timestamp": time.time(),
        }
    except Exception as exc:
        logger.error(f"Error initializing project {project_id}: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


# AI analysis task
@app.task(bind=True)
def run_ai_analysis(self, analysis_type: str, data: Dict[str, Any]):
    """Run AI analysis on provided data."""
    try:
        logger.info(f"Running {analysis_type} analysis")
        # Placeholder for AI analysis logic
        time.sleep(3)  # Simulate processing time
        return {
            "analysis_type": analysis_type,
            "status": "completed",
            "results": {"placeholder": "AI analysis results"},
            "timestamp": time.time(),
        }
    except Exception as exc:
        logger.error(f"Error running {analysis_type} analysis: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


# =====================================
# Health Check Web Server for Cloud Run
# =====================================

# Create a minimal FastAPI app for health checks
health_app = FastAPI(title="OriginFD Workers Health Check")


@health_app.get("/health")
def health_check():
    """Health check endpoint for Cloud Run."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "workers",
            "checks": {},
        }

        # Check Redis connectivity
        try:
            redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check Database connectivity
        if SessionLocal:
            try:
                db = get_database_session()
                db.execute("SELECT 1")
                db.close()
                health_status["checks"]["database"] = "healthy"
            except Exception as e:
                health_status["checks"]["database"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@health_app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "service": "OriginFD Workers Service",
        "status": "running",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }


def run_health_server():
    """Run the health check server in a separate thread."""
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting health check server on port {port}")
    uvicorn.run(health_app, host="0.0.0.0", port=port, log_level="warning")


def main():
    """Main entry point for the workers service."""
    logger.info(f"Starting OriginFD Workers Service in {ENVIRONMENT} mode")
    logger.info(f"Redis URL: {REDIS_URL}")

    # Start the health check server in a separate thread
    health_thread = threading.Thread(target=run_health_server)
    health_thread.daemon = True
    health_thread.start()

    logger.info("Health check server started, beginning Celery worker...")

    # Start the Celery worker
    app.worker_main(
        argv=["worker", "--loglevel=info", "--concurrency=4", "--pool=prefork"]
    )


if __name__ == "__main__":
    main()
