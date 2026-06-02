from __future__ import annotations

import re
from datetime import time


def parse_amount(text: str) -> int | None:
    text = text.strip().replace(" ", "")
    try:
        value = int(text)
    except ValueError:
        return None
    if value == 0:
        return None
    return value


# Leading amount (optionally space-grouped thousands, optional sign) + optional comment.
_AMOUNT_COMMENT_RE = re.compile(
    r"^\s*([+-]?\d{1,3}(?: \d{3})+|[+-]?\d+)(?:\s+(.*))?$", re.DOTALL
)
_MAX_COMMENT_LEN = 500  # must match the operations.comment column length


def parse_amount_and_comment(text: str | None) -> tuple[int, str | None] | None:
    """Parse '<amount> <optional comment>' from command args.

    Returns (amount, comment) or None if the amount is invalid.
    - Supports space-grouped thousands ("1 000" -> 1000) and a leading +/- sign.
    - Rejects zero.
    - comment is None when absent/blank; otherwise trimmed and capped at _MAX_COMMENT_LEN.
    """
    if not text or not text.strip():
        return None
    m = _AMOUNT_COMMENT_RE.match(text.strip())
    if not m:
        return None
    try:
        value = int(m.group(1).replace(" ", ""))
    except ValueError:
        return None
    if value == 0:
        return None
    comment = (m.group(2) or "").strip()
    if len(comment) > _MAX_COMMENT_LEN:
        comment = comment[:_MAX_COMMENT_LEN].rstrip()
    return value, (comment or None)


_TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})\s*-\s*(\d{1,2})[:.](\d{2})$")


def parse_time_range(text: str) -> tuple[time, time] | None:
    cleaned = text.strip().replace("\u2013", "-").replace("\u2014", "-")
    m = _TIME_RE.match(cleaned)
    if not m:
        return None
    try:
        t_from = time(int(m.group(1)), int(m.group(2)))
        t_to = time(int(m.group(3)), int(m.group(4)))
    except ValueError:
        return None
    return t_from, t_to
