from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import CURRENCY_BY_CODE
from bot.models.operation import Operation
from bot.utils import format_amount


def _filter_suffix(username_filter: str | None) -> str:
    if username_filter:
        clean = username_filter.lstrip("@")
        return f":u:{clean}"
    return ":all"


def history_keyboard(
    operations: list[Operation],
    page: int,
    total_pages: int,
    username_filter: str | None = None,
) -> InlineKeyboardMarkup:
    suffix = _filter_suffix(username_filter)
    rows: list[list[InlineKeyboardButton]] = []

    for op in operations:
        cur = CURRENCY_BY_CODE.get(op.currency_code)
        cur_title = cur.title if cur else op.currency_title
        uname = f"@{op.username}" if op.username else str(op.telegram_user_id)
        label = f"#{op.operation_id} | {uname} | {format_amount(op.amount)} | {cur_title}"
        if op.is_reverted:
            label = f"↩️ {label}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"h:op:{op.operation_id}")])

    # Pagination row
    nav: list[InlineKeyboardButton] = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"h:p:{page - 1}{suffix}"))
    else:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data="h:noop"))

    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=f"h:goto{suffix}"))

    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"h:p:{page + 1}{suffix}"))
    else:
        nav.append(InlineKeyboardButton(text="➡️", callback_data="h:noop"))

    rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)
