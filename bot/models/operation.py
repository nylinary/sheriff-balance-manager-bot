from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class OperationType(str, enum.Enum):
    income = "income"
    expense = "expense"
    revert = "revert"


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    operation_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    telegram_user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role_snapshot: Mapped[str | None] = mapped_column(String(32), nullable=True)

    chat_id: Mapped[int] = mapped_column(BigInteger)
    chat_type: Mapped[str] = mapped_column(String(32))

    currency_code: Mapped[str] = mapped_column(String(32))
    currency_title: Mapped[str] = mapped_column(String(128))
    currency_command: Mapped[str] = mapped_column(String(64))

    amount: Mapped[int] = mapped_column(BigInteger)
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType))

    is_reverted: Mapped[bool] = mapped_column(Boolean, default=False)
    reverted_operation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revert_parent_operation_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
