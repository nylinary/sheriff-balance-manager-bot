"""Handlers for currency operation commands (available in group chat)."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import CURRENCIES, CURRENCY_BY_COMMAND
from bot.handlers.common import is_admin, is_group, is_work_chat
from bot.models import async_session
from bot.services import AccessWindowService, OperationService
from bot.utils import format_amount, parse_amount

router = Router(name="employee")


async def _handle_currency_command(message: Message, command_text: str) -> None:
    currency = CURRENCY_BY_COMMAND.get(command_text)
    if currency is None:
        return

    if not message.from_user:
        return

    args = message.text or ""
    # Remove the /command part to get the amount
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Некорректная сумма. Укажите целое число.")
        return

    amount = parse_amount(parts[1])
    if amount is None:
        await message.reply("Некорректная сумма. Укажите целое число.")
        return

    user = message.from_user
    async with async_session() as session:
        in_work_chat = await is_work_chat(message, session)

        # In group chat: only allow in the registered work chat
        if is_group(message) and not in_work_chat:
            return

        # Check access window for non-admins in work chat
        if in_work_chat and not is_admin(user):
            access_svc = AccessWindowService(session)
            if not await access_svc.is_access_open():
                await message.reply("Доступ на внесение операций сейчас закрыт.")
                return

        op_svc = OperationService(session)
        operation, new_balance = await op_svc.create_operation(
            telegram_user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            chat_id=message.chat.id,
            chat_type=message.chat.type,
            currency=currency,
            amount=amount,
        )

    formatted = format_amount(amount)

    # In group chat — short confirmation only
    if in_work_chat:
        await message.reply(f"✅ Запомнил. {formatted}")
    else:
        # Private chat (admin) — can show balance
        await message.reply(
            f"✅ Запомнил. {formatted}\n"
            f"{currency.emoji} Баланс: {format_amount(new_balance)} {currency.title.lower()}"
        )


def _register_currency_commands() -> None:
    for cur in CURRENCIES:
        cmd = cur.command

        async def handler(message: Message, _cmd: str = cmd) -> None:
            await _handle_currency_command(message, _cmd)

        router.message.register(handler, Command(cmd))


_register_currency_commands()
