from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.container import ApplicationContainer
from app.core.services import UserService
from app.dependencies import get_db
from app.presentation.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])

#TODO: Закрыть ручку и дать доступ только админам
# я вообще уже не помню зачем я делал этот роутер, наверно его тоже надо удалять
@router.get("/{user_id}", response_model=UserRead)
@inject
async def get_user(
        user_id: UUID,
        db: AsyncSession = Depends(get_db),
        service: UserService = Depends(Provide[ApplicationContainer.user_service ])
):
    user = await service.get_user_by_id(session=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)

