from __future__ import annotations

from datetime import date, time

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.access_window import AccessWindow


class AccessRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_window(
        self,
        *,
        target_date: date,
        time_from: time,
        time_to: time,
        created_by: int,
    ) -> AccessWindow:
        # Deactivate any existing windows for this date
        await self.session.execute(
            update(AccessWindow)
            .where(AccessWindow.date == target_date, AccessWindow.is_active == True)  # noqa: E712
            .values(is_active=False)
        )
        window = AccessWindow(
            date=target_date,
            time_from=time_from,
            time_to=time_to,
            is_active=True,
            created_by_telegram_id=created_by,
        )
        self.session.add(window)
        await self.session.flush()
        return window

    async def get_active(self, target_date: date) -> AccessWindow | None:
        stmt = (
            select(AccessWindow)
            .where(AccessWindow.date == target_date, AccessWindow.is_active == True)  # noqa: E712
            .order_by(AccessWindow.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def close_all(self, target_date: date) -> int:
        result = await self.session.execute(
            update(AccessWindow)
            .where(AccessWindow.date == target_date, AccessWindow.is_active == True)  # noqa: E712
            .values(is_active=False, closed_manually=True)
        )
        return result.rowcount  # type: ignore[return-value]
