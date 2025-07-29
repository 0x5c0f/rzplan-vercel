from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)


from app.api.routes.rz import (
    performance_data,
    performance_tracking_config,
    dify_chat_log,
    utils,
)

api_router.include_router(performance_tracking_config.router)
api_router.include_router(performance_data.router)

api_router.include_router(utils.router)

api_router.include_router(dify_chat_log.router)