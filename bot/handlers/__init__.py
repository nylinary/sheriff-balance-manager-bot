from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.chat_manage import router as chat_manage_router
from bot.handlers.common import router as common_router
from bot.handlers.employee import router as employee_router
from bot.handlers.history import router as history_router
from bot.handlers.wallet import router as wallet_router


def setup_routers() -> Router:
    root = Router()
    # /start first
    root.include_router(common_router)
    # chat_manage — handles bot join/leave events
    root.include_router(chat_manage_router)
    # Admin/history/wallet callbacks before employee commands
    root.include_router(admin_router)
    root.include_router(wallet_router)
    root.include_router(history_router)
    root.include_router(employee_router)
    return root
