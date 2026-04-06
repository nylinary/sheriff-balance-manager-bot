from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_settings import BotSetting

WORK_CHAT_KEY = "work_chat_id"
ADMIN_CHAT_KEY = "admin_chat_id"


class SettingsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def set(self, key: str, value: str) -> None:
        result = await self.session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        row = result.scalar_one_or_none()
        if row is None:
            self.session.add(BotSetting(key=key, value=value))
        else:
            row.value = value
        await self.session.flush()

    async def delete(self, key: str) -> None:
        result = await self.session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            await self.session.delete(row)
            await self.session.flush()

    async def get_work_chat_id(self) -> int | None:
        val = await self.get(WORK_CHAT_KEY)
        return int(val) if val else None

    async def set_work_chat_id(self, chat_id: int) -> None:
        await self.set(WORK_CHAT_KEY, str(chat_id))

    async def get_admin_chat_id(self) -> int | None:
        val = await self.get(ADMIN_CHAT_KEY)
        return int(val) if val else None

    async def set_admin_chat_id(self, chat_id: int) -> None:
        await self.set(ADMIN_CHAT_KEY, str(chat_id))
