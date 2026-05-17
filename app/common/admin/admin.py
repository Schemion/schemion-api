from contextlib import asynccontextmanager
from uuid import UUID

from jose import JWTError, jwt
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import Response

from app.common.security import create_access_token
from app.common.security.hashing import verify_password_async
from app.core.enums import UserRoles
from app.core.services import UserService
from app.infrastructure.config import settings


def _extract_role_names(user) -> list[str]:
    return [role.name for role in getattr(user, "roles", []) if getattr(role, "name", None)]


@asynccontextmanager
async def _user_service_context(request: Request):
    request_container = getattr(getattr(request, "state", None), "dishka_container", None)
    if request_container is not None:
        yield await request_container.get(UserService)
        return

    container = request.app.state.dishka_container
    async with container() as con:
        yield await con.get(UserService)


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str = settings.JWT_SECRET):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        # В sqladmin ожидается username, но так как у нас его нет, то будет email но подпись останется username
        email = (form.get("username") or "").strip()
        password = form.get("password") or ""
        if not email or not password:
            return False

        async with _user_service_context(request) as user_service:
            user = await user_service.get_user_by_email(email)

            if not user:
                return False
            if not await verify_password_async(password, user.hashed_password):
                return False

            role_names = _extract_role_names(user)
            if UserRoles.admin.value not in role_names:
                return False

            token = create_access_token({"sub": str(user.id), "roles": role_names})
            request.session.update({"token": token})
            return True

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        token = request.session.get("token")
        if not token:
            return False

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id_raw = payload.get("sub")
            if not user_id_raw:
                return False
            user_id = UUID(str(user_id_raw))
        except (JWTError, ValueError):
            return False

        async with _user_service_context(request) as user_service:
            user = await user_service.get_user_by_id(user_id)

            if not user:
                return False

            role_names = _extract_role_names(user)
            if UserRoles.admin.value not in role_names:
                return False

        return True
