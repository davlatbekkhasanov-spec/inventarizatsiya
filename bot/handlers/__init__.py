from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.common import router as common_router
from bot.handlers.mesta import router as mesta_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(common_router)
    root.include_router(mesta_router)
    root.include_router(admin_router)
    return root
