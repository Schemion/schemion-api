from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from uuid import UUID
from typing import Optional

from app.container import ApplicationContainer
from app.core.entities import User as UserEntity
from app.common.security.dependencies import get_current_user
from app.core.services import DatasetService
from app.presentation.schemas import DatasetCreate, DatasetRead

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/create", response_model=DatasetRead, status_code=201)
@inject
async def create_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    num_samples: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_user: UserEntity = Depends(get_current_user),
    service: DatasetService = Depends(Provide[ApplicationContainer.dataset_service])
):
    dataset_create = DatasetCreate(
        name=name,
        description=description,
        num_samples=num_samples or 0
    )

    #TODO: Валидация входящих файлов (вообще то должна быть в сервисе а не тут, но я почему то тут написал)

    try:
        file_data = await file.read()
        created = await service.create_dataset(
            dataset=dataset_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            current_user=current_user
        )
        file.file.close()
        return DatasetRead.model_validate(created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")
    finally:
        await file.close()


@router.get("/", response_model=list[DatasetRead])
@inject
async def get_datasets(
        skip: int = 0,
        limit: int = 100,
        name_contains: Optional[str] = None,
        current_user: UserEntity = Depends(get_current_user),
        service: DatasetService = Depends(Provide[ApplicationContainer.dataset_service])
):
    datasets = await service.get_datasets(current_user=current_user, skip=skip, limit=limit, name_contains=name_contains)
    return [DatasetRead.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetRead)
@inject
async def get_dataset(
        dataset_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        service: DatasetService = Depends(Provide[ApplicationContainer.dataset_service])
):
    dataset = await service.get_dataset_by_id(dataset_id, current_user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")
    return DatasetRead.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=204)
@inject
async def delete_dataset(
        dataset_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        service: DatasetService = Depends(Provide[ApplicationContainer.dataset_service])
):
    try:
        await service.delete_dataset_by_id(dataset_id, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))