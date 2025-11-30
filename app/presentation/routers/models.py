from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from uuid import UUID
from typing import Optional
from app.common.security.dependencies import get_current_user
from app.container import ApplicationContainer
from app.core.services import ModelService
from app.presentation.schemas import ModelCreate, ModelRead
from app.core.enums import ModelStatus, ModelArchitectures
from app.core.entities import User as UserEntity

router = APIRouter(prefix="/models", tags=["models"])

# TODO: надо удалить обязательный профиль для архитектуры или хотя бы сделать его по енуму а не просто строкой
@router.post("/create", response_model=ModelRead, status_code=201)
@inject
async def create_model(
    name: str = Form(...),
    version: str = Form(...),
    architecture: ModelArchitectures = Form(...),
    architecture_profile: str = Form(...),
    dataset_id: Optional[UUID] = Form(None),
    status: ModelStatus = Form(ModelStatus.pending),
    file: UploadFile = File(...),
    current_user: UserEntity = Depends(get_current_user),
    service: ModelService = Depends(Provide[ApplicationContainer.model_service]),
):
    model_create = ModelCreate(
        name=name,
        version=version,
        architecture=architecture.value,
        architecture_profile=architecture_profile,
        dataset_id=dataset_id,
        status=status
    )

    try:
        file_data = await file.read()
        created = await service.create_model(
            model=model_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            current_user=current_user,
        )
        return ModelRead.model_validate(created)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    finally:
        await file.close()


@router.get("/", response_model=list[ModelRead])
@inject
async def get_models(
        skip: int = 0,
        limit: int = 100,
        status: Optional[ModelStatus] = None,
        dataset_id: Optional[UUID] = None,
        include_system: bool = True,
        current_user: UserEntity = Depends(get_current_user),
        service: ModelService = Depends(Provide[ApplicationContainer.model_service]),
):
    models = await service.get_models(
        current_user=current_user,
        skip=skip,
        limit=limit,
        status=status,
        dataset_id=dataset_id,
        include_system=include_system
    )

    return [ModelRead.model_validate(model) for model in models]


@router.get("/{model_id}", response_model=ModelRead)
@inject
async def get_model(
        model_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        service: ModelService = Depends(Provide[ApplicationContainer.model_service]),
):
    model = await service.get_model_by_id(model_id, current_user)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or access denied")
    return ModelRead.model_validate(model)


@router.delete("/{model_id}", status_code=204)
@inject
async def delete_model(
        model_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        service: ModelService = Depends(Provide[ApplicationContainer.model_service]),
):
    try:
        await service.delete_model_by_id(model_id, current_user)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
