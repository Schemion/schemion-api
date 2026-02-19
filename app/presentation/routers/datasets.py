from typing import Annotated, Optional
from uuid import UUID

from alembic.util import status
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.common.security.dependencies import get_current_user
from app.core.services import DatasetService
from app.presentation.schemas import DatasetCreate, DatasetRead

router = APIRouter(prefix="/datasets", tags=["datasets"], route_class=DishkaRoute)


@router.post("/create", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def create_dataset(service: Annotated[DatasetService, FromDishka()], name: str = Form(...),
                         description: Optional[str] = Form(None),
                         file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    dataset_create = DatasetCreate(
        name=name,
        description=description,
    )
    try:
        file_data = await file.read()
        created = await service.create_dataset(
            dataset=dataset_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=UUID(current_user.get("id"))
        )
        file.file.close()
        return DatasetRead.model_validate(created)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process dataset: {str(e)}")
    finally:
        await file.close()


@router.get("/", response_model=list[DatasetRead])
async def get_datasets(service: Annotated[DatasetService, FromDishka()], skip: int = 0, limit: int = 100,
                       name_contains: Optional[str] = None, current_user: dict = Depends(get_current_user),
                       ):
    datasets = await service.get_datasets(user_id=UUID(current_user.get("id")), skip=skip, limit=limit,
                                          name_contains=name_contains)
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
