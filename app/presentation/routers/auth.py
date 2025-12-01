from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.container import ApplicationContainer
from app.presentation import schemas
from app.dependencies import get_db
from app.common import security
from app.config import settings
from app.core.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schemas.Token)
@inject
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(Provide[ApplicationContainer.user_service])
):

    user = await service.get_user_by_email(db,form_data.username)
    # O2Auth тоже ждет username но ему особо пофиг, поэтому в форме у нас username а по факту email
    if not user or not await security.verify_password_async(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "email": user.email
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.UserRead)
@inject
async def create_user(
        user: schemas.UserCreate,
        db: AsyncSession = Depends(get_db),
        service: UserService = Depends(Provide[ApplicationContainer.user_service])
):
    db_user = await service.get_user_by_email(db, str(user.email))
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await service.create_user(db, user)