from __future__ import annotations

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    postgres_dsn: str = "postgresql+asyncpg://sheriff:sheriff@db:5432/sheriff"
    redis_dsn: str = "redis://redis:6379/0"

    admin_ids_raw: str = ""
    admin_usernames_raw: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_ids(self) -> list[int]:
        raw = self.admin_ids_raw.strip()
        return [int(x.strip()) for x in raw.split(",") if x.strip()] if raw else []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_usernames(self) -> list[str]:
        raw = self.admin_usernames_raw.strip()
        if not raw:
            return []
        return [u.strip().lstrip("@").lower() for u in raw.split(",") if u.strip()]

    timezone: str = "Europe/Moscow"

    # History pagination
    history_page_size: int = 5

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()  # type: ignore[call-arg]
