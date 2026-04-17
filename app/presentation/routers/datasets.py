from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import asyncio

from app.common.security.dependencies import get_current_user
from app.core.services import DatasetService
from app.presentation.schemas import DatasetCreate, DatasetCreateRequest, DatasetListRequest, DatasetRead

router = APIRouter(prefix="/datasets", tags=["datasets"], route_class=DishkaRoute)


@router.post("/create", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def create_dataset(service: Annotated[DatasetService, FromDishka()],
                         payload: Annotated[DatasetCreateRequest, Depends(DatasetCreateRequest.as_form)],
                         file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    dataset_create = DatasetCreate(
        name=payload.name,
        description=payload.description,
    )
    try:
        file_data = await asyncio.wait_for(file.read(), timeout=10)
        created = await service.create_dataset(
            dataset=dataset_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=UUID(current_user.get("id"))
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="File read operation timed out")
    finally:
        await file.close()
    return DatasetRead.model_validate(created)


@router.get("/", response_model=list[DatasetRead])
async def get_datasets(service: Annotated[DatasetService, FromDishka()],
                       params: Annotated[DatasetListRequest, Depends()],
                       current_user: dict = Depends(get_current_user),
                       ):
    datasets = await service.get_datasets(user_id=UUID(current_user.get("id")), skip=params.skip, limit=params.limit,
                                          name_contains=params.name_contains)
    return [DatasetRead.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetRead)
async def get_dataset(service: Annotated[DatasetService, FromDishka()], dataset_id: UUID,
                      current_user: dict = Depends(get_current_user)):
    dataset = await service.get_dataset_by_id(dataset_id, UUID(current_user.get("id")))
    return DatasetRead.model_validate(dataset)

@router.get("/download/{dataset_id}", response_model=dict)
async def download_dataset(service: Annotated[DatasetService, FromDishka()], dataset_id: UUID,current_user: dict = Depends(get_current_user)):
    url = await service.download_dataset(dataset_id, UUID(current_user.get("id")))
    return {"download_url": url}

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(service: Annotated[DatasetService, FromDishka()], dataset_id: UUID,
                         current_user: dict = Depends(get_current_user)):
    await service.delete_dataset_by_id(dataset_id, UUID(current_user.get("id")))
