import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecommendationReview(Base):
    __tablename__ = "recommendation_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recommendation_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    decision_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Advisor",
    )
    action: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
        default="accepted",
    )  # "accepted", "modified", "rejected"
    user_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    original_recommendation: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    modified_recommendation: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
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
