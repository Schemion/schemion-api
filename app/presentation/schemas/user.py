import uuid
from pydantic import BaseModel, EmailStr, ConfigDict

from app.core.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.user


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
