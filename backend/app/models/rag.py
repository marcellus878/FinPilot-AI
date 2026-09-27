import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    publisher: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False,
    )
    url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        default="general_finance",
    )
    doc_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="guide",
    )
    license: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )
    publication_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    embedding_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON serialized vector for SQLite / fallback storage
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument",
        back_populates="chunks",
    )


class RetrievalEvent(Base):
    __tablename__ = "retrieval_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=True,
    )
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    intent: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general_query",
    )
    category_filter: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    retrieved_chunk_ids: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
    )
    sufficiency_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    refinement_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    sources_cited: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
