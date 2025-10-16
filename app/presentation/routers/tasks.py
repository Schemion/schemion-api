from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.common.security.dependencies import require_roles
from app.core.entities import User
from app.core.enums import TaskStatus
from app.core.services import TaskService
from app.dependencies import get_storage, get_db
from app.infrastructure.database.repositories import TaskRepository
from app.presentation.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create/inference", response_model=TaskRead, status_code=201)
def create_inference_task(
    user_id: UUID = Form(...),
    model_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
):
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}."
        )

    task_create = TaskCreate(
        user_id=user_id,
        task_type=TaskStatus.inference,
        model_id=model_id,
    )

    service = TaskService(TaskRepository(db), storage)

    try:
        file_data = file.file.read()
        created = service.create_inference_task(
            task=task_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create inference task: {e}")


@router.post("/create/training", response_model=TaskRead, status_code=201)
def create_training_task(
    user_id: UUID = Form(...),
    dataset_id: UUID = Form(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
):
    task_create = TaskCreate(
        user_id=user_id,
        task_type=TaskStatus.training,
        dataset_id=dataset_id,
    )
    service = TaskService(TaskRepository(db), storage)
    try:
        created = service.create_training_task(task_create)
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create training task: {e}")

@router.get("/", response_model=list[TaskRead])
def get_tasks(skip: int = 0,limit: int = 100,user_id: Optional[UUID] = None,model_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    service = TaskService(TaskRepository(db), Depends(get_storage))
    return service.get_tasks(skip, limit, user_id, model_id)


@router.get("/user/{user_id}", response_model=list[TaskRead])
def get_tasks_by_user(user_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(TaskRepository(db), Depends(get_storage))
    tasks = service.get_tasks_by_user_id(user_id)
    if tasks is None:
        raise HTTPException(status_code=404, detail="User not found")
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(TaskRepository(db), Depends(get_storage))
    task = service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID, db: Session = Depends(get_db), storage=Depends(get_storage), _: User = Depends(require_roles(["admin"]))):
    service = TaskService(TaskRepository(db), storage)
    service.delete_task_by_id(task_id)