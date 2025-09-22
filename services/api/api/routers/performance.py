"""
Performance monitoring and metrics API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from core.performance import db_monitor, health_monitor, rate_limiter, response_cache
from core.redis_config import redis_config
from deps import get_current_user
from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics/summary")
async def get_performance_summary(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get overall performance metrics summary.
    Requires authentication to prevent information disclosure.
    """
    return {
        "requests": {
            "total_processed": health_monitor.request_count,
            "error_count": health_monitor.error_count,
            "error_rate_percent": round(
                (health_monitor.error_count / max(health_monitor.request_count, 1))
                * 100,
                2,
            ),
            "uptime_seconds": round(
                datetime.now().timestamp() - health_monitor.start_time, 2
            ),
        },
        "database": {
            "total_queries": len(db_monitor.query_stats),
            "slow_queries": len(
                [
                    q
                    for q, stats in db_monitor.query_stats.items()
                    if stats["avg_time"] > db_monitor.slow_query_threshold
                ]
            ),
            "average_query_time_ms": round(
                sum(stats["avg_time"] for stats in db_monitor.query_stats.values())
                / max(len(db_monitor.query_stats), 1)
                * 1000,
                2,
            ),
        },
        "redis": await redis_config.health_check(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics/queries")
async def get_query_metrics(
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("avg_time", regex="^(count|total_time|avg_time)$"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get database query performance metrics.
    Returns the slowest/most frequent queries.
    """
    # Sort queries by the specified metric
    sorted_queries = sorted(
        db_monitor.query_stats.items(), key=lambda x: x[1][sort_by], reverse=True
    )

    return {
        "queries": [
            {
                "query": query[:200] + "..." if len(query) > 200 else query,
                "count": stats["count"],
                "total_time_seconds": round(stats["total_time"], 3),
                "avg_time_ms": round(stats["avg_time"] * 1000, 2),
                "is_slow": stats["avg_time"] > db_monitor.slow_query_threshold,
            }
            for query, stats in sorted_queries[:limit]
        ],
        "total_unique_queries": len(db_monitor.query_stats),
        "sorted_by": sort_by,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics/cache")
async def get_cache_metrics(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get cache performance metrics.
    """
    try:
        cache_client = redis_config.get_cache_client()

        # Get cache statistics
        info = cache_client.info()

        # Get cache keys count
        cache_keys = cache_client.keys("api_cache:*")

        return {
            "cache": {
                "total_keys": len(cache_keys),
                "memory_used_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate_percent": round(
                    info.get("keyspace_hits", 0)
                    / max(
                        info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                    )
                    * 100,
                    2,
                ),
                "connected_clients": info.get("connected_clients", 0),
            },
            "redis_version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        return {
            "error": "Failed to retrieve cache metrics",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.post("/cache/invalidate")
async def invalidate_cache_endpoint(
    pattern: str = Query(..., description="Cache key pattern to invalidate"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Invalidate cache entries matching a pattern.
    Requires authentication for security.
    """
    try:
        cache_client = redis_config.get_cache_client()

        # Find matching keys
        keys = cache_client.keys(f"api_cache:*{pattern}*")

        if keys:
            cache_client.delete(*keys)
            invalidated_count = len(keys)
        else:
            invalidated_count = 0

        logger.info(
            f"Cache invalidation by user {current_user['id']}: {invalidated_count} keys matching '{pattern}'"
        )

        return {
            "invalidated_keys": invalidated_count,
            "pattern": pattern,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        return {
            "error": "Failed to invalidate cache",
            "pattern": pattern,
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/metrics/rate-limits")
async def get_rate_limit_metrics(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get rate limiting metrics and active limits.
    """
    try:
        rate_limit_client = redis_config.get_rate_limit_client()

        # Get all rate limit keys
        rate_limit_keys = rate_limit_client.keys("rate_limit:*")

        active_limits = []
        for key in rate_limit_keys[:50]:  # Limit to first 50 for performance
            try:
                # Get the number of requests in the current window
                count = rate_limit_client.zcard(key)
                if count > 0:
                    # Get TTL
                    ttl = rate_limit_client.ttl(key)
                    identifier = key.replace("rate_limit:", "")

                    active_limits.append(
                        {
                            "identifier": identifier,
                            "current_requests": count,
                            "window_expires_in": ttl,
                        }
                    )
            except Exception as e:
                logger.warning(f"Error processing rate limit key {key}: {e}")
                continue

        return {
            "rate_limits": {
                "total_active": len(rate_limit_keys),
                "showing_top": len(active_limits),
                "active_limits": sorted(
                    active_limits, key=lambda x: x["current_requests"], reverse=True
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get rate limit metrics: {e}")
        return {
            "error": "Failed to retrieve rate limit metrics",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/health/comprehensive")
async def comprehensive_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check including all performance metrics.
    Public endpoint for monitoring systems.
    """
    try:
        # Get basic health status
        health_status = await health_monitor.get_health_status()

        # Add Redis health
        redis_health = await redis_config.health_check()
        health_status["redis"] = redis_health

        # Add performance summary
        health_status["performance_summary"] = {
            "total_requests": health_monitor.request_count,
            "error_rate": round(
                (health_monitor.error_count / max(health_monitor.request_count, 1))
                * 100,
                2,
            ),
            "database_queries": len(db_monitor.query_stats),
            "slow_queries": len(
                [
                    q
                    for q, stats in db_monitor.query_stats.items()
                    if stats["avg_time"] > db_monitor.slow_query_threshold
                ]
            ),
        }

        # Determine overall status
        redis_healthy = all(db["healthy"] for db in redis_health.values())
        overall_healthy = (
            health_status.get("database", {}).get("healthy", False)
            and redis_healthy
            and health_status["performance_summary"]["error_rate"]
            < 5.0  # Less than 5% error rate
        )

        health_status["overall_status"] = "healthy" if overall_healthy else "degraded"
        health_status["timestamp"] = datetime.utcnow().isoformat()

        return health_status

    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
