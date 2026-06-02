"""Add comment column to operations

Revision ID: 003
Revises: 002
Create Date: 2026-06-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("operations", sa.Column("comment", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("operations", "comment")
