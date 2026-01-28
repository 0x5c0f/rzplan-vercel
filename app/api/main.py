from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

# subsystem routers
from app.rz.subsystem.mcp import main
api_router.include_router(main.router)

# RZ module routers
from app.api.routes.rz import dict as dict_routes
api_router.include_router(dict_routes.router)