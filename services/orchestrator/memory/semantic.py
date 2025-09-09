"""
Semantic Memory System for OriginFD AI Orchestrator.
Stores curated knowledge, best practices, and domain expertise.
"""
import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import uuid4
from pydantic import BaseModel
import aiosqlite
import numpy as np
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class KnowledgeItem(BaseModel):
    """Individual knowledge item in semantic memory."""
    knowledge_id: str
    knowledge_type: str  # "best_practice", "domain_fact", "procedure", "pattern", etc.
    title: str
    content: str
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    domain: Optional[str] = None  # PV, BESS, Hybrid, etc.
    confidence: float = 1.0  # 0.0 to 1.0
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embedding: Optional[List[float]] = None  # Vector embedding for similarity search


class KnowledgePattern(BaseModel):
    """Learned pattern from successful executions."""
    pattern_id: str
    pattern_type: str  # "success_pattern", "failure_pattern", "optimization"
    description: str
    conditions: Dict[str, Any]  # When this pattern applies
    actions: List[str]  # What actions to take
    success_rate: float
    usage_count: int
    created_from_executions: List[str]  # Task IDs that created this pattern
    last_updated: datetime


class SemanticMemory:
    """
    Semantic Memory System for storing curated knowledge and learned patterns.
    
    Features:
    - Knowledge categorization and tagging
    - Vector similarity search
    - Pattern learning from successful executions
    - Knowledge validation and confidence scoring
    - Domain-specific knowledge organization
    - Automatic knowledge consolidation
    """
    
    def __init__(self, db_path: Optional[Path] = None, embedding_dim: int = 384):
        self.db_path = db_path or Path("data/semantic_memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_dim = embedding_dim
        
        # Knowledge organization
        self.knowledge_items: Dict[str, KnowledgeItem] = {}
        self.patterns: Dict[str, KnowledgePattern] = {}
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        
        # Configuration
        self.max_knowledge_items = 10000
        self.min_confidence_threshold = 0.3
        self.pattern_learning_threshold = 3  # Min successes to create pattern
        self.consolidation_interval = timedelta(hours=6)
        
        logger.info(f"SemanticMemory initialized with db: {self.db_path}")
    
    async def initialize(self):
        """Initialize the semantic memory system."""
        logger.info("Initializing SemanticMemory...")
        
        # Create database tables
        await self._create_tables()
        
        # Load knowledge items
        await self._load_knowledge_items()
        
        # Load patterns
        await self._load_patterns()
        
        # Start background consolidation
        asyncio.create_task(self._consolidation_worker())
        
        logger.info(f"SemanticMemory initialized with {len(self.knowledge_items)} items and {len(self.patterns)} patterns")
    
    async def store_knowledge(
        self,
        knowledge_type: str,
        title: str,
        content: str,
        domain: Optional[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        source: Optional[str] = None,
        confidence: float = 1.0
    ) -> str:
        """Store a new knowledge item."""
        knowledge_id = str(uuid4())
        
        # Generate embedding for content
        embedding = await self._generate_embedding(f"{title} {content}")
        
        knowledge_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            domain=domain,
            tags=tags or [],
            metadata=metadata or {},
            source=source,
            confidence=confidence,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            embedding=embedding.tolist() if embedding is not None else None
        )
        
        # Store in memory and database
        self.knowledge_items[knowledge_id] = knowledge_item
        if embedding is not None:
            self.embeddings_cache[knowledge_id] = embedding
        
        await self._store_knowledge_item(knowledge_item)
        
        logger.debug(f"Stored knowledge: {knowledge_id} - {title}")
        return knowledge_id
    
    async def retrieve_knowledge(
        self,
        query: str,
        knowledge_types: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_confidence: Optional[float] = None,
        limit: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """Retrieve knowledge items with similarity scoring."""
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        candidates = []
        min_conf = min_confidence or self.min_confidence_threshold
        
        for knowledge_id, item in self.knowledge_items.items():
            # Apply filters
            if knowledge_types and item.knowledge_type not in knowledge_types:
                continue
            if domains and item.domain not in domains:
                continue
            if tags and not any(tag in item.tags for tag in tags):
                continue
            if item.confidence < min_conf:
                continue
            
            # Calculate similarity score
            similarity = 0.0
            if query_embedding is not None and knowledge_id in self.embeddings_cache:
                item_embedding = self.embeddings_cache[knowledge_id]
                similarity = self._cosine_similarity(query_embedding, item_embedding)
            
            # Boost score based on confidence and access patterns
            boosted_score = similarity * item.confidence
            if item.access_count > 0:
                boosted_score *= (1 + np.log(item.access_count) * 0.1)
            
            candidates.append((item, boosted_score))
        
        # Sort by score and limit results
        candidates.sort(key=lambda x: x[1], reverse=True)
        results = candidates[:limit]
        
        # Update access counts
        for item, _ in results:
            await self._update_access_count(item.knowledge_id)
        
        return results
    
    async def learn_pattern(
        self,
        pattern_type: str,
        description: str,
        conditions: Dict[str, Any],
        actions: List[str],
        execution_ids: List[str],
        success_rate: float = 1.0
    ) -> str:
        """Learn a new pattern from successful executions."""
        # Check if similar pattern already exists
        existing_pattern = await self._find_similar_pattern(conditions, actions)
        
        if existing_pattern:
            # Update existing pattern
            existing_pattern.usage_count += 1
            existing_pattern.success_rate = (
                (existing_pattern.success_rate * (existing_pattern.usage_count - 1) + success_rate) 
                / existing_pattern.usage_count
            )
            existing_pattern.created_from_executions.extend(execution_ids)
            existing_pattern.last_updated = datetime.utcnow()
            
            await self._update_pattern(existing_pattern)
            
            logger.info(f"Updated existing pattern: {existing_pattern.pattern_id}")
            return existing_pattern.pattern_id
        else:
            # Create new pattern
            pattern_id = str(uuid4())
            
            pattern = KnowledgePattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                description=description,
                conditions=conditions,
                actions=actions,
                success_rate=success_rate,
                usage_count=1,
                created_from_executions=execution_ids,
                last_updated=datetime.utcnow()
            )
            
            self.patterns[pattern_id] = pattern
            await self._store_pattern(pattern)
            
            logger.info(f"Learned new pattern: {pattern_id} - {description}")
            return pattern_id
    
    async def find_applicable_patterns(
        self,
        current_conditions: Dict[str, Any],
        pattern_types: Optional[List[str]] = None,
        min_success_rate: float = 0.7
    ) -> List[Tuple[KnowledgePattern, float]]:
        """Find patterns applicable to current conditions."""
        applicable_patterns = []
        
        for pattern in self.patterns.values():
            # Filter by pattern type
            if pattern_types and pattern.pattern_type not in pattern_types:
                continue
            
            # Filter by success rate
            if pattern.success_rate < min_success_rate:
                continue
            
            # Calculate condition match score
            match_score = self._calculate_condition_match(
                pattern.conditions, current_conditions
            )
            
            if match_score > 0.5:  # Threshold for applicability
                applicable_patterns.append((pattern, match_score))
        
        # Sort by match score and success rate
        applicable_patterns.sort(
            key=lambda x: x[1] * x[0].success_rate, reverse=True
        )
        
        return applicable_patterns
    
    async def update_knowledge_confidence(
        self,
        knowledge_id: str,
        feedback: str,
        success: bool
    ):
        """Update knowledge confidence based on usage feedback."""
        if knowledge_id not in self.knowledge_items:
            return
        
        item = self.knowledge_items[knowledge_id]
        
        # Adjust confidence based on feedback
        if success:
            item.confidence = min(1.0, item.confidence + 0.1)
        else:
            item.confidence = max(0.0, item.confidence - 0.1)
        
        item.updated_at = datetime.utcnow()
        
        # Store feedback in metadata
        if "feedback_history" not in item.metadata:
            item.metadata["feedback_history"] = []
        
        item.metadata["feedback_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback,
            "success": success
        })
        
        await self._update_knowledge_item(item)
        
        logger.debug(f"Updated confidence for {knowledge_id}: {item.confidence}")
    
    async def search_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 20
    ) -> List[KnowledgeItem]:
        """Search knowledge items by tags."""
        results = []
        
        for item in self.knowledge_items.values():
            if match_all:
                if all(tag in item.tags for tag in tags):
                    results.append(item)
            else:
                if any(tag in item.tags for tag in tags):
                    results.append(item)
        
        # Sort by confidence and access count
        results.sort(
            key=lambda x: (x.confidence, x.access_count), reverse=True
        )
        
        return results[:limit]
    
    async def get_domain_knowledge(
        self,
        domain: str,
        knowledge_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[KnowledgeItem]:
        """Get all knowledge for a specific domain."""
        results = []
        
        for item in self.knowledge_items.values():
            if item.domain == domain:
                if not knowledge_types or item.knowledge_type in knowledge_types:
                    results.append(item)
        
        # Sort by confidence and recency
        results.sort(
            key=lambda x: (x.confidence, x.updated_at), reverse=True
        )
        
        return results[:limit]
    
    async def consolidate_knowledge(self):
        """Consolidate and clean up knowledge base."""
        logger.info("Starting knowledge consolidation...")
        
        # Remove low-confidence items
        items_to_remove = [
            item_id for item_id, item in self.knowledge_items.items()
            if item.confidence < self.min_confidence_threshold and item.access_count == 0
        ]
        
        for item_id in items_to_remove:
            await self._remove_knowledge_item(item_id)
        
        # Merge similar knowledge items
        await self._merge_similar_items()
        
        # Clean up old patterns
        await self._cleanup_old_patterns()
        
        logger.info(f"Consolidation complete. Removed {len(items_to_remove)} items")
    
    async def export_knowledge_base(self, file_path: Path):
        """Export knowledge base to JSON file."""
        export_data = {
            "knowledge_items": {
                item_id: item.dict() for item_id, item in self.knowledge_items.items()
            },
            "patterns": {
                pattern_id: pattern.dict() for pattern_id, pattern in self.patterns.items()
            },
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_items": len(self.knowledge_items),
            "total_patterns": len(self.patterns)
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Knowledge base exported to {file_path}")
    
    # Private methods
    
    async def _create_tables(self):
        """Create database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Knowledge items table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    knowledge_id TEXT PRIMARY KEY,
                    knowledge_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    domain TEXT,
                    tags TEXT,
                    metadata TEXT,
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    embedding BLOB
                )
            """)
            
            # Patterns table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    success_rate REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 0,
                    created_from_executions TEXT,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items(knowledge_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_domain ON knowledge_items(domain)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON knowledge_items(confidence)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_pattern_type ON knowledge_patterns(pattern_type)")
            
            await db.commit()
    
    async def _store_knowledge_item(self, item: KnowledgeItem):
        """Store knowledge item in database."""
        async with aiosqlite.connect(self.db_path) as db:
            embedding_blob = None
            if item.embedding:
                embedding_blob = pickle.dumps(np.array(item.embedding))
            
            await db.execute("""
                INSERT OR REPLACE INTO knowledge_items
                (knowledge_id, knowledge_type, title, content, domain, tags,
                 metadata, source, confidence, created_at, updated_at,
                 access_count, last_accessed, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.knowledge_id, item.knowledge_type, item.title, item.content,
                item.domain, json.dumps(item.tags), json.dumps(item.metadata),
                item.source, item.confidence, item.created_at.isoformat(),
                item.updated_at.isoformat(), item.access_count,
                item.last_accessed.isoformat() if item.last_accessed else None,
                embedding_blob
            ))
            await db.commit()
    
    async def _load_knowledge_items(self):
        """Load knowledge items from database."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT knowledge_id, knowledge_type, title, content, domain,
                       tags, metadata, source, confidence, created_at, updated_at,
                       access_count, last_accessed, embedding
                FROM knowledge_items
            """) as cursor:
                rows = await cursor.fetchall()
                
                for row in rows:
                    embedding = None
                    embedding_list = None
                    if row[13]:  # embedding blob
                        embedding = pickle.loads(row[13])
                        embedding_list = embedding.tolist()
                        self.embeddings_cache[row[0]] = embedding
                    
                    item = KnowledgeItem(
                        knowledge_id=row[0],
                        knowledge_type=row[1],
                        title=row[2],
                        content=row[3],
                        domain=row[4],
                        tags=json.loads(row[5]) if row[5] else [],
                        metadata=json.loads(row[6]) if row[6] else {},
                        source=row[7],
                        confidence=row[8],
                        created_at=datetime.fromisoformat(row[9]),
                        updated_at=datetime.fromisoformat(row[10]),
                        access_count=row[11],
                        last_accessed=datetime.fromisoformat(row[12]) if row[12] else None,
                        embedding=embedding_list
                    )
                    
                    self.knowledge_items[item.knowledge_id] = item
    
    async def _store_pattern(self, pattern: KnowledgePattern):
        """Store pattern in database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO knowledge_patterns
                (pattern_id, pattern_type, description, conditions, actions,
                 success_rate, usage_count, created_from_executions, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_id, pattern.pattern_type, pattern.description,
                json.dumps(pattern.conditions), json.dumps(pattern.actions),
                pattern.success_rate, pattern.usage_count,
                json.dumps(pattern.created_from_executions),
                pattern.last_updated.isoformat()
            ))
            await db.commit()
    
    async def _load_patterns(self):
        """Load patterns from database."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT pattern_id, pattern_type, description, conditions, actions,
                       success_rate, usage_count, created_from_executions, last_updated
                FROM knowledge_patterns
            """) as cursor:
                rows = await cursor.fetchall()
                
                for row in rows:
                    pattern = KnowledgePattern(
                        pattern_id=row[0],
                        pattern_type=row[1],
                        description=row[2],
                        conditions=json.loads(row[3]),
                        actions=json.loads(row[4]),
                        success_rate=row[5],
                        usage_count=row[6],
                        created_from_executions=json.loads(row[7]),
                        last_updated=datetime.fromisoformat(row[8])
                    )
                    
                    self.patterns[pattern.pattern_id] = pattern
    
    async def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text (placeholder - integrate with actual embedding service)."""
        # TODO: Integrate with actual embedding service (OpenAI, Sentence Transformers, etc.)
        # For now, return a random embedding
        if text:
            np.random.seed(hash(text) % 2**32)
            return np.random.normal(0, 1, self.embedding_dim).astype(np.float32)
        return None
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    async def _update_access_count(self, knowledge_id: str):
        """Update access count for knowledge item."""
        if knowledge_id in self.knowledge_items:
            item = self.knowledge_items[knowledge_id]
            item.access_count += 1
            item.last_accessed = datetime.utcnow()
            
            # Update in database periodically (not every access for performance)
            if item.access_count % 10 == 0:
                await self._update_knowledge_item(item)
    
    async def _update_knowledge_item(self, item: KnowledgeItem):
        """Update knowledge item in database."""
        await self._store_knowledge_item(item)
    
    async def _update_pattern(self, pattern: KnowledgePattern):
        """Update pattern in database."""
        await self._store_pattern(pattern)
    
    async def _find_similar_pattern(
        self,
        conditions: Dict[str, Any],
        actions: List[str]
    ) -> Optional[KnowledgePattern]:
        """Find existing pattern similar to the given conditions and actions."""
        for pattern in self.patterns.values():
            condition_similarity = self._calculate_condition_match(
                pattern.conditions, conditions
            )
            action_similarity = self._calculate_action_similarity(
                pattern.actions, actions
            )
            
            if condition_similarity > 0.8 and action_similarity > 0.8:
                return pattern
        
        return None
    
    def _calculate_condition_match(
        self,
        pattern_conditions: Dict[str, Any],
        current_conditions: Dict[str, Any]
    ) -> float:
        """Calculate how well pattern conditions match current conditions."""
        if not pattern_conditions:
            return 0.0
        
        matches = 0
        total = len(pattern_conditions)
        
        for key, value in pattern_conditions.items():
            if key in current_conditions:
                if current_conditions[key] == value:
                    matches += 1
                elif isinstance(value, (int, float)) and isinstance(current_conditions[key], (int, float)):
                    # Numerical similarity
                    diff = abs(value - current_conditions[key])
                    max_val = max(abs(value), abs(current_conditions[key]), 1)
                    similarity = 1 - (diff / max_val)
                    matches += max(0, similarity)
        
        return matches / total
    
    def _calculate_action_similarity(self, actions1: List[str], actions2: List[str]) -> float:
        """Calculate similarity between two action lists."""
        if not actions1 or not actions2:
            return 0.0
        
        set1 = set(actions1)
        set2 = set(actions2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _remove_knowledge_item(self, knowledge_id: str):
        """Remove knowledge item from memory and database."""
        self.knowledge_items.pop(knowledge_id, None)
        self.embeddings_cache.pop(knowledge_id, None)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM knowledge_items WHERE knowledge_id = ?",
                (knowledge_id,)
            )
            await db.commit()
    
    async def _merge_similar_items(self):
        """Merge similar knowledge items to reduce redundancy."""
        # TODO: Implement knowledge item merging based on content similarity
        pass
    
    async def _cleanup_old_patterns(self):
        """Remove old, unused patterns."""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        patterns_to_remove = [
            pattern_id for pattern_id, pattern in self.patterns.items()
            if pattern.usage_count < 3 and pattern.last_updated < cutoff_date
        ]
        
        for pattern_id in patterns_to_remove:
            self.patterns.pop(pattern_id, None)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM knowledge_patterns WHERE pattern_id = ?",
                    (pattern_id,)
                )
                await db.commit()
        
        logger.info(f"Cleaned up {len(patterns_to_remove)} old patterns")
    
    async def _consolidation_worker(self):
        """Background worker for periodic consolidation."""
        while True:
            try:
                await asyncio.sleep(self.consolidation_interval.total_seconds())
                await self.consolidate_knowledge()
            except Exception as e:
                logger.error(f"Consolidation worker error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

