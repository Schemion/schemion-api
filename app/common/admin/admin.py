from uuid import UUID

from fastapi import Depends
from jose import jwt, JWTError
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

from app.common.security import verify_password, create_access_token
from app.core.services import UserService
from app.dependencies import get_db
from app.infrastructure.database.repositories import UserRepository
from app.config import settings


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str = settings.JWT_SECRET):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form["email"], form["password"]

        db = next(get_db())

        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        user = user_service.get_user_by_email(email)

        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False

        token = create_access_token({"sub": str(user.id), "role": user.role})

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
            user_id = payload.get("sub")
            user_role = payload.get("role")
            if not user_id or not user_role:
                return False

            db = next(get_db())
            user_repo = UserRepository(db)
            user_service = UserService(user_repo)
            user = user_service.get_user_by_id(UUID(user_id))
            if not user:
                return False

            if user_role != "admin":
                return False
        except JWTError:
            return False

        return True
