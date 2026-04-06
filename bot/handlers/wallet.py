"""Wallet display — admin only, private chat or admin group."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.handlers.common import is_admin, is_admin_chat, is_admin_context, is_private
from bot.models import async_session
from bot.services import BalanceService

router = Router(name="wallet")


@router.message(Command("кошелек", "дай"))
async def cmd_wallet(message: Message) -> None:
    async with async_session() as session:
        in_admin_chat = await is_admin_chat(message, session)

    if not is_admin_context(message, in_admin_chat=in_admin_chat):
        if is_private(message):
            await message.reply("У вас нет доступа к этой команде.")
        return

    async with async_session() as session:
        svc = BalanceService(session)
        text = await svc.get_wallet_text()
    await message.answer(text)


@router.callback_query(lambda c: c.data == "w:show")
async def cb_wallet(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user):
        await callback.answer("У вас нет доступа.", show_alert=True)
        return

    async with async_session() as session:
        svc = BalanceService(session)
        text = await svc.get_wallet_text()
    await callback.message.answer(text)  # type: ignore[union-attr]
    await callback.answer()
