from __future__ import annotations

import io

import zoneinfo
from openpyxl import Workbook

from bot.config import settings
from bot.models.operation import Operation
from bot.utils.time import now

COLUMNS = [
    "ID",
    "№ операции",
    "Дата",
    "Код валюты",
    "Валюта",
    "Сумма",
    "Знак",
    "Тип операции",
    "Telegram ID",
    "Имя пользователя",
    "Полное имя",
    "ID чата",
    "Тип чата",
    "Откатана",
    "ID отката",
    "ID родительской операции",
    "Роль",
    "Откатил (Telegram ID)",
    "Откатил (username)",
    "Откатил (имя)",
]


def build_excel(operations: list[Operation]) -> tuple[io.BytesIO, str]:
    tz = zoneinfo.ZoneInfo(settings.timezone)
    wb = Workbook()
    ws = wb.active
    ws.title = "Операции"  # type: ignore[union-attr]

    ws.append(COLUMNS)  # type: ignore[union-attr]

    for op in operations:
        created = op.created_at
        if created and created.tzinfo:
            created = created.astimezone(tz)
        ws.append(
            [  # type: ignore[union-attr]
                op.id,
                op.operation_id,
                created.strftime("%d.%m.%Y %H:%M") if created else "",
                op.currency_code,
                op.currency_title,
                op.amount,
                "+" if op.amount >= 0 else "-",
                op.operation_type.value if op.operation_type else "",
                op.telegram_user_id,
                op.username,
                op.full_name,
                op.chat_id,
                op.chat_type,
                op.is_reverted,
                op.reverted_operation_id,
                op.revert_parent_operation_id,
                op.role_snapshot,
                op.reverted_by_telegram_id,
                op.reverted_by_username,
                op.reverted_by_full_name,
            ]
        )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    ts = now().strftime("%Y-%m-%d_%H-%M")
    filename = f"operations_{ts}.xlsx"
    return buf, filename
