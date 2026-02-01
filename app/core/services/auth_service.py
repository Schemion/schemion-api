from app.common.security import create_access_token, verify_password
from app.common.security.hashing import get_password_hash_async, verify_password_async
from app.core.interfaces import IUserRepository
from app.presentation.schemas import LoginRequest, Token, UserCreate, UserRead



class AuthService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repo = user_repository

    async def register(self, user_create: UserCreate) -> UserRead:
        existing_user = await self.user_repo.get_user_by_email(str(user_create.email))
        if existing_user:
            raise ValueError("Email already registered")

        hashed_pw = await get_password_hash_async(user_create.password)

        new_user = await self.user_repo.create_user(UserCreate(email=user_create.email, password=hashed_pw))

        return UserRead.model_validate(new_user)

    async def login(self, login: LoginRequest):
        user = await self.user_repo.get_user_by_email(email=login.email)
        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password_async(login.password, user.hashed_password):
            raise ValueError("Invalid email or password")


        roles = [role.name for role in user.roles] if user.roles else []

        permissions_names = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions_names.add(permission.name)

        token_data = {"sub": str(user.id), "roles": roles, "permissions": list(permissions_names)}
        access_token = create_access_token(token_data)
        return Token(access_token=access_token)