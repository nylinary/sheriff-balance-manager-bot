"""Shared helpers and /start, /счета handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import CURRENCIES, settings
from bot.models import async_session
from bot.repositories.settings_repo import SettingsRepo
from bot.repositories.user_repo import UserRepo

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not is_private(message):
        return

    if not is_admin(message.from_user):
        await message.answer("У вас нет доступа к этому боту.")
        return

    # Save admin user to DB so we can look up their telegram_id by username
    user = message.from_user
    async with async_session() as session:
        user_repo = UserRepo(session)
        await user_repo.get_or_create(
            telegram_id=user.id,
            username=user.username,
            full_name=user.full_name,
        )
        await session.commit()

    currency_lines = "\n".join(
        f"  {c.emoji} {c.title} — <code>/{c.command}</code>" for c in CURRENCIES
    )

    text = (
        "👋 Добро пожаловать в <b>Sheriff Balance Manager</b>!\n\n"
        "Бот для учёта мультивалютных операций.\n\n"
        f"💰 <b>Внесение операций</b> (после команды укажите сумму):\n{currency_lines}\n\n"
        "<code>/счета</code> — список доступных валют\n\n"
        "Положительная сумма — приход, отрицательная — расход.\n\n"
        "🔑 <b>Управление:</b>\n"
        "  <code>/дай</code> — текущие балансы\n"
        "  <code>/история</code> — история операций\n"
        "  <code>/выгрузка</code> — выгрузка в Excel"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("инфо"))
async def cmd_info(message: Message) -> None:
    if not is_group(message):
        return

    currency_lines = "\n".join(
        f"  {c.emoji} {c.title} — <code>/{c.command} [сумма]</code>" for c in CURRENCIES
    )

    text = (
        "ℹ️ <b>Доступные команды:</b>\n\n"
        f"💰 <b>Операции</b> (положительная сумма — приход, отрицательная — расход):\n{currency_lines}\n\n"
        "<code>/счета</code> — список доступных валют\n"
        "<code>/инфо</code> — эта справка"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("счета"))
async def cmd_currencies(message: Message) -> None:
    if is_private(message) and not is_admin(message.from_user):
        return

    lines = "\n".join(
        f"{c.emoji} <b>{c.title}</b> — <code>/{c.command}</code>" for c in CURRENCIES
    )
    text = f"💰 <b>Доступные валюты:</b>\n\n{lines}\n\nПосле команды укажите сумму."
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
