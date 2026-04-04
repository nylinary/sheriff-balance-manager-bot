"""Handle bot being added/removed from group chats."""
from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR
from aiogram.types import ChatMemberUpdated

from bot.handlers.common import is_admin
from bot.models import async_session
from bot.repositories.settings_repo import SettingsRepo

router = Router(name="chat_manage")
logger = logging.getLogger(__name__)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> (MEMBER | ADMINISTRATOR)))
async def on_bot_added(event: ChatMemberUpdated, bot: Bot) -> None:
    """Bot was added to a group chat."""
    if event.chat.type not in ("group", "supergroup"):
        return

    # Only admins can register the work chat
    if not is_admin(event.from_user):
        logger.warning(
            "Non-admin %s (%s) tried to add bot to chat %s. Leaving.",
            event.from_user.id,
            event.from_user.username,
            event.chat.id,
        )
        await bot.send_message(event.chat.id, "Только администратор бота может добавить меня в чат.")
        await bot.leave_chat(event.chat.id)
        return

    async with async_session() as session:
        repo = SettingsRepo(session)
        await repo.set_work_chat_id(event.chat.id)
        await session.commit()

    logger.info("Work chat set to %s by admin %s", event.chat.id, event.from_user.id)
    await bot.send_message(event.chat.id, f"✅ Рабочий чат установлен (ID: {event.chat.id}).")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(MEMBER | ADMINISTRATOR) >> IS_NOT_MEMBER))
async def on_bot_removed(event: ChatMemberUpdated) -> None:
    """Bot was removed from a group chat."""
    async with async_session() as session:
        repo = SettingsRepo(session)
        current = await repo.get_work_chat_id()
        if current == event.chat.id:
            await repo.delete("work_chat_id")
            await session.commit()
            logger.info("Work chat %s unregistered (bot removed).", event.chat.id)
