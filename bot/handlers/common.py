"""Shared helpers for handlers."""
from __future__ import annotations

from aiogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.repositories.settings_repo import SettingsRepo


def is_admin(user: User | None) -> bool:
    if user is None:
        return False
    if user.id in settings.admin_ids:
        return True
    if user.username and user.username.lower() in settings.admin_usernames:
        return True
    return False


def is_private(message: Message) -> bool:
    return message.chat.type == "private"


def is_group(message: Message) -> bool:
    return message.chat.type in ("group", "supergroup")


async def is_work_chat(message: Message, session: AsyncSession) -> bool:
    """Check if the message comes from the registered work chat."""
    if not is_group(message):
        return False
    repo = SettingsRepo(session)
    work_id = await repo.get_work_chat_id()
    return work_id is not None and message.chat.id == work_id
