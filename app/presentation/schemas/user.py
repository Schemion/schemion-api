import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.enums import UserRoles


class UserBase(BaseModel):
    email: EmailStr
    role: UserRoles = UserRoles.user


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
