"""Shared helpers for handlers."""
from __future__ import annotations

from aiogram.types import Message, User

from bot.config import settings


def is_admin(user: User | None) -> bool:
    if user is None:
        return False
    return user.id in settings.admin_ids


def is_private(message: Message) -> bool:
    return message.chat.type == "private"


def is_group(message: Message) -> bool:
    return message.chat.type in ("group", "supergroup")
