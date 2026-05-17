from uuid import UUID

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.enums import UserRoles
from app.core.services import UserService
from app.infrastructure.config import settings


def _normalize_admin_path(path: str | None) -> str:
    normalized = (path or "/admin").strip()
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    normalized = normalized.rstrip("/")
    return normalized or "/admin"


ADMIN_BASE_PATH = _normalize_admin_path(getattr(settings, "ADMIN_BASE_URL", "/admin"))


def _not_found_response() -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            return token

    try:
        return request.session.get("token")
    except AssertionError:
        return None


def _is_public_admin_path(path: str) -> bool:
    normalized = path.rstrip("/")
    if normalized == f"{ADMIN_BASE_PATH}/login":
        return True
    if normalized == f"{ADMIN_BASE_PATH}/statics":
        return True
    if path.startswith(f"{ADMIN_BASE_PATH}/statics/"):
        return True
    return False


class AdminGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path
        if path == ADMIN_BASE_PATH or path.startswith(f"{ADMIN_BASE_PATH}/"):
            if _is_public_admin_path(path):
                return await call_next(request)

            token = _extract_token(request)
            if not token:
                return _not_found_response()

            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
                user_id_raw = payload.get("sub")
                if not user_id_raw:
                    return _not_found_response()
                user_id = UUID(str(user_id_raw))
            except (JWTError, ValueError):
                return _not_found_response()

            container = request.app.state.dishka_container
            async with container() as con:
                user_service = await con.get(UserService)
                user = await user_service.get_user_by_id(user_id)
                role_names = [role.name for role in getattr(user, "roles", []) if getattr(role, "name", None)] if user else []

                if UserRoles.admin.value not in role_names:
                    return _not_found_response()

        return await call_next(request)
