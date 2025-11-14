from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.common.security import get_current_user
from app.core.services import UserService, DatasetService, ModelService
from app.dependencies import get_db, get_storage
from app.infrastructure.database.repositories import UserRepository, DatasetRepository, ModelRepository
from app.presentation.schemas import UserRead, DatasetRead, ModelRead
from app.core.entities import User as UserEntity

router = APIRouter(prefix="/users", tags=["users"])

#TODO: Закрыть ручку и дать доступ только админам
@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    service = UserService(UserRepository(db))
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: UserEntity = Depends(get_current_user),
):
    return current_user


@router.get("/{user_id}/datasets", response_model=list[DatasetRead])
def get_user_datasets(user_id: UUID, current_user: UserEntity = Depends(get_current_user), db: Session = Depends(get_db), storage=Depends(get_storage),):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(403, "Access denied")

    service = DatasetService(DatasetRepository(db), storage)
    return service.get_datasets(current_user=current_user, skip=0, limit=100, name_contains=None)


@router.get("/{user_id}/models", response_model=list[ModelRead])
def get_user_models(user_id: UUID, current_user: UserEntity = Depends(get_current_user), db: Session = Depends(get_db), storage=Depends(get_storage),):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(403, "Access denied")

    service = ModelService(ModelRepository(db), storage, DatasetRepository(db))
    return service.get_models(current_user=current_user,skip=0, limit=100, include_system=False )