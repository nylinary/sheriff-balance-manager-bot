"""Access window management — admin only."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from bot.handlers.common import is_admin, is_private
from bot.models import async_session
from bot.services import AccessWindowService
from bot.utils import parse_time_range

router = Router(name="access")
logger = logging.getLogger(__name__)


@router.message(Command("открытьд", ignore_case=True))
async def cmd_open_access(message: Message, command: CommandObject) -> None:
    if not is_private(message) or not is_admin(message.from_user):
        if is_private(message):
            await message.reply("У вас нет доступа к этой команде.")
        return

    arg_text = (command.args or "").strip()
    logger.info("open_access raw args: %r", arg_text)
    if not arg_text:
        await message.reply(
            "Неверный формат времени. Используйте: /открытьд 19:00-22:00"
        )
        return

    parsed = parse_time_range(arg_text)
    if parsed is None:
        await message.reply(
            "Неверный формат времени. Используйте: /открытьд 19:00-22:00"
        )
        return

    time_from, time_to = parsed

    async with async_session() as session:
        svc = AccessWindowService(session)
        await svc.open_window(time_from, time_to, created_by=message.from_user.id)  # type: ignore[union-attr]

    f = time_from.strftime("%H:%M")
    t = time_to.strftime("%H:%M")
    await message.answer(f"✅ Доступ открыт на период {f}-{t}.")


@router.message(Command("закрытьд", ignore_case=True))
async def cmd_close_access(message: Message) -> None:
    if not is_private(message) or not is_admin(message.from_user):
        if is_private(message):
            await message.reply("У вас нет доступа к этой команде.")
        return

    async with async_session() as session:
        svc = AccessWindowService(session)
        closed = await svc.close_window()

    if closed:
        await message.answer("✅ Доступ закрыт.")
    else:
        await message.answer("Активного окна доступа не найдено.")
