"""
CAG (Cache-Augmented Generation) Store for OriginFD AI Orchestrator.
Implements intelligent caching for prompts, embeddings, tool outputs, and simulations.
"""
import asyncio
import json
import logging
import hashlib
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import uuid4
from pydantic import BaseModel
from enum import Enum
import aioredis
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """Types of cached content."""
    PROMPT_RESPONSE = "prompt_response"
    EMBEDDING = "embedding"
    TOOL_OUTPUT = "tool_output"
    SIMULATION_RESULT = "simulation_result"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    AGENT_PLAN = "agent_plan"


class CacheEntry(BaseModel):
    """Individual cache entry."""
    cache_key: str
    cache_type: CacheType
    content: Any
    metadata: Dict[str, Any] = {}
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    hit_count: int = 0
    miss_count: int = 0
    size_bytes: int = 0
    tags: List[str] = []
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None


class CacheStats(BaseModel):
    """Cache performance statistics."""
    total_entries: int
    total_size_bytes: int
    hit_rate: float
    miss_rate: float
    average_response_time_ms: float
    entries_by_type: Dict[CacheType, int]
    top_accessed_keys: List[Tuple[str, int]]
    eviction_count: int
    expired_count: int


class CAGStore:
    """
    Cache-Augmented Generation Store with intelligent caching strategies.

    Features:
    - Multi-tier storage (Redis + SQLite)
    - Content-aware TTL policies
    - Intelligent cache invalidation
    - Performance monitoring
    - Cache warming strategies
    - Drift detection and validation
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db_path: Optional[Path] = None,
        max_memory_mb: int = 512
    ):
        self.redis_url = redis_url
        self.db_path = db_path or Path("data/cag_store.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

        # Storage backends
        self.redis_client: Optional[aioredis.Redis] = None
        self.use_redis = True

        # Cache configuration
        self.default_ttl = {
            CacheType.PROMPT_RESPONSE: timedelta(hours=6),
            CacheType.EMBEDDING: timedelta(days=7),
            CacheType.TOOL_OUTPUT: timedelta(hours=2),
            CacheType.SIMULATION_RESULT: timedelta(hours=12),
            CacheType.KNOWLEDGE_RETRIEVAL: timedelta(hours=4),
            CacheType.AGENT_PLAN: timedelta(minutes=30)
        }

        # Performance tracking
        self.stats = CacheStats(
            total_entries=0,
            total_size_bytes=0,
            hit_rate=0.0,
            miss_rate=0.0,
            average_response_time_ms=0.0,
            entries_by_type={},
            top_accessed_keys=[],
            eviction_count=0,
            expired_count=0
        )

        # Background tasks
        self._cleanup_interval = timedelta(minutes=15)
        self._stats_update_interval = timedelta(minutes=5)

        logger.info(f"CAGStore initialized with max memory: {max_memory_mb}MB")

    async def initialize(self):
        """Initialize the CAG store."""
        logger.info("Initializing CAGStore...")

        # Initialize Redis connection
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                max_connections=20
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to SQLite only.")
            self.use_redis = False

        # Initialize SQLite database
        await self._create_tables()

        # Load existing stats
        await self._load_stats()

        # Start background tasks
        asyncio.create_task(self._cleanup_worker())
        asyncio.create_task(self._stats_updater())

        logger.info("CAGStore initialized successfully")

    async def get(
        self,
        cache_key: str,
        cache_type: Optional[CacheType] = None
    ) -> Optional[Any]:
        """Retrieve content from cache."""
        start_time = time.time()

        try:
            # Try Redis first (hot cache)
            if self.use_redis and self.redis_client:
                content = await self._get_from_redis(cache_key)
                if content is not None:
                    await self._record_hit(cache_key, time.time() - start_time)
                    return content

            # Try SQLite (warm cache)
            content = await self._get_from_sqlite(cache_key)
            if content is not None:
                # Promote to Redis if available
                if self.use_redis and self.redis_client:
                    await self._set_in_redis(cache_key, content, cache_type)

                await self._record_hit(cache_key, time.time() - start_time)
                return content

            # Cache miss
            await self._record_miss(cache_key, time.time() - start_time)
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            await self._record_miss(cache_key, time.time() - start_time)
            return None

    async def set(
        self,
        cache_key: str,
        content: Any,
        cache_type: CacheType,
        ttl: Optional[timedelta] = None,
        tags: List[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store content in cache."""
        try:
            # Calculate size
            content_bytes = self._serialize_content(content)
            size_bytes = len(content_bytes)

            # Check memory limits
            if size_bytes > self.max_memory_bytes * 0.1:  # Don't cache items > 10% of max memory
                logger.warning(f"Content too large to cache: {size_bytes} bytes")
                return False

            # Determine TTL
            effective_ttl = ttl or self.default_ttl.get(cache_type, timedelta(hours=1))
            expires_at = datetime.utcnow() + effective_ttl

            # Create cache entry
            entry = CacheEntry(
                cache_key=cache_key,
                cache_type=cache_type,
                content=content,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                tags=tags or [],
                tenant_id=tenant_id,
                user_id=user_id
            )

            # Store in Redis (hot cache)
            if self.use_redis and self.redis_client:
                await self._set_in_redis(cache_key, content, cache_type, effective_ttl)

            # Store in SQLite (persistent cache)
            await self._set_in_sqlite(entry)

            # Update stats
            self.stats.total_entries += 1
            self.stats.total_size_bytes += size_bytes

            # Trigger cleanup if memory usage is high
            if self.stats.total_size_bytes > self.max_memory_bytes * 0.8:
                asyncio.create_task(self._evict_lru_entries())

            logger.debug(f"Cached content: {cache_key} ({cache_type})")
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False

    async def invalidate(
        self,
        cache_key: Optional[str] = None,
        cache_type: Optional[CacheType] = None,
        tags: Optional[List[str]] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        """Invalidate cache entries based on criteria."""
        invalidated_count = 0

        try:
            # Build filter conditions
            conditions = []
            params = []

            if cache_key:
                conditions.append("cache_key = ?")
                params.append(cache_key)

            if cache_type:
                conditions.append("cache_type = ?")
                params.append(cache_type.value)

            if tenant_id:
                conditions.append("tenant_id = ?")
                params.append(tenant_id)

            # Handle tag-based invalidation
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                conditions.append(f"({' OR '.join(tag_conditions)})")

            if not conditions:
                logger.warning("No invalidation criteria provided")
                return 0

            # Get keys to invalidate
            async with aiosqlite.connect(self.db_path) as db:
                query = f"""
                    SELECT cache_key, size_bytes FROM cache_entries
                    WHERE {' AND '.join(conditions)}
                """

                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()

                    for row in rows:
                        key, size_bytes = row

                        # Remove from Redis
                        if self.use_redis and self.redis_client:
                            await self.redis_client.delete(key)

                        # Update stats
                        self.stats.total_size_bytes -= size_bytes
                        invalidated_count += 1

                # Remove from SQLite
                delete_query = f"""
                    DELETE FROM cache_entries WHERE {' AND '.join(conditions)}
                """
                await db.execute(delete_query, params)
                await db.commit()

            self.stats.total_entries -= invalidated_count

            logger.info(f"Invalidated {invalidated_count} cache entries")
            return invalidated_count

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    async def warm_cache(
        self,
        warming_strategy: str,
        context: Dict[str, Any]
    ):
        """Warm cache with commonly accessed content."""
        logger.info(f"Starting cache warming with strategy: {warming_strategy}")

        if warming_strategy == "popular_embeddings":
            await self._warm_popular_embeddings(context)
        elif warming_strategy == "user_patterns":
            await self._warm_user_patterns(context)
        elif warming_strategy == "simulation_results":
            await self._warm_simulation_results(context)

        logger.info("Cache warming completed")

    async def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        await self._update_stats()
        return self.stats

    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        try:
            current_time = datetime.utcnow()

            # Clean up SQLite
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT cache_key, size_bytes FROM cache_entries
                    WHERE expires_at < ?
                """, (current_time.isoformat(),)) as cursor:
                    expired_rows = await cursor.fetchall()

                if expired_rows:
                    # Remove from Redis
                    if self.use_redis and self.redis_client:
                        expired_keys = [row[0] for row in expired_rows]
                        if expired_keys:
                            await self.redis_client.delete(*expired_keys)

                    # Remove from SQLite
                    await db.execute("""
                        DELETE FROM cache_entries WHERE expires_at < ?
                    """, (current_time.isoformat(),))
                    await db.commit()

                    # Update stats
                    expired_count = len(expired_rows)
                    expired_size = sum(row[1] for row in expired_rows)

                    self.stats.total_entries -= expired_count
                    self.stats.total_size_bytes -= expired_size
                    self.stats.expired_count += expired_count

                    logger.info(f"Cleaned up {expired_count} expired cache entries")
                    return expired_count

            return 0

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

    # Private methods

    async def _create_tables(self):
        """Create SQLite database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    cache_type TEXT NOT NULL,
                    content BLOB NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    hit_count INTEGER DEFAULT 0,
                    miss_count INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0,
                    tags TEXT,
                    tenant_id TEXT,
                    user_id TEXT
                )
            """)

            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_type ON cache_entries(cache_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tenant_id ON cache_entries(tenant_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON cache_entries(access_count)")

            await db.commit()

    async def _get_from_redis(self, cache_key: str) -> Optional[Any]:
        """Get content from Redis."""
        try:
            content_bytes = await self.redis_client.get(cache_key)
            if content_bytes:
                return self._deserialize_content(content_bytes)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def _set_in_redis(
        self,
        cache_key: str,
        content: Any,
        cache_type: Optional[CacheType] = None,
        ttl: Optional[timedelta] = None
    ):
        """Set content in Redis."""
        try:
            content_bytes = self._serialize_content(content)
            ttl_seconds = int(ttl.total_seconds()) if ttl else 3600  # 1 hour default

            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                content_bytes
            )
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def _get_from_sqlite(self, cache_key: str) -> Optional[Any]:
        """Get content from SQLite."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT content, expires_at FROM cache_entries
                    WHERE cache_key = ?
                """, (cache_key,)) as cursor:
                    row = await cursor.fetchone()

                    if row:
                        content_blob, expires_at_str = row

                        # Check expiration
                        if expires_at_str:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if datetime.utcnow() > expires_at:
                                # Entry expired, remove it
                                await db.execute(
                                    "DELETE FROM cache_entries WHERE cache_key = ?",
                                    (cache_key,)
                                )
                                await db.commit()
                                return None

                        # Update access info
                        await db.execute("""
                            UPDATE cache_entries
                            SET access_count = access_count + 1,
                                last_accessed = ?
                            WHERE cache_key = ?
                        """, (datetime.utcnow().isoformat(), cache_key))
                        await db.commit()

                        return self._deserialize_content(content_blob)

                    return None
        except Exception as e:
            logger.error(f"SQLite get error: {e}")
            return None

    async def _set_in_sqlite(self, entry: CacheEntry):
        """Set content in SQLite."""
        try:
            content_bytes = self._serialize_content(entry.content)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO cache_entries
                    (cache_key, cache_type, content, metadata, created_at,
                     expires_at, size_bytes, tags, tenant_id, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.cache_key,
                    entry.cache_type.value,
                    content_bytes,
                    json.dumps(entry.metadata),
                    entry.created_at.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                    entry.size_bytes,
                    json.dumps(entry.tags),
                    entry.tenant_id,
                    entry.user_id
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"SQLite set error: {e}")

    def _serialize_content(self, content: Any) -> bytes:
        """Serialize content for storage."""
        return pickle.dumps(content)

    def _deserialize_content(self, content_bytes: bytes) -> Any:
        """Deserialize content from storage."""
        return pickle.loads(content_bytes)

    async def _record_hit(self, cache_key: str, response_time_ms: float):
        """Record cache hit statistics."""
        # Update global stats (in memory for performance)
        total_hits = self.stats.hit_rate * (self.stats.hit_rate + self.stats.miss_rate)
        total_requests = total_hits + self.stats.miss_rate

        self.stats.hit_rate = (total_hits + 1) / (total_requests + 1)
        self.stats.miss_rate = self.stats.miss_rate / (total_requests + 1)

        # Update response time
        current_avg = self.stats.average_response_time_ms
        self.stats.average_response_time_ms = (current_avg + response_time_ms * 1000) / 2

    async def _record_miss(self, cache_key: str, response_time_ms: float):
        """Record cache miss statistics."""
        # Update global stats
        total_hits = self.stats.hit_rate * (self.stats.hit_rate + self.stats.miss_rate)
        total_requests = total_hits + self.stats.miss_rate

        self.stats.miss_rate = (self.stats.miss_rate + 1) / (total_requests + 1)
        self.stats.hit_rate = total_hits / (total_requests + 1)

    async def _evict_lru_entries(self):
        """Evict least recently used entries to free memory."""
        try:
            target_size = self.max_memory_bytes * 0.7  # Target 70% of max memory
            bytes_to_free = self.stats.total_size_bytes - target_size

            if bytes_to_free <= 0:
                return

            async with aiosqlite.connect(self.db_path) as db:
                # Get LRU entries
                async with db.execute("""
                    SELECT cache_key, size_bytes FROM cache_entries
                    ORDER BY
                        COALESCE(last_accessed, created_at) ASC,
                        access_count ASC
                    LIMIT 100
                """) as cursor:
                    lru_entries = await cursor.fetchall()

                freed_bytes = 0
                evicted_keys = []

                for cache_key, size_bytes in lru_entries:
                    if freed_bytes >= bytes_to_free:
                        break

                    evicted_keys.append(cache_key)
                    freed_bytes += size_bytes

                if evicted_keys:
                    # Remove from Redis
                    if self.use_redis and self.redis_client:
                        await self.redis_client.delete(*evicted_keys)

                    # Remove from SQLite
                    placeholders = ",".join("?" * len(evicted_keys))
                    await db.execute(
                        f"DELETE FROM cache_entries WHERE cache_key IN ({placeholders})",
                        evicted_keys
                    )
                    await db.commit()

                    # Update stats
                    self.stats.total_entries -= len(evicted_keys)
                    self.stats.total_size_bytes -= freed_bytes
                    self.stats.eviction_count += len(evicted_keys)

                    logger.info(f"Evicted {len(evicted_keys)} LRU entries, freed {freed_bytes} bytes")

        except Exception as e:
            logger.error(f"LRU eviction error: {e}")

    async def _warm_popular_embeddings(self, context: Dict[str, Any]):
        """Warm cache with popular embeddings."""
        # TODO: Implement embedding cache warming
        pass

    async def _warm_user_patterns(self, context: Dict[str, Any]):
        """Warm cache based on user access patterns."""
        # TODO: Implement user pattern-based warming
        pass

    async def _warm_simulation_results(self, context: Dict[str, Any]):
        """Warm cache with common simulation results."""
        # TODO: Implement simulation result warming
        pass

    async def _load_stats(self):
        """Load statistics from database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total entries and size
                async with db.execute("""
                    SELECT COUNT(*), COALESCE(SUM(size_bytes), 0) FROM cache_entries
                """) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        self.stats.total_entries = row[0]
                        self.stats.total_size_bytes = row[1]

                # Get entries by type
                async with db.execute("""
                    SELECT cache_type, COUNT(*) FROM cache_entries
                    GROUP BY cache_type
                """) as cursor:
                    rows = await cursor.fetchall()
                    self.stats.entries_by_type = {
                        CacheType(row[0]): row[1] for row in rows
                    }

        except Exception as e:
            logger.error(f"Stats loading error: {e}")

    async def _update_stats(self):
        """Update statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get top accessed keys
                async with db.execute("""
                    SELECT cache_key, access_count FROM cache_entries
                    ORDER BY access_count DESC
                    LIMIT 10
                """) as cursor:
                    rows = await cursor.fetchall()
                    self.stats.top_accessed_keys = [(row[0], row[1]) for row in rows]

        except Exception as e:
            logger.error(f"Stats update error: {e}")

    async def _cleanup_worker(self):
        """Background worker for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval.total_seconds())
                await self.cleanup_expired()

                # Evict if memory usage is high
                if self.stats.total_size_bytes > self.max_memory_bytes * 0.9:
                    await self._evict_lru_entries()

            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                await asyncio.sleep(900)  # Wait 15 minutes on error

    async def _stats_updater(self):
        """Background worker for statistics updates."""
        while True:
            try:
                await asyncio.sleep(self._stats_update_interval.total_seconds())
                await self._update_stats()
            except Exception as e:
                logger.error(f"Stats updater error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

