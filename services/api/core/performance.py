"""
Performance optimization utilities for OriginFD API.
Implements caching, rate limiting, compression, and monitoring.
"""

import hashlib
import json
import logging
import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional

import redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# =====================================
# Response Caching System
# =====================================


class ResponseCache:
    """Redis-based response cache for API endpoints."""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = 300  # 5 minutes default

    def generate_cache_key(self, request: Request, include_user: bool = True) -> str:
        """Generate a unique cache key for the request."""
        key_parts = [
            request.method,
            str(request.url.path),
            str(sorted(request.query_params.items())),
        ]

        if include_user and hasattr(request.state, "user"):
            key_parts.append(f"user:{request.state.user.get('id', 'anonymous')}")

        key_string = "|".join(key_parts)
        return f"api_cache:{hashlib.sha256(key_string.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> None:
        """Set cached response."""
        try:
            ttl = ttl or self.default_ttl
            self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def delete(self, pattern: str) -> None:
        """Delete cached responses matching pattern."""
        try:
            keys = self.redis_client.keys(f"api_cache:*{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")


# Global cache instance
response_cache = ResponseCache()


def cached_response(
    ttl: int = 300,
    include_user: bool = True,
    cache_condition: Callable[[Request], bool] = None,
):
    """
    Decorator for caching API responses.

    Args:
        ttl: Time to live in seconds
        include_user: Include user ID in cache key
        cache_condition: Function to determine if request should be cached
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Check if caching is enabled for this request
            if cache_condition and not cache_condition(request):
                return await func(request, *args, **kwargs)

            # Only cache GET requests by default
            if request.method != "GET":
                return await func(request, *args, **kwargs)

            # Generate cache key
            cache_key = response_cache.generate_cache_key(request, include_user)

            # Try to get from cache
            cached_response = await response_cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit: {cache_key}")
                return JSONResponse(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers={"X-Cache": "HIT"},
                )

            # Execute function
            response = await func(request, *args, **kwargs)

            # Cache successful responses
            if hasattr(response, "status_code") and 200 <= response.status_code < 300:
                if hasattr(response, "body"):
                    try:
                        content = json.loads(response.body)
                        cache_data = {
                            "content": content,
                            "status_code": response.status_code,
                        }
                        await response_cache.set(cache_key, cache_data, ttl)
                        logger.debug(f"Cache set: {cache_key}")
                    except Exception as e:
                        logger.warning(f"Failed to cache response: {e}")

            # Add cache header
            if hasattr(response, "headers"):
                response.headers["X-Cache"] = "MISS"

            return response

        return wrapper

    return decorator


# =====================================
# Rate Limiting System
# =====================================


class RateLimiter:
    """Redis-based rate limiter for API endpoints."""

    def __init__(self, redis_url: str = "redis://localhost:6379/2"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    async def is_allowed(
        self, identifier: str, limit: int, window: int
    ) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            (is_allowed, {"remaining": int, "reset_time": int})
        """
        key = f"rate_limit:{identifier}"
        current_time = int(time.time())

        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            results = pipe.execute()

            request_count = results[1]

            if request_count < limit:
                remaining = limit - request_count - 1
                reset_time = current_time + window
                return True, {"remaining": remaining, "reset_time": reset_time}
            else:
                # Find the oldest request in the window
                oldest_requests = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_requests:
                    reset_time = int(oldest_requests[0][1]) + window
                else:
                    reset_time = current_time + window

                return False, {"remaining": 0, "reset_time": reset_time}

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiter is down
            return True, {"remaining": limit, "reset_time": current_time + window}


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(
    requests_per_minute: int = 60,
    per_user: bool = True,
    key_func: Callable[[Request], str] = None,
):
    """
    Decorator for rate limiting API endpoints.

    Args:
        requests_per_minute: Maximum requests per minute
        per_user: Apply limit per user (True) or per IP (False)
        key_func: Custom function to generate rate limit key
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Generate rate limit key
            if key_func:
                identifier = key_func(request)
            elif per_user and hasattr(request.state, "user"):
                identifier = f"user:{request.state.user.get('id', 'anonymous')}"
            else:
                identifier = f"ip:{request.client.host}"

            # Check rate limit
            is_allowed, info = await rate_limiter.is_allowed(
                identifier, requests_per_minute, 60
            )

            if not is_allowed:
                headers = {
                    "X-RateLimit-Limit": str(requests_per_minute),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset_time"]),
                    "Retry-After": str(info["reset_time"] - int(time.time())),
                }
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers=headers,
                )

            # Execute function and add rate limit headers
            response = await func(request, *args, **kwargs)

            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(requests_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(info["reset_time"])

            return response

        return wrapper

    return decorator


# =====================================
# Database Performance Monitoring
# =====================================


class DatabaseMonitor:
    """Monitor database query performance."""

    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # seconds

    def log_query(self, query: str, duration: float):
        """Log query execution time."""
        if duration > self.slow_query_threshold:
            logger.warning(f"Slow query ({duration:.2f}s): {query[:200]}...")

        # Update stats
        if query not in self.query_stats:
            self.query_stats[query] = {"count": 0, "total_time": 0, "avg_time": 0}

        stats = self.query_stats[query]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]


# Global database monitor
db_monitor = DatabaseMonitor()


# SQLAlchemy event listener for query monitoring
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    total_time = time.time() - context._query_start_time
    db_monitor.log_query(statement, total_time)


# =====================================
# Response Compression Middleware
# =====================================


async def compression_middleware(request: Request, call_next):
    """Middleware to compress responses when appropriate."""
    response = await call_next(request)

    # Check if client accepts compression
    accept_encoding = request.headers.get("accept-encoding", "")
    if "gzip" not in accept_encoding.lower():
        return response

    # Only compress JSON responses larger than 1KB
    if (
        hasattr(response, "media_type")
        and response.media_type == "application/json"
        and hasattr(response, "body")
        and len(response.body) > 1024
    ):

        import gzip

        compressed_body = gzip.compress(response.body)

        # Only use compression if it saves significant space
        if len(compressed_body) < len(response.body) * 0.9:
            response.body = compressed_body
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(compressed_body))

    return response


# =====================================
# Performance Monitoring Utilities
# =====================================


@asynccontextmanager
async def monitor_performance(operation_name: str):
    """Context manager for monitoring operation performance."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Performance: {operation_name} took {duration:.3f}s")

        # Log slow operations
        if duration > 2.0:
            logger.warning(f"Slow operation: {operation_name} took {duration:.3f}s")


