from aiogram import Router

from bot.handlers.access import router as access_router
from bot.handlers.admin import router as admin_router
from bot.handlers.employee import router as employee_router
from bot.handlers.history import router as history_router
from bot.handlers.wallet import router as wallet_router


def setup_routers() -> Router:
    root = Router()
    # Order matters: admin/history/wallet callbacks before employee commands
    root.include_router(admin_router)
    root.include_router(wallet_router)
    root.include_router(history_router)
    root.include_router(access_router)
    root.include_router(employee_router)
    return root
