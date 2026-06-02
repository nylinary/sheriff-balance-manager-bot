"""Pytest bootstrap: provide required env vars before bot.config.settings loads."""

import os

# Settings() requires BOT_TOKEN at import time; the rest have defaults.
os.environ.setdefault("BOT_TOKEN", "test-token")
