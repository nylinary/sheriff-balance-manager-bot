import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

import sqlalchemy

from bot.config import settings
from bot.handlers import setup_routers
from bot.models.base import engine, Base

import bot.models  # noqa: F401 — register all models

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            sqlalchemy.text("CREATE SEQUENCE IF NOT EXISTS operation_id_seq START 1")
        )
        # Add reverted_by columns if they don't exist yet
        for col, col_type in [
            ("reverted_by_telegram_id", "BIGINT"),
            ("reverted_by_username", "VARCHAR(255)"),
            ("reverted_by_full_name", "VARCHAR(512)"),
        ]:
            await conn.execute(
                sqlalchemy.text(
                    f"ALTER TABLE operations ADD COLUMN IF NOT EXISTS {col} {col_type}"
                )
            )
    logger.info("Database tables ensured.")


async def main() -> None:
    storage = RedisStorage.from_url(settings.redis_dsn)
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = Dispatcher(storage=storage)

    dp.startup.register(on_startup)

    root_router = setup_routers()
    dp.include_router(root_router)

    logger.info("Starting bot polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
