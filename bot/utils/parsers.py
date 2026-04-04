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


_TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})\s*-\s*(\d{1,2})[:.](\d{2})$")


def parse_time_range(text: str) -> tuple[time, time] | None:
    m = _TIME_RE.match(text.strip())
    if not m:
        return None
    try:
        t_from = time(int(m.group(1)), int(m.group(2)))
        t_to = time(int(m.group(3)), int(m.group(4)))
    except ValueError:
        return None
    return t_from, t_to
