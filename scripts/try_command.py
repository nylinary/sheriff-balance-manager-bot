#!/usr/bin/env python3
"""Parse a currency command locally and show the result — no DB, no Telegram, no prod.

Replicates exactly what bot/handlers/employee.py does: strips the /command, resolves
the currency, runs parse_amount_and_comment, and renders how the value + comment would
appear to the employee, in the admin chat, in the history card, and in the Excel export.

Usage:
    uv run python scripts/try_command.py "/руб 3200 оплата за такси"
    uv run python scripts/try_command.py /руб 1 000 крупная сумма
    uv run python scripts/try_command.py "/руб 100 <b>x</b> & y"   # HTML-escape demo
"""

from __future__ import annotations

import os
import sys

# Settings() needs BOT_TOKEN at import time; set a dummy so we never read the real .env value.
os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.config import CURRENCY_BY_COMMAND  # noqa: E402 — must come after env setup
from bot.models.operation import Operation, OperationType  # noqa: E402
from bot.services.notifications import _build_notification_text  # noqa: E402
from bot.utils import format_amount, parse_amount_and_comment  # noqa: E402
from bot.utils.time import now  # noqa: E402

INVALID_MSG = "Некорректная сумма. Укажите целое число."


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1

    # Accept either one quoted arg or several bare args.
    text = (argv[0] if len(argv) == 1 else " ".join(argv)).strip()
    print(f"Input: {text!r}\n")

    # Mirror the handler: parts = message.text.split(maxsplit=1)
    parts = text.split(maxsplit=1)
    cmd = parts[0].lstrip("/").split("@", 1)[0].lower()

    currency = CURRENCY_BY_COMMAND.get(cmd)
    if currency is None:
        known = ", ".join(f"/{c}" for c in CURRENCY_BY_COMMAND)
        print(f"⚠️  '/{cmd}' is not a currency command.\n    Known commands: {known}")
        return 1
    print(f"Command:  /{cmd}  →  {currency.emoji} {currency.title} (code={currency.code})")

    if len(parts) < 2:
        print(f"\nResult:   ❌ reply «{INVALID_MSG}»  (amount missing)")
        return 0

    args = parts[1]
    parsed = parse_amount_and_comment(args)
    if parsed is None:
        print(f"Args:     {args!r}")
        print(f"\nResult:   ❌ reply «{INVALID_MSG}»")
        return 0

    amount, comment = parsed
    op_type = OperationType.income if amount > 0 else OperationType.expense
    print(f"Args:     {args!r}")
    print(f"Amount:   {amount}   (formatted: {format_amount(amount)})")
    print(f"Comment:  {comment!r}")
    print(f"Type:     {op_type.value}")

    # Build an in-memory Operation (never added to a session) to render real outputs.
    op = Operation(
        operation_id=0,
        telegram_user_id=123456,
        username="test_user",
        full_name="Test User",
        chat_id=0,
        chat_type="group",
        currency_code=currency.code,
        currency_title=currency.title,
        currency_command=currency.command,
        amount=amount,
        operation_type=op_type,
        comment=comment,
    )
    op.created_at = now()

    print("\n--- Employee reply (work chat, plain text) ---")
    print(f"✅ Запомнил. {format_amount(amount)}")

    print("\n--- Admin chat notification (parse_mode=HTML) ---")
    print(_build_notification_text(op, op.created_at))

    print("\n--- History operation card line (plain text) ---")
    print(f"Комментарий: {op.comment}" if op.comment else "(no Комментарий line)")

    print("\n--- Excel 'Комментарий' cell ---")
    print(repr(op.comment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
