from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID

from app.common.security.dependencies import get_current_user
from app.core.entities import User
from app.core.enums import TaskStatus
from app.core.services import TaskService
from app.dependencies import get_storage, get_db, get_redis
from app.infrastructure.database.repositories import TaskRepository, DatasetRepository, ModelRepository
from app.presentation.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create/inference", response_model=TaskRead, status_code=201)
def create_inference_task(
    current_user: User = Depends(get_current_user),
    model_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    cache = Depends(get_redis()),
):

    task_create = TaskCreate(
        user_id=current_user.id,
        task_type=TaskStatus.inference,
        model_id=model_id,
    )

    service = TaskService(TaskRepository(db), storage, ModelRepository(db), DatasetRepository(db), cache)

    try:
        file_data = file.file.read()
        created = service.create_inference_task(
            task=task_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
            current_user=current_user,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create inference task: {e}")


@router.post("/create/training", response_model=TaskRead, status_code=201)
def create_training_task(
    current_user: User = Depends(get_current_user),
    dataset_id: UUID = Form(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    cache = Depends(get_redis())
):
    task_create = TaskCreate(
        user_id=current_user.id,
        task_type=TaskStatus.training,
        dataset_id=dataset_id,
    )
    service = TaskService(TaskRepository(db), storage, ModelRepository(db), DatasetRepository(db), cache)
    try:
        created = service.create_training_task(task_create)
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create training task: {e}")

@router.get("/", response_model=list[TaskRead])
def get_tasks(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), storage = Depends(get_storage), cache = Depends(get_redis())):
    service = TaskService(TaskRepository(db), storage, ModelRepository(db), DatasetRepository(db), cache)
    return service.get_tasks(current_user,skip, limit)



@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), storage = Depends(get_storage), cache = Depends(get_redis())):
    service = TaskService(TaskRepository(db), storage, ModelRepository(db), DatasetRepository(db), cache)
    task = service.get_task_by_id(task_id, current_user)
    return task



@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID, db: Session = Depends(get_db), storage=Depends(get_storage), current_user: User = Depends(get_current_user), cache = Depends(get_redis())):
    service = TaskService(TaskRepository(db), storage, ModelRepository(db), DatasetRepository(db), cache)
    service.delete_task_by_id(task_id, current_user)