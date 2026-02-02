from typing import Annotated

from dependency_injector.wiring import Provide, inject
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.core.services import UserService
from app.presentation.routers.tasks import FromDishka
from app.presentation.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"], route_class=DishkaRoute)

#TODO: Закрыть ручку и дать доступ только админам
# я вообще уже не помню зачем я делал этот роутер, наверно его тоже надо удалять
@router.get("/{user_id}", response_model=UserRead)
async def get_user( user_id: UUID,service: Annotated[UserService, FromDishka()]):
    user = await service.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)

