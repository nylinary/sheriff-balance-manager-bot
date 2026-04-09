"""Handlers for currency operation commands (available in group chat)."""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import CURRENCIES, CURRENCY_BY_COMMAND
from bot.handlers.common import (
    is_admin,
    is_admin_chat,
    is_group,
    is_private,
    is_work_chat,
)
from bot.models import async_session
from bot.services import OperationService
from bot.services.notifications import notify_admins_about_operation
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


async def _handle_currency_command(
    message: Message, command_text: str, bot: Bot
) -> None:
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
    admin = is_admin(user)
    async with async_session() as session:
        in_work_chat = await is_work_chat(message, session)
        in_admin_chat = await is_admin_chat(message, session)

        # In group chat: only allow in work chat or admin chat
        if is_group(message) and not in_work_chat and not in_admin_chat:
            return

        # Admin chat — only admins can use commands
        if in_admin_chat and not admin:
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

    if in_work_chat:
        # Work chat — short confirmation + notify admins (private + admin chat)
        await message.reply(f"✅ Запомнил. {formatted}", reply_markup=kb)
        async with async_session() as notify_session:
            await notify_admins_about_operation(
                bot,
                operation,
                notify_session,
                exclude_user_id=user.id if admin else None,
            )
    else:
        # Private chat or admin chat — show balance + revert button + notify
        await message.reply(
            f"✅ Запомнил. {formatted}\n"
            f"{currency.emoji} Баланс: {format_amount(new_balance)} {currency.title.lower()}",
            reply_markup=kb,
        )
        async with async_session() as notify_session:
            await notify_admins_about_operation(
                bot,
                operation,
                notify_session,
                exclude_user_id=user.id,
                exclude_chat_id=message.chat.id if in_admin_chat else None,
            )


def _register_currency_commands() -> None:
    for cur in CURRENCIES:
        cmd = cur.command

        async def handler(message: Message, bot: Bot, _cmd: str = cmd) -> None:
            await _handle_currency_command(message, _cmd, bot)

        router.message.register(handler, Command(cmd, ignore_case=True))


_register_currency_commands()
