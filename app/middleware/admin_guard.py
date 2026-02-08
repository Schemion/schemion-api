from uuid import UUID

from fastapi import Request
from jose import JWTError, jwt
from sqlalchemy.sql.annotation import Annotated
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.enums import UserRoles
from app.core.services import UserService
from app.dependencies import get_db_session
from app.infrastructure.config import settings
from app.presentation.routers.tasks import FromDishka


# TODO: избавится от контекстного менеджера сессий по возможности
# Нужно чтобы прятать от случайных юзеров сам факт наличия админ панели
class AdminGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
            self,
            request: Request,
            call_next: RequestResponseEndpoint,
            user_service: UserService = Annotated[UserService, FromDishka()],
    ):
        if request.url.path.startswith("/admin"):
            token = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

            if not token:
                return JSONResponse(status_code=404, content={"detail": "Not Found"})

            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
                user_id = payload.get("sub")
                if not user_id:
                    return JSONResponse(status_code=404, content={"detail": "Not Found"})

                async with get_db_session() as session:
                    user = await user_service.get_user_by_id(UUID(user_id))

                    if not user or user.role != UserRoles.admin.value:
                        return JSONResponse(status_code=404, content={"detail": "Not Found"})

            except JWTError:
                return JSONResponse(status_code=404, content={"detail": "Not Found"})

        response = await call_next(request)
        return response
