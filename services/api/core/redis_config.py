"""
Redis configuration for caching and rate limiting.
"""

import logging
import os
from typing import Optional

import redis

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration manager."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.cache_db = int(os.getenv("REDIS_CACHE_DB", "1"))
        self.rate_limit_db = int(os.getenv("REDIS_RATE_LIMIT_DB", "2"))
        self.session_db = int(os.getenv("REDIS_SESSION_DB", "3"))

        # Connection pools for different use cases
        self._cache_pool: Optional[redis.ConnectionPool] = None
        self._rate_limit_pool: Optional[redis.ConnectionPool] = None
        self._session_pool: Optional[redis.ConnectionPool] = None

    @property
    def cache_pool(self) -> redis.ConnectionPool:
        """Get or create cache connection pool."""
        if self._cache_pool is None:
            self._cache_pool = redis.ConnectionPool.from_url(
                f"{self.redis_url}/{self.cache_db}",
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True,
            )
        return self._cache_pool

    @property
    def rate_limit_pool(self) -> redis.ConnectionPool:
        """Get or create rate limit connection pool."""
        if self._rate_limit_pool is None:
            self._rate_limit_pool = redis.ConnectionPool.from_url(
                f"{self.redis_url}/{self.rate_limit_db}",
                max_connections=10,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True,
            )
        return self._rate_limit_pool

    @property
    def session_pool(self) -> redis.ConnectionPool:
        """Get or create session connection pool."""
        if self._session_pool is None:
            self._session_pool = redis.ConnectionPool.from_url(
                f"{self.redis_url}/{self.session_db}",
                max_connections=15,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True,
            )
        return self._session_pool

    def get_cache_client(self) -> redis.Redis:
        """Get Redis client for caching."""
        return redis.Redis(connection_pool=self.cache_pool)

    def get_rate_limit_client(self) -> redis.Redis:
        """Get Redis client for rate limiting."""
        return redis.Redis(connection_pool=self.rate_limit_pool)

    def get_session_client(self) -> redis.Redis:
        """Get Redis client for sessions."""
        return redis.Redis(connection_pool=self.session_pool)

    async def health_check(self) -> dict:
        """Check Redis health for all databases."""
        health_status = {
            "cache": {"healthy": False, "error": None},
            "rate_limit": {"healthy": False, "error": None},
            "session": {"healthy": False, "error": None},
        }

        # Test cache database
        try:
            cache_client = self.get_cache_client()
            cache_client.ping()
            health_status["cache"]["healthy"] = True
        except Exception as e:
            health_status["cache"]["error"] = str(e)
            logger.warning(f"Cache Redis health check failed: {e}")

        # Test rate limit database
        try:
            rate_limit_client = self.get_rate_limit_client()
            rate_limit_client.ping()
            health_status["rate_limit"]["healthy"] = True
        except Exception as e:
            health_status["rate_limit"]["error"] = str(e)
            logger.warning(f"Rate limit Redis health check failed: {e}")

        # Test session database
        try:
            session_client = self.get_session_client()
            session_client.ping()
            health_status["session"]["healthy"] = True
        except Exception as e:
            health_status["session"]["error"] = str(e)
            logger.warning(f"Session Redis health check failed: {e}")

        return health_status

    def close_connections(self):
        """Close all Redis connection pools."""
        pools = [self._cache_pool, self._rate_limit_pool, self._session_pool]
        for pool in pools:
            if pool:
                pool.disconnect()

        # Reset pools
        self._cache_pool = None
        self._rate_limit_pool = None
        self._session_pool = None


# Global Redis configuration instance
redis_config = RedisConfig()
