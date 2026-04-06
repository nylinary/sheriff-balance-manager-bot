"""Admin-only handlers: revert (admin or owner), export."""

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


# ── Revert via callback (admin or operation owner) ───────────────

_REV_RE = re.compile(r"^op:rev:(\d+)$")


@router.callback_query(lambda c: c.data and c.data.startswith("op:rev:"))
async def cb_revert(callback: CallbackQuery) -> None:
    user = callback.from_user
    if not user:
        await callback.answer()
        return

    m = _REV_RE.match(callback.data or "")
    if not m:
        await callback.answer()
        return

    operation_id = int(m.group(1))
    admin = is_admin(user)

    async with async_session() as session:
        op_svc = OperationService(session)
        try:
            original, revert_op, new_balance = await op_svc.revert_operation(
                operation_id,
                reverted_by_telegram_id=user.id,
                reverted_by_username=user.username,
                reverted_by_full_name=user.full_name,
                is_admin_user=admin,
            )
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return

    text = (
        f"↩️ Операция #{operation_id} откатана.\n"
        f"Создана обратная операция #{revert_op.operation_id}: "
        f"{format_amount(revert_op.amount)}"
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
