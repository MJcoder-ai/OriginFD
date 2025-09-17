"""
Episodic Memory System for OriginFD AI Orchestrator.
Stores session-based interactions, conversations, and temporal events.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aiofiles
import aiosqlite
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MemoryRecord(BaseModel):
    """Individual memory record."""

    record_id: str
    session_id: str
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: datetime
    interaction_type: (
        str  # "user_message", "agent_response", "tool_execution", "handover", etc.
    )
    content: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    tags: List[str] = []


class SessionSummary(BaseModel):
    """Session summary for quick retrieval."""

    session_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    interaction_count: int
    agents_involved: List[str] = []
    topics: List[str] = []
    summary: Optional[str] = None


class EpisodicMemory:
    """
    Episodic Memory System for storing temporal, session-based interactions.

    Features:
    - Session-based memory organization
    - Fast retrieval by session, user, agent, or timeframe
    - Automatic summarization of long sessions
    - Memory consolidation and cleanup
    - Search and filtering capabilities
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/episodic_memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Memory configuration
        self.max_session_duration = timedelta(hours=24)
        self.max_records_per_session = 1000
        self.cleanup_interval = timedelta(days=1)
        self.retention_period = timedelta(days=30)

        # Active sessions cache
        self.active_sessions: Dict[str, SessionSummary] = {}
        self.session_cache: Dict[str, List[MemoryRecord]] = {}

        logger.info(f"EpisodicMemory initialized with db: {self.db_path}")

    async def initialize(self):
        """Initialize the episodic memory system."""
        logger.info("Initializing EpisodicMemory...")

        # Create database tables
        await self._create_tables()

        # Load active sessions
        await self._load_active_sessions()

        # Start background cleanup
        asyncio.create_task(self._cleanup_worker())

        logger.info("EpisodicMemory initialized successfully")

    async def store_interaction(
        self,
        session_id: str,
        interaction_type: str,
        content: Dict[str, Any],
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Store a new interaction in episodic memory."""
        record = MemoryRecord(
            record_id=str(uuid4()),
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            interaction_type=interaction_type,
            content=content,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Store in database
        await self._store_record(record)

        # Update session cache
        if session_id not in self.session_cache:
            self.session_cache[session_id] = []
        self.session_cache[session_id].append(record)

        # Update session summary
        await self._update_session_summary(session_id, record)

        logger.debug(f"Stored interaction: {record.record_id} in session {session_id}")
        return record.record_id

    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        interaction_types: Optional[List[str]] = None,
    ) -> List[MemoryRecord]:
        """Retrieve interaction history for a session."""
        # Check cache first
        if session_id in self.session_cache:
            records = self.session_cache[session_id]
        else:
            records = await self._load_session_records(session_id)
            self.session_cache[session_id] = records

        # Filter by interaction types if specified
        if interaction_types:
            records = [r for r in records if r.interaction_type in interaction_types]

        # Apply limit
        if limit:
            records = records[-limit:]

        return records

    async def get_user_sessions(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[SessionSummary]:
        """Get all sessions for a user within a timeframe."""
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT session_id, user_id, tenant_id, start_time, end_time,
                       interaction_count, agents_involved, topics, summary
                FROM session_summaries
                WHERE user_id = ?
            """
            params = [user_id]

            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)

            if start_time:
                query += " AND start_time >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND end_time <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY start_time DESC"

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

                return [
                    SessionSummary(
                        session_id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        interaction_count=row[5],
                        agents_involved=json.loads(row[6]) if row[6] else [],
                        topics=json.loads(row[7]) if row[7] else [],
                        summary=row[8],
                    )
                    for row in rows
                ]

    async def search_interactions(
        self,
        query: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        interaction_types: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """Search interactions based on content and filters."""
        async with aiosqlite.connect(self.db_path) as db:
            sql_query = """
                SELECT record_id, session_id, agent_id, user_id, tenant_id,
                       timestamp, interaction_type, content, metadata, tags
                FROM memory_records
                WHERE content LIKE ?
            """
            params = [f"%{query}%"]

            if user_id:
                sql_query += " AND user_id = ?"
                params.append(user_id)

            if tenant_id:
                sql_query += " AND tenant_id = ?"
                params.append(tenant_id)

            if agent_id:
                sql_query += " AND agent_id = ?"
                params.append(agent_id)

            if interaction_types:
                placeholders = ",".join("?" * len(interaction_types))
                sql_query += f" AND interaction_type IN ({placeholders})"
                params.extend(interaction_types)

            if start_time:
                sql_query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                sql_query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            sql_query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            async with db.execute(sql_query, params) as cursor:
                rows = await cursor.fetchall()

                return [
                    MemoryRecord(
                        record_id=row[0],
                        session_id=row[1],
                        agent_id=row[2],
                        user_id=row[3],
                        tenant_id=row[4],
                        timestamp=datetime.fromisoformat(row[5]),
                        interaction_type=row[6],
                        content=json.loads(row[7]),
                        metadata=json.loads(row[8]) if row[8] else {},
                        tags=json.loads(row[9]) if row[9] else [],
                    )
                    for row in rows
                ]

    async def get_session_summary(self, session_id: str) -> Optional[SessionSummary]:
        """Get summary for a specific session."""
        return self.active_sessions.get(session_id)

    async def close_session(self, session_id: str, summary: Optional[str] = None):
        """Close a session and generate summary."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = datetime.utcnow()
            session.summary = summary or await self._generate_session_summary(
                session_id
            )

            # Update in database
            await self._update_session_in_db(session)

            # Remove from active sessions
            self.active_sessions.pop(session_id, None)

            logger.info(f"Closed session: {session_id}")

    async def cleanup_old_records(self, older_than: Optional[datetime] = None):
        """Clean up old memory records."""
        cutoff_time = older_than or (datetime.utcnow() - self.retention_period)

        async with aiosqlite.connect(self.db_path) as db:
            # Delete old records
            await db.execute(
                "DELETE FROM memory_records WHERE timestamp < ?",
                (cutoff_time.isoformat(),),
            )

            # Delete old session summaries
            await db.execute(
                "DELETE FROM session_summaries WHERE end_time < ?",
                (cutoff_time.isoformat(),),
            )

            await db.commit()

        # Clear cache for deleted sessions
        sessions_to_remove = [
            sid
            for sid, session in self.active_sessions.items()
            if session.start_time < cutoff_time
        ]

        for sid in sessions_to_remove:
            self.active_sessions.pop(sid, None)
            self.session_cache.pop(sid, None)

        logger.info(f"Cleaned up records older than {cutoff_time}")

    # Private methods

    async def _create_tables(self):
        """Create database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Memory records table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    record_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT,
                    user_id TEXT,
                    tenant_id TEXT,
                    timestamp TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    tags TEXT
                )
            """
            )

            # Session summaries table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    tenant_id TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    interaction_count INTEGER DEFAULT 0,
                    agents_involved TEXT,
                    topics TEXT,
                    summary TEXT
                )
            """
            )

            # Create indexes
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_id ON memory_records(session_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_id ON memory_records(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_records(timestamp)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_interaction_type ON memory_records(interaction_type)"
            )

            await db.commit()

    async def _store_record(self, record: MemoryRecord):
        """Store a memory record in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO memory_records
                (record_id, session_id, agent_id, user_id, tenant_id, timestamp,
                 interaction_type, content, metadata, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.record_id,
                    record.session_id,
                    record.agent_id,
                    record.user_id,
                    record.tenant_id,
                    record.timestamp.isoformat(),
                    record.interaction_type,
                    json.dumps(record.content),
                    json.dumps(record.metadata),
                    json.dumps(record.tags),
                ),
            )
            await db.commit()

    async def _load_session_records(self, session_id: str) -> List[MemoryRecord]:
        """Load all records for a session from database."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT record_id, session_id, agent_id, user_id, tenant_id,
                       timestamp, interaction_type, content, metadata, tags
                FROM memory_records
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """,
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

                return [
                    MemoryRecord(
                        record_id=row[0],
                        session_id=row[1],
                        agent_id=row[2],
                        user_id=row[3],
                        tenant_id=row[4],
                        timestamp=datetime.fromisoformat(row[5]),
                        interaction_type=row[6],
                        content=json.loads(row[7]),
                        metadata=json.loads(row[8]) if row[8] else {},
                        tags=json.loads(row[9]) if row[9] else [],
                    )
                    for row in rows
                ]

    async def _update_session_summary(self, session_id: str, record: MemoryRecord):
        """Update session summary with new record."""
        if session_id not in self.active_sessions:
            # Create new session summary
            self.active_sessions[session_id] = SessionSummary(
                session_id=session_id,
                user_id=record.user_id,
                tenant_id=record.tenant_id,
                start_time=record.timestamp,
                interaction_count=0,
                agents_involved=[],
                topics=[],
            )

        session = self.active_sessions[session_id]
        session.interaction_count += 1

        # Add agent if not already present
        if record.agent_id and record.agent_id not in session.agents_involved:
            session.agents_involved.append(record.agent_id)

        # Extract topics from content (simple keyword extraction)
        content_text = json.dumps(record.content).lower()
        keywords = [
            "component",
            "design",
            "project",
            "simulation",
            "optimization",
            "procurement",
        ]
        for keyword in keywords:
            if keyword in content_text and keyword not in session.topics:
                session.topics.append(keyword)

        # Update in database
        await self._update_session_in_db(session)

    async def _update_session_in_db(self, session: SessionSummary):
        """Update session summary in database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO session_summaries
                (session_id, user_id, tenant_id, start_time, end_time,
                 interaction_count, agents_involved, topics, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session.session_id,
                    session.user_id,
                    session.tenant_id,
                    session.start_time.isoformat(),
                    session.end_time.isoformat() if session.end_time else None,
                    session.interaction_count,
                    json.dumps(session.agents_involved),
                    json.dumps(session.topics),
                    session.summary,
                ),
            )
            await db.commit()

    async def _load_active_sessions(self):
        """Load active sessions from database."""
        async with aiosqlite.connect(self.db_path) as db:
            # Load sessions that haven't ended
            async with db.execute(
                """
                SELECT session_id, user_id, tenant_id, start_time, end_time,
                       interaction_count, agents_involved, topics, summary
                FROM session_summaries
                WHERE end_time IS NULL
            """
            ) as cursor:
                rows = await cursor.fetchall()

                for row in rows:
                    session = SessionSummary(
                        session_id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        interaction_count=row[5],
                        agents_involved=json.loads(row[6]) if row[6] else [],
                        topics=json.loads(row[7]) if row[7] else [],
                        summary=row[8],
                    )
                    self.active_sessions[session.session_id] = session

    async def _generate_session_summary(self, session_id: str) -> str:
        """Generate AI-powered session summary."""
        records = await self.get_session_history(session_id)

        if not records:
            return "Empty session"

        # Simple summary for now - could be enhanced with AI
        interaction_types = set(r.interaction_type for r in records)
        agent_count = len(set(r.agent_id for r in records if r.agent_id))

        return f"Session with {len(records)} interactions, {agent_count} agents involved. Types: {', '.join(interaction_types)}"

    async def _cleanup_worker(self):
        """Background worker for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self.cleanup_old_records()
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
