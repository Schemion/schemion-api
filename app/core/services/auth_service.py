import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from jwt import InvalidTokenError

from app.common.security import create_access_token, create_refresh_token, decode_token
from app.common.security.hashing import get_password_hash_async, verify_password_async
from app.core.exceptions import MailDeliveryError, ServiceUnavailableError, UnauthorizedError, ValidationError
from app.core.interfaces import IMailService, IRegistrationConfirmationRepository, IUserRepository
from app.infrastructure.config import settings
from app.presentation.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegistrationCodeSent,
    RegistrationConfirmRequest,
    Token,
    UserCreate,
)


class AuthService:
    def __init__(
            self,
            user_repository: IUserRepository,
            confirmation_repository: IRegistrationConfirmationRepository,
            mail_service: IMailService,
    ):
        self.user_repo = user_repository
        self.confirmation_repo = confirmation_repository
        self.mail_service = mail_service

    async def register(self, user_create: UserCreate) -> RegistrationCodeSent:
        existing_user = await self.user_repo.get_user_by_email(str(user_create.email))
        if existing_user:
            raise ValidationError("Email already registered")

        hashed_pw = await get_password_hash_async(user_create.password)
        email = str(user_create.email)
        code = self._generate_confirmation_code()
        code_hash = self._hash_confirmation_code(email, code)

        await self.confirmation_repo.upsert_confirmation(
            email=email,
            hashed_password=hashed_pw,
            code_hash=code_hash,
            expires_at=self._confirmation_expires_at(),
        )

        try:
            await self.mail_service.send_registration_confirmation(email, code)
        except MailDeliveryError:
            await self.confirmation_repo.delete_by_email(email)
            raise ServiceUnavailableError("Could not send registration confirmation email")

        return RegistrationCodeSent(detail="Registration confirmation code sent")

    async def confirm_registration(self, confirm_request: RegistrationConfirmRequest) -> Token:
        email = str(confirm_request.email)
        existing_user = await self.user_repo.get_user_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        confirmation = await self.confirmation_repo.get_by_email(email)
        if not confirmation:
            raise ValidationError("Registration confirmation code was not requested")

        if self._is_confirmation_expired(confirmation.expires_at):
            await self.confirmation_repo.delete_by_email(email)
            raise ValidationError("Registration confirmation code expired")

        if confirmation.attempts >= settings.REGISTRATION_CODE_MAX_ATTEMPTS:
            await self.confirmation_repo.delete_by_email(email)
            raise ValidationError("Too many confirmation attempts")

        expected_code_hash = self._hash_confirmation_code(email, confirm_request.code)
        if not hmac.compare_digest(confirmation.code_hash, expected_code_hash):
            attempts = await self.confirmation_repo.increment_attempts(email)
            if attempts >= settings.REGISTRATION_CODE_MAX_ATTEMPTS:
                await self.confirmation_repo.delete_by_email(email)
                raise ValidationError("Too many confirmation attempts")
            raise ValidationError("Invalid registration confirmation code")

        created_user = await self.user_repo.create_user(
            UserCreate(email=confirm_request.email, password=confirmation.hashed_password)
        )
        await self.confirmation_repo.delete_by_email(email)
        new_user = await self.user_repo.get_user_by_email(email) or created_user

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

    def _generate_confirmation_code(self) -> str:
        code_length = settings.REGISTRATION_CODE_LENGTH
        return f"{secrets.randbelow(10 ** code_length):0{code_length}d}"

    def _hash_confirmation_code(self, email: str, code: str) -> str:
        message = f"{email.lower()}:{code}".encode("utf-8")
        secret = settings.JWT_SECRET.encode("utf-8")
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    def _confirmation_expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=settings.REGISTRATION_CODE_TTL_SECONDS)

    def _is_confirmation_expired(self, expires_at: datetime) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return expires_at <= datetime.now(timezone.utc)
