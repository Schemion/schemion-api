from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RegistrationCodeSent(BaseModel):
    detail: str


class RegistrationConfirmRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")
