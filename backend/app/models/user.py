import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile
    from app.models.transaction import Transaction
    from app.models.budget import Budget
    from app.models.goal import Goal
    from app.models.financial_plan import FinancialPlan
    from app.models.recommendation import Recommendation
    from app.models.decision_history import DecisionHistory
    from app.models.agent_event import AgentEvent


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    # 1-to-1 relationship
    financial_profile: Mapped[Optional["FinancialProfile"]] = relationship(
        "FinancialProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-to-many relationships
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    budgets: Mapped[List["Budget"]] = relationship(
        "Budget",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    goals: Mapped[List["Goal"]] = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    financial_plans: Mapped[List["FinancialPlan"]] = relationship(
        "FinancialPlan",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    decision_history: Mapped[List["DecisionHistory"]] = relationship(
        "DecisionHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    agent_events: Mapped[List["AgentEvent"]] = relationship(
        "AgentEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
