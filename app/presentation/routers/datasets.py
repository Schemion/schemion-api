from dependency_injector.wiring import Provide, inject
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from uuid import UUID
from typing import Annotated, Optional
from app.common.security.dependencies import get_current_user
from app.core.services import DatasetService
from app.presentation.schemas import DatasetCreate, DatasetRead

router = APIRouter(prefix="/datasets", tags=["datasets"], route_class=DishkaRoute)


@router.post("/create", response_model=DatasetRead, status_code=201)
async def create_dataset(service: Annotated[DatasetService, FromDishka()], name: str = Form(...), description: Optional[str] = Form(None), num_samples: Optional[int] = Form(None), file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    dataset_create = DatasetCreate(
        name=name,
        description=description,
        num_samples=num_samples or 0
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")
    finally:
        await file.close()


@router.get("/", response_model=list[DatasetRead])
async def get_datasets(service: Annotated[DatasetService, FromDishka()], skip: int = 0, limit: int = 100,  name_contains: Optional[str] = None, current_user: dict = Depends(get_current_user),
):
    datasets = await service.get_datasets(user_id=UUID(current_user.get("id")), skip=skip, limit=limit, name_contains=name_contains)
    return [DatasetRead.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetRead)
async def get_dataset(service: Annotated[DatasetService, FromDishka()], dataset_id: UUID, current_user: dict = Depends(get_current_user)):
    dataset = await service.get_dataset_by_id(dataset_id, UUID(current_user.get("id")))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")
    return DatasetRead.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(service: Annotated[DatasetService, FromDishka()],  dataset_id: UUID, current_user: dict = Depends(get_current_user)):
    try:
        await service.delete_dataset_by_id(dataset_id, UUID(current_user.get("id")))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))