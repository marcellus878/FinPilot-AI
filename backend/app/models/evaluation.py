import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        default="agentic_rag",
    )  # "no_rag", "basic_rag", "agentic_rag"
    llm_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="groq",
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="llama-3.3-70b-versatile",
    )
    total_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    intent_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    tool_selection_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    groundedness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    retrieval_relevance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    structured_output_validity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    reflection_success_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    average_latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    results_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
