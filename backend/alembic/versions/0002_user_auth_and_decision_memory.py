"""user_auth_and_decision_memory

Revision ID: 0002_user_auth_and_decision_memory
Revises: 0001_initial_schema
Create Date: 2026-09-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_user_auth_and_decision_memory"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add hashed_password column to users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default="")
        )

    # Add extended decision memory columns to decision_history table
    with op.batch_alter_table("decision_history") as batch_op:
        batch_op.add_column(sa.Column("decision_type", sa.String(length=50), nullable=True, server_default="purchase"))
        batch_op.add_column(sa.Column("item_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("strategy_selected", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("alternatives_considered", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("affected_goals", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("baseline_metrics", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("resulting_metrics", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("assumptions", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("recommendation_summary", sa.Text(), nullable=True))
        batch_op.create_index(op.f("ix_decision_history_decision_type"), ["decision_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("decision_history") as batch_op:
        batch_op.drop_index(op.f("ix_decision_history_decision_type"))
        batch_op.drop_column("recommendation_summary")
        batch_op.drop_column("assumptions")
        batch_op.drop_column("resulting_metrics")
        batch_op.drop_column("baseline_metrics")
        batch_op.drop_column("affected_goals")
        batch_op.drop_column("alternatives_considered")
        batch_op.drop_column("strategy_selected")
        batch_op.drop_column("amount")
        batch_op.drop_column("item_name")
        batch_op.drop_column("decision_type")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("hashed_password")
