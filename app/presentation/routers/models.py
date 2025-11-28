from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.common.security.dependencies import get_current_user
from app.core.services import ModelService
from app.dependencies import get_storage, get_db, get_redis
from app.infrastructure.database.repositories import ModelRepository, DatasetRepository
from app.presentation.schemas import ModelCreate, ModelRead
from app.core.enums import ModelStatus, ModelArchitectures
from app.core.entities import User as UserEntity

router = APIRouter(prefix="/models", tags=["models"])

# TODO: надо удалить обязательный профиль для архитектуры или хотя бы сделать его по енуму а не просто строкой
@router.post("/create", response_model=ModelRead, status_code=201)
async def create_model(
    name: str = Form(...),
    version: str = Form(...),
    architecture: ModelArchitectures = Form(...),
    architecture_profile: str = Form(...),
    dataset_id: Optional[UUID] = Form(None),
    status: ModelStatus = Form(ModelStatus.pending),
    file: UploadFile = File(...),
    current_user: UserEntity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage = Depends(get_storage),
    cache = Depends(get_redis)
):


    model_create = ModelCreate(
        name=name,
        version=version,
        architecture=architecture.value,
        architecture_profile=architecture_profile,
        dataset_id=dataset_id,
        status=status
    )

    service = ModelService(ModelRepository(db), storage, DatasetRepository(db), cache)
    try:
        file_data = await file.read()
        created = await service.create_model(
            model=model_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            current_user=current_user,
        )
        return created
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    finally:
        await file.close()


@router.get("/", response_model=list[ModelRead])
async def get_models(skip: int = 0,limit: int = 100,status: Optional[ModelStatus] = None,dataset_id: Optional[UUID] = None, include_system: bool = True, current_user: UserEntity = Depends(get_current_user), db: AsyncSession = Depends(get_db), storage=Depends(get_storage), cache = Depends(get_redis)):
    service = ModelService(ModelRepository(db), storage, DatasetRepository(db), cache)
    return await service.get_models(
        current_user=current_user,
        skip=skip,
        limit=limit,
        status=status,
        dataset_id=dataset_id,
        include_system=include_system
    )


@router.get("/{model_id}", response_model=ModelRead)
async def get_model(model_id: UUID, current_user: UserEntity = Depends(get_current_user), db: AsyncSession = Depends(get_db),storage=Depends(get_storage), cache = Depends(get_redis)):
    service = ModelService(ModelRepository(db), storage, DatasetRepository(db), cache)
    model = await service.get_model_by_id(model_id, current_user)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or access denied")
    return model


@router.delete("/{model_id}", status_code=204)
async def delete_model(model_id: UUID, current_user: UserEntity = Depends(get_current_user), db: AsyncSession = Depends(get_db), storage=Depends(get_storage), cache = Depends(get_redis),):
    service = ModelService(ModelRepository(db), storage, DatasetRepository(db), cache)
    try:
        await service.delete_model_by_id(model_id, current_user)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
