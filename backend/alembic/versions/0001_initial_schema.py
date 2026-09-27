"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-27 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. financial_profiles table
    op.create_table(
        "financial_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("monthly_income", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("current_savings", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("monthly_debt_payment", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("essential_expenses", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("emergency_savings", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("dependents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_preference", sa.String(length=50), nullable=False, server_default="moderate"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_financial_profiles_user_id"), "financial_profiles", ["user_id"], unique=True)

    # 3. transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_transactions_type"), "transactions", ["type"], unique=False)
    op.create_index(op.f("ix_transactions_category"), "transactions", ["category"], unique=False)
    op.create_index(op.f("ix_transactions_transaction_date"), "transactions", ["transaction_date"], unique=False)

    # 4. budgets table
    op.create_table(
        "budgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("period", sa.String(length=50), nullable=False, server_default="monthly"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_budgets_user_id"), "budgets", ["user_id"], unique=False)
    op.create_index(op.f("ix_budgets_category"), "budgets", ["category"], unique=False)

    # 5. goals table
    op.create_table(
        "goals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("current_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)

    # 6. financial_plans table
    op.create_table(
        "financial_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_data", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_financial_plans_user_id"), "financial_plans", ["user_id"], unique=False)
    op.create_index(op.f("ix_financial_plans_is_active"), "financial_plans", ["is_active"], unique=False)

    # 7. recommendations table
    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("recommendation_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendations_user_id"), "recommendations", ["user_id"], unique=False)
    op.create_index(op.f("ix_recommendations_recommendation_type"), "recommendations", ["recommendation_type"], unique=False)
    op.create_index(op.f("ix_recommendations_status"), "recommendations", ["status"], unique=False)

    # 8. decision_history table
    op.create_table(
        "decision_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("user_action", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("financial_impact", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_decision_history_user_id"), "decision_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_decision_history_status"), "decision_history", ["status"], unique=False)

    # 9. agent_events table
    op.create_table(
        "agent_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("previous_state", sa.JSON(), nullable=True),
        sa.Column("new_state", sa.JSON(), nullable=True),
        sa.Column("responsible_agent", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_events_user_id"), "agent_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_agent_events_event_type"), "agent_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_agent_events_responsible_agent"), "agent_events", ["responsible_agent"], unique=False)


def downgrade() -> None:
    op.drop_table("agent_events")
    op.drop_table("decision_history")
    op.drop_table("recommendations")
    op.drop_table("financial_plans")
    op.drop_table("goals")
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("financial_profiles")
    op.drop_table("users")
