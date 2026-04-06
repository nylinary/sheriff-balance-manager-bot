"""Handle bot being added/removed from group chats + chat type commands."""

from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    Command,
    IS_NOT_MEMBER,
    MEMBER,
    ADMINISTRATOR,
)
from aiogram.types import ChatMemberUpdated, Message

from bot.handlers.common import is_admin, is_group
from bot.models import async_session
from bot.repositories.settings_repo import SettingsRepo

router = Router(name="chat_manage")
logger = logging.getLogger(__name__)


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> (MEMBER | ADMINISTRATOR)
    )
)
async def on_bot_added(event: ChatMemberUpdated, bot: Bot) -> None:
    """Bot was added to a group chat."""
    if event.chat.type not in ("group", "supergroup"):
        return

    # Only admins can add the bot
    if not is_admin(event.from_user):
        logger.warning(
            "Non-admin %s (%s) tried to add bot to chat %s. Leaving.",
            event.from_user.id,
            event.from_user.username,
            event.chat.id,
        )
        await bot.send_message(
            event.chat.id, "Только администратор бота может добавить меня в чат."
        )
        await bot.leave_chat(event.chat.id)
        return

    await bot.send_message(
        event.chat.id,
        "✅ Бот добавлен.\n\n"
        "Назначьте тип чата командой:\n"
        "  <code>/сотрудники</code> — рабочий чат сотрудников\n"
        "  <code>/админы</code> — чат администраторов",
        parse_mode="HTML",
    )
    logger.info("Bot added to chat %s by admin %s", event.chat.id, event.from_user.id)


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(MEMBER | ADMINISTRATOR) >> IS_NOT_MEMBER
    )
)
async def on_bot_removed(event: ChatMemberUpdated) -> None:
    """Bot was removed from a group chat."""
    async with async_session() as session:
        repo = SettingsRepo(session)
        work_id = await repo.get_work_chat_id()
        admin_id = await repo.get_admin_chat_id()
        if work_id == event.chat.id:
            await repo.delete("work_chat_id")
            logger.info("Work chat %s unregistered (bot removed).", event.chat.id)
        if admin_id == event.chat.id:
            await repo.delete("admin_chat_id")
            logger.info("Admin chat %s unregistered (bot removed).", event.chat.id)
        await session.commit()


# ── Chat type commands ───────────────────────────────────────────


@router.message(Command("сотрудники"))
async def cmd_set_work_chat(message: Message) -> None:
    if not is_group(message) or not is_admin(message.from_user):
        return

    async with async_session() as session:
        repo = SettingsRepo(session)

        # Don't allow changing if already registered as admin chat
        admin_id = await repo.get_admin_chat_id()
        if admin_id == message.chat.id:
            await message.answer("❌ Этот чат уже зарегистрирован как админский.")
            return

        # Don't allow re-registering
        work_id = await repo.get_work_chat_id()
        if work_id == message.chat.id:
            await message.answer("ℹ️ Этот чат уже зарегистрирован как рабочий.")
            return

        await repo.set_work_chat_id(message.chat.id)
        await session.commit()

    logger.info(
        "Work chat set to %s by admin %s", message.chat.id, message.from_user.id
    )
    await message.answer(
        f"✅ Рабочий чат сотрудников установлен (ID: {message.chat.id})."
    )


@router.message(Command("админы"))
async def cmd_set_admin_chat(message: Message) -> None:
    if not is_group(message) or not is_admin(message.from_user):
        return

    async with async_session() as session:
        repo = SettingsRepo(session)

        # Don't allow changing if already registered as work chat
        work_id = await repo.get_work_chat_id()
        if work_id == message.chat.id:
            await message.answer("❌ Этот чат уже зарегистрирован как рабочий.")
            return

        # Don't allow re-registering
        admin_id = await repo.get_admin_chat_id()
        if admin_id == message.chat.id:
            await message.answer("ℹ️ Этот чат уже зарегистрирован как админский.")
            return

        await repo.set_admin_chat_id(message.chat.id)
        await session.commit()

    logger.info(
        "Admin chat set to %s by admin %s", message.chat.id, message.from_user.id
    )
    await message.answer(f"✅ Чат администраторов установлен (ID: {message.chat.id}).")
