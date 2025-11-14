from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.common.security.dependencies import get_current_user
from app.core.services import ModelService
from app.dependencies import get_storage, get_db
from app.infrastructure.database.repositories import ModelRepository, DatasetRepository
from app.presentation.schemas import ModelCreate, ModelRead
from app.core.enums import ModelStatus, ModelArchitectures
from app.core.entities import User as UserEntity

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/create", response_model=ModelRead, status_code=201)
async def create_model(
    name: str = Form(...),
    version: str = Form(...),
    architecture: ModelArchitectures = Form(...),
    dataset_id: Optional[UUID] = Form(None),
    base_model_id: Optional[UUID] = Form(None),  # Для fine-tuning
    status: ModelStatus = Form(ModelStatus.pending),
    file: UploadFile = File(...),
    current_user: UserEntity = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage = Depends(get_storage),
):
    if base_model_id is None and dataset_id is None:
        raise HTTPException(400, "Must specify either dataset_id (new training) or base_model_id (fine-tuning)")

    model_create = ModelCreate(
        name=name,
        version=version,
        architecture=architecture.value,
        dataset_id=dataset_id,
        base_model_id=base_model_id,
        status=status
    )

    service = ModelService(ModelRepository(db), storage, DatasetRepository(db))
    try:
        file_data = await file.read()
        created = service.create_model(
            model=model_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            current_user=current_user,
            is_fine_tune=bool(base_model_id)
        )
        return created
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    finally:
        await file.close()


@router.get("/", response_model=list[ModelRead])
def get_models(skip: int = 0,limit: int = 100,status: Optional[ModelStatus] = None,dataset_id: Optional[UUID] = None, include_system: bool = True, current_user: UserEntity = Depends(get_current_user), db: Session = Depends(get_db), storage=Depends(get_storage)):
    service = ModelService(ModelRepository(db), storage, DatasetRepository(db))
    return service.get_models(
        current_user=current_user,
        skip=skip,
        limit=limit,
        status=status,
        dataset_id=dataset_id,
        include_system=include_system
    )


@router.get("/{model_id}", response_model=ModelRead)
def get_model(model_id: UUID, current_user: UserEntity = Depends(get_current_user), db: Session = Depends(get_db),storage=Depends(get_storage)):
    service = ModelService(ModelRepository(db), storage, DatasetRepository(db))
    model = service.get_model_by_id(model_id, current_user)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or access denied")
    return model


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: UUID, current_user: UserEntity = Depends(get_current_user), db: Session = Depends(get_db), storage=Depends(get_storage)):
    service = ModelService(ModelRepository(db), storage, DatasetRepository(db))
    try:
        service.delete_model_by_id(model_id, current_user)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
