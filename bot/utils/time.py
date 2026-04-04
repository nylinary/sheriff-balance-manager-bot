from __future__ import annotations

from datetime import datetime

import zoneinfo

from bot.config import settings


def now() -> datetime:
    tz = zoneinfo.ZoneInfo(settings.timezone)
    return datetime.now(tz)
