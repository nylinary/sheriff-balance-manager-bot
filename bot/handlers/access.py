"""Access window management — admin only."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.common import is_admin, is_private
from bot.models import async_session
from bot.services import AccessWindowService
from bot.utils import parse_time_range

router = Router(name="access")


@router.message(Command("открытьд"))
async def cmd_open_access(message: Message) -> None:
    if not is_private(message) or not is_admin(message.from_user):
        if is_private(message):
            await message.reply("У вас нет доступа к этой команде.")
        return

    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Неверный формат времени. Используйте: /открытьд 19:00-22:00"
        )
        return

    parsed = parse_time_range(args[1])
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


@router.message(Command("закрытьд"))
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
