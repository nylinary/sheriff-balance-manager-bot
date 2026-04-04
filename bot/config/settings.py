from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    postgres_dsn: str = "postgresql+asyncpg://sheriff:sheriff@db:5432/sheriff"
    redis_dsn: str = "redis://redis:6379/0"

    admin_ids: list[int] = []
    admin_usernames: list[str] = []

    @field_validator("admin_usernames", mode="after")
    @classmethod
    def _normalize_usernames(cls, v: list[str]) -> list[str]:
        return [u.lstrip("@").lower() for u in v]

    timezone: str = "Europe/Moscow"

    # History pagination
    history_page_size: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()  # type: ignore[call-arg]
