"""goals_category_and_contribution

Revision ID: 0003_goals_category_and_contribution
Revises: 0002_user_auth_and_decision_memory
Create Date: 2026-09-27 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_goals_category_and_contribution"
down_revision: Union[str, None] = "0002_user_auth_and_decision_memory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("goals") as batch_op:
        batch_op.add_column(
            sa.Column("category", sa.String(length=100), nullable=False, server_default="General")
        )
        batch_op.add_column(
            sa.Column("monthly_contribution", sa.Numeric(precision=12, scale=2), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("goals") as batch_op:
        batch_op.drop_column("monthly_contribution")
        batch_op.drop_column("category")
