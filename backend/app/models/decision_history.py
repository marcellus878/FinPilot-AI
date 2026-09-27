import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DecisionHistory(Base):
    __tablename__ = "decision_history"

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
    user_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    decision_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        default="general_decision",
    )  # "large_purchase", "recurring_commitment", "income_change", "emergency_expense", "salary_allocation", "goal_conflict", "plan_adaptation", "general_advice"
    item_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        index=True,
        nullable=True,
    )
    amount: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    strategy_selected: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    alternatives_considered: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    affected_goals: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    baseline_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    resulting_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    assumptions: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    recommendation_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    financial_impact: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
        default="pending",
    )  # "accepted", "rejected", "pending", "active", "superseded"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="decision_history")
