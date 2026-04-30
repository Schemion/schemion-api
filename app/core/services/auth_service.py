from jwt import InvalidTokenError

from app.common.security import create_access_token, create_refresh_token, decode_token
from app.common.security.hashing import get_password_hash_async, verify_password_async
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.interfaces import IUserRepository
from app.presentation.schemas import LoginRequest, RefreshTokenRequest, Token, UserCreate


class AuthService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repo = user_repository

    async def register(self, user_create: UserCreate) -> Token:
        existing_user = await self.user_repo.get_user_by_email(str(user_create.email))
        if existing_user:
            raise ValidationError("Email already registered")

        hashed_pw = await get_password_hash_async(user_create.password)

        created_user = await self.user_repo.create_user(UserCreate(email=user_create.email, password=hashed_pw))
        new_user = await self.user_repo.get_user_by_email(str(user_create.email)) or created_user

        return self._create_token_pair(new_user)

    async def login(self, login: LoginRequest) -> Token:
        user = await self.user_repo.get_user_by_email(email=login.email)
        if not user:
            raise UnauthorizedError("Invalid email or password")

        if not await verify_password_async(login.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        return self._create_token_pair(user)

    async def refresh(self, refresh_request: RefreshTokenRequest) -> Token:
        try:
            payload = decode_token(refresh_request.refresh_token)
        except InvalidTokenError:
            raise UnauthorizedError("Invalid refresh token")

        if payload.get("type") != "refresh" or not payload.get("sub"):
            raise UnauthorizedError("Invalid refresh token")

        token_data = {
            "sub": payload["sub"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
        }

        return Token(access_token=create_access_token(token_data))

    def _create_token_pair(self, user) -> Token:
        roles = [role.name for role in user.roles] if getattr(user, "roles", None) else []

        permissions_names = set()
        for role in getattr(user, "roles", []) or []:
            for permission in role.permissions:
                permissions_names.add(permission.name)

        token_data = {"sub": str(user.id), "roles": roles, "permissions": list(permissions_names)}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return Token(access_token=access_token, refresh_token=refresh_token)
