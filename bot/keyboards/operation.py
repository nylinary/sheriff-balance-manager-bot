from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def operation_card_keyboard(
    operation_id: int,
    is_reverted: bool,
    *,
    is_admin_user: bool = False,
) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    if not is_reverted and is_admin_user:
        buttons.append(
            InlineKeyboardButton(
                text="🔄 Откатить", callback_data=f"op:rev:{operation_id}"
            )
        )
    if is_admin_user:
        buttons.append(InlineKeyboardButton(text="💰 Кошелек", callback_data="w:show"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
