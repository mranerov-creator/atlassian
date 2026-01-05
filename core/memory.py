"""
BlueVektor Agents - Memory System
Long-term memory with PostgreSQL + pgvector, session state with Redis.
"""
import json
from datetime import datetime
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
import structlog
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from core.config import get_settings

logger = structlog.get_logger()


# =============================================================================
# SQLAlchemy Models
# =============================================================================

class Base(DeclarativeBase):
    pass


class Conversation(Base):
    """Stores conversation threads."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(50), nullable=False, index=True)
    context_type = Column(String(50), nullable=False)  # e.g., "opportunity", "wp1", "wp4"
    context_id = Column(String(100), nullable=True)    # e.g., opportunity ID
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Stores individual messages in conversations."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")


class Artifact(Base):
    """Stores generated artifacts (documents, analyses, etc.)."""
    __tablename__ = "artifacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(50), nullable=False, index=True)
    artifact_type = Column(String(50), nullable=False)  # e.g., "opportunity_brief", "wp1_report"
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    context_type = Column(String(50), nullable=True)
    context_id = Column(String(100), nullable=True)
    version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_artifacts_context", "context_type", "context_id"),
    )


class KnowledgeChunk(Base):
    """Stores embedded knowledge chunks for RAG."""
    __tablename__ = "knowledge_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source = Column(String(255), nullable=False)      # File path or URL
    chunk_index = Column(String(50), nullable=False)  # Position in source
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)   # OpenAI ada-002 dimensions
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index(
            "ix_knowledge_embedding",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )


class Decision(Base):
    """Decision log for traceability."""
    __tablename__ = "decisions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(50), nullable=False, index=True)
    decision_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    context = Column(JSON, default=dict)
    outcome = Column(String(50), nullable=True)  # approved, rejected, pending
    approved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


# =============================================================================
# Memory Manager
# =============================================================================

class MemoryManager:
    """
    Manages long-term memory (PostgreSQL) and session state (Redis).
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Async PostgreSQL engine
        async_db_url = self.settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self.async_engine = create_async_engine(async_db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Sync engine for migrations
        self.sync_engine = create_engine(self.settings.database_url)
        
        # Redis client
        self._redis: redis.Redis | None = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    async def init_db(self):
        """Initialize database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    
    # -------------------------------------------------------------------------
    # Conversation Management
    # -------------------------------------------------------------------------
    
    async def create_conversation(
        self,
        agent_id: str,
        context_type: str,
        context_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        """Create a new conversation thread."""
        async with self.async_session() as session:
            conversation = Conversation(
                agent_id=agent_id,
                context_type=context_type,
                context_id=context_id,
                metadata_=metadata or {},
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add a message to a conversation."""
        async with self.async_session() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata_=metadata or {},
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get message history for a conversation."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            return [
                {"role": m.role, "content": m.content, "metadata": m.metadata_}
                for m in reversed(messages)
            ]
    
    # -------------------------------------------------------------------------
    # Artifact Management
    # -------------------------------------------------------------------------
    
    async def save_artifact(
        self,
        agent_id: str,
        artifact_type: str,
        name: str,
        content: str,
        context_type: str | None = None,
        context_id: str | None = None,
        metadata: dict | None = None,
    ) -> Artifact:
        """Save a generated artifact."""
        async with self.async_session() as session:
            artifact = Artifact(
                agent_id=agent_id,
                artifact_type=artifact_type,
                name=name,
                content=content,
                context_type=context_type,
                context_id=context_id,
                metadata_=metadata or {},
            )
            session.add(artifact)
            await session.commit()
            await session.refresh(artifact)
            logger.info(
                "Artifact saved",
                artifact_id=artifact.id,
                agent_id=agent_id,
                artifact_type=artifact_type
            )
            return artifact
    
    async def get_artifacts(
        self,
        context_type: str,
        context_id: str,
        artifact_type: str | None = None,
    ) -> list[Artifact]:
        """Get artifacts for a context."""
        async with self.async_session() as session:
            query = select(Artifact).where(
                Artifact.context_type == context_type,
                Artifact.context_id == context_id,
            )
            if artifact_type:
                query = query.where(Artifact.artifact_type == artifact_type)
            
            result = await session.execute(query.order_by(Artifact.created_at.desc()))
            return list(result.scalars().all())
    
    # -------------------------------------------------------------------------
    # Decision Log
    # -------------------------------------------------------------------------
    
    async def log_decision(
        self,
        agent_id: str,
        decision_type: str,
        description: str,
        rationale: str | None = None,
        context: dict | None = None,
        requires_approval: bool = False,
    ) -> Decision:
        """Log a decision for traceability."""
        async with self.async_session() as session:
            decision = Decision(
                agent_id=agent_id,
                decision_type=decision_type,
                description=description,
                rationale=rationale,
                context=context or {},
                outcome="pending" if requires_approval else "auto_approved",
            )
            session.add(decision)
            await session.commit()
            await session.refresh(decision)
            return decision
    
    # -------------------------------------------------------------------------
    # Session State (Redis)
    # -------------------------------------------------------------------------
    
    async def set_state(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int = 3600,
    ) -> None:
        """Set session state in Redis."""
        r = await self.get_redis()
        await r.setex(f"state:{key}", ttl, json.dumps(value))
    
    async def get_state(self, key: str) -> dict[str, Any] | None:
        """Get session state from Redis."""
        r = await self.get_redis()
        data = await r.get(f"state:{key}")
        return json.loads(data) if data else None
    
    async def delete_state(self, key: str) -> None:
        """Delete session state."""
        r = await self.get_redis()
        await r.delete(f"state:{key}")
    
    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------
    
    async def close(self):
        """Close connections."""
        if self._redis:
            await self._redis.close()
        await self.async_engine.dispose()


# Singleton instance
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
