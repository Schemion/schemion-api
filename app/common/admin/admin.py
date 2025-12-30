from uuid import UUID

from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from jose import jwt, JWTError
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from app.common.security import create_access_token
from app.common.security.hashing import verify_password_async
from app.container import ApplicationContainer
from app.core.services import UserService
from app.config import settings
from app.dependencies import get_db_session


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str = settings.JWT_SECRET):
        super().__init__(secret_key=secret_key)

    @inject
    async def login(
            self,
            request: Request,
            user_service: UserService = Provide[ApplicationContainer.user_service]
    ) -> bool:
        form = await request.form()
        # В sqladmin ожидается username, но так как у нас его нет, то будет email но подпись останется username
        email, password = form["username"], form["password"]

        async with get_db_session() as session:
            user = await user_service.get_user_by_email(session, email)

            if not user:
                return False
            if not await verify_password_async(password, user.hashed_password):
                return False

            token = create_access_token({"sub": str(user.id), "role": user.role})

            request.session.update({"token": token})

            return True

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    @inject
    async def authenticate(
            self,
            request: Request,
            user_service: UserService = Provide[ApplicationContainer.user_service]
    ) -> Response | bool:
        token = request.session.get("token")
        if not token:
            return False

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            user_role = payload.get("role")
            if not user_id or not user_role:
                return False

            async with get_db_session() as session:
                user = await user_service.get_user_by_id(session, user_id)


                if not user:
                    return False

                if user_role != "admin":
                    return False
        except JWTError:
            return False

        return True
