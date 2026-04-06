"""Send notifications to admin users about employee operations."""

from __future__ import annotations

import logging
import zoneinfo
from datetime import datetime

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import CURRENCY_BY_CODE, settings
from bot.models.operation import Operation
from bot.utils import format_amount

logger = logging.getLogger(__name__)


def _build_notification_text(operation: Operation, dt: datetime) -> str:
    tz = zoneinfo.ZoneInfo(settings.timezone)
    local_dt = dt.astimezone(tz) if dt.tzinfo else dt
    date_str = local_dt.strftime("%d.%m.%Y %H:%M")

    cur = CURRENCY_BY_CODE.get(operation.currency_code)
    cur_emoji = cur.emoji if cur else ""
    cur_title = cur.title if cur else operation.currency_title

    user_display = operation.full_name or "—"
    if operation.username:
        user_display += f" (@{operation.username})"

    return (
        f"🔔 <b>Уведомление</b>\n\n"
        f"📅 {date_str}\n"
        f"👤 {user_display}\n"
        f"{cur_emoji} {cur_title}: <b>{format_amount(operation.amount)}</b>"
    )


def _notification_keyboard(operation_id: int) -> InlineKeyboardMarkup:
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


async def notify_admins_about_operation(
    bot: Bot,
    operation: Operation,
    exclude_user_id: int | None = None,
) -> None:
    """Send operation notification to all admins.

    exclude_user_id — skip this admin (e.g. if the admin made the operation themselves).
    """
    text = _build_notification_text(operation, operation.created_at)
    kb = _notification_keyboard(operation.operation_id)

    admin_ids = settings.admin_ids

    for admin_id in admin_ids:
        if admin_id == exclude_user_id:
            continue
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            logger.debug("Could not send notification to admin %s", admin_id)
