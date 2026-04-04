"""History browsing with inline pagination — admin only, private chat."""

from __future__ import annotations

import re
import zoneinfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import CURRENCY_BY_CODE, settings
from bot.handlers.common import is_admin, is_private
from bot.keyboards import history_keyboard, operation_card_keyboard
from bot.models import async_session
from bot.services import HistoryService
from bot.utils import format_amount

router = Router(name="history")


class PageInputState(StatesGroup):
    waiting_page = State()


# ── /история ──────────────────────────────────────────────────────


@router.message(Command("история"))
async def cmd_history(message: Message, state: FSMContext) -> None:
    if not is_private(message) or not is_admin(message.from_user):
        if is_private(message):
            await message.reply("У вас нет доступа к этой команде.")
        return

    await state.clear()

    args = (message.text or "").split(maxsplit=1)
    username_filter = args[1].strip() if len(args) > 1 else None

    async with async_session() as session:
        svc = HistoryService(session)
        operations, page, total_pages = await svc.get_page(1, username_filter)

    if not operations:
        if username_filter:
            await message.answer("Операции по указанному пользователю не найдены.")
        else:
            await message.answer("История операций пуста.")
        return

    kb = history_keyboard(operations, page, total_pages, username_filter)
    await message.answer("📋 История операций:", reply_markup=kb)


# ── Pagination callbacks ──────────────────────────────────────────

_PAGE_RE = re.compile(r"^h:p:(\d+):(all|u:(.+))$")


@router.callback_query(lambda c: c.data and c.data.startswith("h:p:"))
async def cb_history_page(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user):
        await callback.answer("У вас нет доступа.", show_alert=True)
        return

    m = _PAGE_RE.match(callback.data or "")
    if not m:
        await callback.answer()
        return

    page = int(m.group(1))
    username_filter = m.group(3)  # None if "all"

    async with async_session() as session:
        svc = HistoryService(session)
        operations, page, total_pages = await svc.get_page(page, username_filter)

    if not operations:
        await callback.answer("Нет операций.", show_alert=True)
        return

    kb = history_keyboard(operations, page, total_pages, username_filter)
    await callback.message.edit_reply_markup(reply_markup=kb)  # type: ignore[union-attr]
    await callback.answer()


# ── Goto page (FSM) ──────────────────────────────────────────────

_GOTO_RE = re.compile(r"^h:goto:(all|u:(.+))$")


@router.callback_query(lambda c: c.data and c.data.startswith("h:goto"))
async def cb_goto_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user):
        await callback.answer("У вас нет доступа.", show_alert=True)
        return

    m = _GOTO_RE.match(callback.data or "")
    username_filter = m.group(2) if m else None

    await state.set_state(PageInputState.waiting_page)
    await state.update_data(username_filter=username_filter)
    await callback.message.answer("Введите номер страницы:")  # type: ignore[union-attr]
    await callback.answer()


@router.message(PageInputState.waiting_page)
async def on_page_number(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    username_filter = data.get("username_filter")

    text = (message.text or "").strip()
    if not text.isdigit():
        await message.reply("Некорректный номер страницы.")
        await state.clear()
        return

    page = int(text)

    async with async_session() as session:
        svc = HistoryService(session)
        operations, page, total_pages = await svc.get_page(page, username_filter)

    await state.clear()

    if not operations:
        await message.answer("Нет операций.")
        return

    kb = history_keyboard(operations, page, total_pages, username_filter)
    await message.answer("📋 История операций:", reply_markup=kb)


# ── Open operation card ──────────────────────────────────────────

_OP_RE = re.compile(r"^h:op:(\d+)$")


@router.callback_query(lambda c: c.data and c.data.startswith("h:op:"))
async def cb_open_operation(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user):
        await callback.answer("У вас нет доступа.", show_alert=True)
        return

    m = _OP_RE.match(callback.data or "")
    if not m:
        await callback.answer()
        return

    operation_id = int(m.group(1))

    async with async_session() as session:
        svc = HistoryService(session)
        op = await svc.get_operation(operation_id)

    if op is None:
        await callback.answer("Операция не найдена.", show_alert=True)
        return

    tz = zoneinfo.ZoneInfo(settings.timezone)
    created = op.created_at
    if created and created.tzinfo:
        created = created.astimezone(tz)
    date_str = created.strftime("%d.%m.%Y %H:%M") if created else "—"

    cur = CURRENCY_BY_CODE.get(op.currency_code)
    cur_title = cur.title if cur else op.currency_title

    status = "откатана" if op.is_reverted else "активна"
    uname = f"@{op.username}" if op.username else "—"

    text = (
        f"ID операции: {op.operation_id}\n"
        f"Дата: {date_str}\n"
        f"Пользователь: {uname}\n"
        f"Имя: {op.full_name or '—'}\n"
        f"Telegram ID: {op.telegram_user_id}\n"
        f"Валюта: {cur_title}\n"
        f"Сумма: {format_amount(op.amount)}\n"
        f"Тип: {op.operation_type.value}\n"
        f"Chat ID: {op.chat_id}\n"
        f"Статус: {status}"
    )

    kb = operation_card_keyboard(op.operation_id, op.is_reverted)
    await callback.message.answer(text, reply_markup=kb)  # type: ignore[union-attr]
    await callback.answer()


# ── Noop callback ─────────────────────────────────────────────────


@router.callback_query(lambda c: c.data == "h:noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()
