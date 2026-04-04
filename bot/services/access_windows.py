from __future__ import annotations

from datetime import time

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.access_window import AccessWindow
from bot.repositories import AccessRepo
from bot.utils.time import now


class AccessWindowService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AccessRepo(session)

    async def open_window(
        self,
        time_from: time,
        time_to: time,
        created_by: int,
    ) -> AccessWindow:
        current = now()
        window = await self.repo.create_window(
            target_date=current.date(),
            time_from=time_from,
            time_to=time_to,
            created_by=created_by,
        )
        await self.session.commit()
        return window

    async def close_window(self) -> bool:
        current = now()
        count = await self.repo.close_all(current.date())
        await self.session.commit()
        return count > 0

    async def is_access_open(self) -> bool:
        current = now()
        window = await self.repo.get_active(current.date())
        if window is None:
            return False
        current_time = current.time()
        return window.time_from <= current_time <= window.time_to
