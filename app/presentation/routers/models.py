from typing import Annotated, Optional
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette import status

from app.common.security.dependencies import get_current_user
from app.core.enums import ModelArchitectures
from app.core.services import ModelService
from app.presentation.schemas import ModelCreate, ModelRead

router = APIRouter(prefix="/models", tags=["models"], route_class=DishkaRoute)


# TODO: надо удалить обязательный профиль для архитектуры или хотя бы сделать его по енуму а не просто строкой
@router.post("/create", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
async def create_model(service: Annotated[ModelService, FromDishka()], name: str = Form(...),
                       architecture: ModelArchitectures = Form(...), architecture_profile: str = Form(...),
                       dataset_id: Optional[UUID] = Form(None), file: UploadFile = File(...),
                       current_user: dict = Depends(get_current_user)):
    model_create = ModelCreate(
        name=name,
        architecture=architecture.value,
        architecture_profile=architecture_profile,
        dataset_id=dataset_id,
    )

    try:
        file_data = await file.read()
        created = await service.create_model(
            model=model_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=UUID(current_user.get("id")),
        )
        return ModelRead.model_validate(created)
    finally:
        await file.close()


@router.get("/", response_model=list[ModelRead])
async def get_models(service: Annotated[ModelService, FromDishka()], skip: int = 0, limit: int = 100, dataset_id: Optional[UUID] = None,
                     include_system: bool = True, current_user: dict = Depends(get_current_user)):
    models = await service.get_models(
        user_id=UUID(current_user.get("id")),
        skip=skip,
        limit=limit,
        dataset_id=dataset_id,
        include_system=include_system,
    )

    return [ModelRead.model_validate(model) for model in models]


@router.get("/{model_id}", response_model=ModelRead)
async def get_model(service: Annotated[ModelService, FromDishka()], model_id: UUID,
                    current_user: dict = Depends(get_current_user)):
    model = await service.get_model_by_id(model_id, UUID(current_user.get("id")))
    return ModelRead.model_validate(model)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(service: Annotated[ModelService, FromDishka()], model_id: UUID,
                       current_user: dict = Depends(get_current_user)):
    await service.delete_model_by_id(model_id, UUID(current_user.get("id")))

@router.get("/download/{model_id}", response_model=dict)
async def download_model(service: Annotated[ModelService, FromDishka()], model_id: UUID,current_user: dict = Depends(get_current_user)):
    url = await service.download_model(model_id, UUID(current_user.get("id")))
    return {"download_url": url}
