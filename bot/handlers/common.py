"""Shared helpers and /start, /счета handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import CURRENCIES, settings
from bot.repositories.settings_repo import SettingsRepo

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    currency_lines = "\n".join(
        f"  /{c.command} [сумма] — {c.emoji} {c.title}" for c in CURRENCIES
    )
    admin_section = ""
    if is_admin(message.from_user):
        admin_section = (
            "\n\n🔑 <b>Команды администратора:</b>\n"
            "  /кошелек — текущие балансы\n"
            "  /история — история операций\n"
            "  /выгрузка — выгрузка в Excel"
        )

    text = (
        "👋 Добро пожаловать в <b>Sheriff Balance Manager</b>!\n\n"
        "Бот для учёта мультивалютных операций.\n\n"
        f"💰 <b>Внесение операций:</b>\n{currency_lines}\n\n"
        "📋 /счета — список доступных валют\n\n"
        f"Положительная сумма — приход, отрицательная — расход."
        f"{admin_section}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("счета"))
async def cmd_currencies(message: Message) -> None:
    lines = "\n".join(
        f"{c.emoji} <b>{c.title}</b> — /{c.command} [сумма]" for c in CURRENCIES
    )
    text = f"💰 <b>Доступные валюты:</b>\n\n{lines}"
    await message.answer(text, parse_mode="HTML")


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
