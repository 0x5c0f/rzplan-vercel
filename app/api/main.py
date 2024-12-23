from fastapi import APIRouter

from app.api.routes import items, login, users, utils

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])


from app.api.routes.rz import performance_data, performance_tracking_config, notification

api_router.include_router(performance_tracking_config.router)
api_router.include_router(performance_data.router)

api_router.include_router(notification.router)