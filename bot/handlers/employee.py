"""Handlers for currency operation commands (available in group chat)."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import CURRENCIES, CURRENCY_BY_COMMAND
from bot.handlers.common import is_admin, is_group, is_private, is_work_chat
from bot.models import async_session
from bot.services import OperationService
from bot.utils import format_amount, parse_amount

router = Router(name="employee")


def _revert_keyboard(operation_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Откатить",
                    callback_data=f"op:rev:{operation_id}",
                )
            ]
        ]
    )


async def _handle_currency_command(message: Message, command_text: str) -> None:
    currency = CURRENCY_BY_COMMAND.get(command_text)
    if currency is None:
        return

    if not message.from_user:
        return

    # Private chat — admin only
    if is_private(message) and not is_admin(message.from_user):
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
    kb = _revert_keyboard(operation.operation_id)

    # In group chat — short confirmation with revert button
    if in_work_chat:
        await message.reply(f"✅ Запомнил. {formatted}", reply_markup=kb)
    else:
        # Private chat (admin) — show balance + revert button
        await message.reply(
            f"✅ Запомнил. {formatted}\n"
            f"{currency.emoji} Баланс: {format_amount(new_balance)} {currency.title.lower()}",
            reply_markup=kb,
        )


def _register_currency_commands() -> None:
    for cur in CURRENCIES:
        cmd = cur.command

        async def handler(message: Message, _cmd: str = cmd) -> None:
            await _handle_currency_command(message, _cmd)

        router.message.register(handler, Command(cmd))


_register_currency_commands()
