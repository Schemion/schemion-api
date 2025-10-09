from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.common.security.dependencies import require_roles
from app.core.entities import User
from app.core.services import ModelService
from app.dependencies import get_storage, get_db
from app.infrastructure.database.repositories import ModelRepository
from app.presentation.schemas import ModelCreate, ModelRead
from app.core.enums import ModelStatus

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/create", response_model=ModelRead, status_code=201)
def create_model(name: str = Form(...),version: str = Form(...), dataset_id: Optional[UUID] = Form(None),status: ModelStatus = Form(ModelStatus.pending),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        storage=Depends(get_storage),
        _: User = Depends(require_roles(["admin"]))
):
    model_create = ModelCreate(
        name=name,
        version=version,
        dataset_id=dataset_id,
        status=status
    )

    service = ModelService(ModelRepository(db), storage)
    try:
        file_data = file.file.read()
        created = service.create_model(
            model=model_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload model")


@router.get("/", response_model=list[ModelRead])
def get_models(skip: int = 0,limit: int = 100,status: Optional[ModelStatus] = None,dataset_id: Optional[UUID] = None,db: Session = Depends(get_db)):
    service = ModelService(ModelRepository(db), Depends(get_storage))
    return service.get_models(skip, limit, status, dataset_id)


@router.get("/{model_id}", response_model=ModelRead)
def get_model(model_id: UUID, db: Session = Depends(get_db)):
    service = ModelService(ModelRepository(db), Depends(get_storage))
    model = service.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: UUID, db: Session = Depends(get_db), storage=Depends(get_storage), _: User = Depends(require_roles(["admin"]))):
    service = ModelService(ModelRepository(db), storage)
    service.delete_model_by_id(model_id)