from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class AccessWindow(Base):
    __tablename__ = "access_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    time_from: Mapped[time] = mapped_column(Time)
    time_to: Mapped[time] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_manually: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_telegram_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
