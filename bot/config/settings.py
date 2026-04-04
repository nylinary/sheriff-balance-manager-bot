from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    postgres_dsn: str = "postgresql+asyncpg://sheriff:sheriff@db:5432/sheriff"
    redis_dsn: str = "redis://redis:6379/0"

    admin_ids: list[int] = []
    timezone: str = "Europe/Moscow"
    work_chat_id: int | None = None

    # History pagination
    history_page_size: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()  # type: ignore[call-arg]