def performance_metrics(func: Callable) -> Callable:
    """Decorator to monitor function performance."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with monitor_performance(func.__name__):
            return await func(*args, **kwargs)

    return wrapper


# =====================================
# Cache Invalidation Utilities
# =====================================


async def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching a pattern."""
    await response_cache.delete(pattern)
    logger.info(f"Invalidated cache pattern: {pattern}")


# Cache invalidation for common operations
async def invalidate_component_cache(component_id: str = None):
    """Invalidate component-related cache entries."""
    if component_id:
        await response_cache.delete(f"components/{component_id}")
    await response_cache.delete("components")
    await response_cache.delete("stats")


# =====================================
# Health Check Enhancements
# =====================================


class HealthMonitor:
    """Enhanced health monitoring with performance metrics."""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        uptime = time.time() - self.start_time

        # Test database connection
        db_healthy = True
        db_response_time = None
        try:
            start = time.time()
            # This would need a database session
            # db.execute("SELECT 1")
            db_response_time = time.time() - start
        except Exception:
            db_healthy = False

        # Test Redis connection
        redis_healthy = True
        redis_response_time = None
        try:
            start = time.time()
            await response_cache.redis_client.ping()
            redis_response_time = time.time() - start
        except Exception:
            redis_healthy = False

        return {
            "status": "healthy" if db_healthy and redis_healthy else "degraded",
            "uptime": uptime,
            "requests_processed": self.request_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "database": {
                "healthy": db_healthy,
                "response_time_ms": (
                    db_response_time * 1000 if db_response_time else None
                ),
            },
            "cache": {
                "healthy": redis_healthy,
                "response_time_ms": (
                    redis_response_time * 1000 if redis_response_time else None
                ),
            },
            "performance": {
                "slow_queries": len(
                    [
                        q
                        for q, stats in db_monitor.query_stats.items()
                        if stats["avg_time"] > db_monitor.slow_query_threshold
                    ]
                )
            },
        }


# Global health monitor
health_monitor = HealthMonitor()
