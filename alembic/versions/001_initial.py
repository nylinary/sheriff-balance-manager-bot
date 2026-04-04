"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-04-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "telegram_id", sa.BigInteger, unique=True, index=True, nullable=False
        ),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(512), nullable=True),
        sa.Column(
            "role",
            sa.Enum("admin", "employee", name="userrole"),
            nullable=False,
            server_default="employee",
        ),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "balances",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "currency_code", sa.String(32), unique=True, index=True, nullable=False
        ),
        sa.Column("amount", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "operations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("operation_id", sa.Integer, unique=True, index=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger, nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(512), nullable=True),
        sa.Column("role_snapshot", sa.String(32), nullable=True),
        sa.Column("chat_id", sa.BigInteger, nullable=False),
        sa.Column("chat_type", sa.String(32), nullable=False),
        sa.Column("currency_code", sa.String(32), nullable=False),
        sa.Column("currency_title", sa.String(128), nullable=False),
        sa.Column("currency_command", sa.String(64), nullable=False),
        sa.Column("amount", sa.BigInteger, nullable=False),
        sa.Column(
            "operation_type",
            sa.Enum("income", "expense", "revert", name="operationtype"),
            nullable=False,
        ),
        sa.Column(
            "is_reverted", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column("reverted_operation_id", sa.Integer, nullable=True),
        sa.Column("revert_parent_operation_id", sa.Integer, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("meta_json", sa.JSON, nullable=True),
    )

    op.create_table(
        "access_windows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("time_from", sa.Time, nullable=False),
        sa.Column("time_to", sa.Time, nullable=False),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "closed_manually",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_by_telegram_id", sa.BigInteger, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # Sequence for business operation_id
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS operation_id_seq START 1"))


def downgrade() -> None:
    op.execute(sa.text("DROP SEQUENCE IF EXISTS operation_id_seq"))
    op.drop_table("access_windows")
    op.drop_table("operations")
    op.drop_table("balances")
    op.drop_table("users")
    op.execute(sa.text("DROP TYPE IF EXISTS userrole"))
    op.execute(sa.text("DROP TYPE IF EXISTS operationtype"))
