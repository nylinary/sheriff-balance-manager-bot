"""Admin-only handlers: revert, export."""

from __future__ import annotations

import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.handlers.common import is_admin, is_private
from bot.models import async_session
from bot.repositories import OperationRepo
from bot.services import OperationService
from bot.services.export_excel import build_excel
from bot.utils import format_amount

router = Router(name="admin")


# ── Revert via callback ──────────────────────────────────────────

_REV_RE = re.compile(r"^op:rev:(\d+)$")


@router.callback_query(lambda c: c.data and c.data.startswith("op:rev:"))
async def cb_revert(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user):
        await callback.answer("У вас нет доступа.", show_alert=True)
        return

    m = _REV_RE.match(callback.data or "")
    if not m:
        await callback.answer()
        return

    operation_id = int(m.group(1))
    user = callback.from_user

    async with async_session() as session:
        op_svc = OperationService(session)
        try:
            original, revert_op, new_balance = await op_svc.revert_operation(
                operation_id,
                admin_telegram_id=user.id,  # type: ignore[union-attr]
                admin_username=user.username if user else None,
                admin_full_name=user.full_name if user else None,
            )
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return

    text = (
        f"↩️ Операция #{operation_id} откатана.\n"
        f"Создана обратная операция #{revert_op.operation_id}: {format_amount(revert_op.amount)}\n"
        f"Новый баланс {original.currency_title}: {format_amount(new_balance)}"
    )
    await callback.message.answer(text)  # type: ignore[union-attr]
    await callback.answer()


# ── Excel export ──────────────────────────────────────────────────


@router.message(Command("выгрузка", "excel"))
async def cmd_export(message: Message) -> None:
    if not is_private(message) or not is_admin(message.from_user):
        if is_private(message):
            await message.reply("У вас нет доступа к этой команде.")
        return

    async with async_session() as session:
        repo = OperationRepo(session)
        operations = await repo.get_all()

    if not operations:
        await message.answer("История операций пуста.")
        return

    buf, filename = build_excel(operations)
    doc = BufferedInputFile(buf.read(), filename=filename)
    await message.answer_document(doc)
