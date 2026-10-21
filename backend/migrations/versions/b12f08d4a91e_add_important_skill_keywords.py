"""add important skill keywords to saved comparisons

Revision ID: b12f08d4a91e
Revises: a24063bc79d0
Create Date: 2026-10-21 00:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b12f08d4a91e"
down_revision: Union[str, None] = "a24063bc79d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "skill_comparisons",
        sa.Column(
            "important_keywords",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("skill_comparisons", "important_keywords")
