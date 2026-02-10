from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from app.core.services.auth_service import AuthService
from app.presentation import schemas
from app.presentation.schemas import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


@router.post("/login", response_model=Token)
async def login(login_schema: LoginRequest, service: Annotated[AuthService, FromDishka()]):
    return await service.login(login_schema)


@router.post("/register", response_model=schemas.UserRead)
async def create_user(user: schemas.UserCreate, service: Annotated[AuthService, FromDishka()]):
    return await service.register(user)
