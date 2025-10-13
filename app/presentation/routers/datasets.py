from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.common.security.dependencies import require_roles
from app.core.entities import User
from app.core.services import DatasetService
from app.dependencies import get_storage, get_db
from app.infrastructure.database.repositories import DatasetRepository
from app.presentation.schemas import DatasetCreate, DatasetRead

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/create", response_model=DatasetRead, status_code=201)
def create_dataset(name: str = Form(...), description: Optional[str] = Form(None), num_samples: Optional[int] = Form(None),
                   file: UploadFile = File(...), db: Session = Depends(get_db), storage=Depends(get_storage), _: User = Depends(require_roles(["admin"]))
    ):
    dataset_create = DatasetCreate(
        name=name,
        description=description,
        num_samples=num_samples or 0
    )

    service = DatasetService(DatasetRepository(db), storage)
    try:
        file_data = file.file.read()
        created = service.create_dataset(
            dataset=dataset_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        file.file.close()
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {e}")


@router.get("/", response_model=list[DatasetRead])
def get_datasets(skip: int = 0,limit: int = 100,name_contains: Optional[str] = None,db: Session = Depends(get_db), storage = Depends(get_storage)):
    service = DatasetService(DatasetRepository(db), storage)
    return service.get_datasets(skip, limit, name_contains)


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: UUID, db: Session = Depends(get_db), storage = Depends(get_storage)):
    service = DatasetService(DatasetRepository(db), storage)
    dataset = service.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: UUID, db: Session = Depends(get_db), storage=Depends(get_storage), _: User = Depends(require_roles(["admin"]))):
    service = DatasetService(DatasetRepository(db), storage)
    service.delete_dataset_by_id(dataset_id)