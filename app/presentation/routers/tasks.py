from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.security.dependencies import get_current_user
from app.container import ApplicationContainer
from app.core.entities import User
from app.core.enums import TaskStatus
from app.core.services import TaskService
from app.dependencies import get_db
from app.presentation.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create/inference", response_model=TaskRead, status_code=201)
@inject
async def create_inference_task(
        current_user: User = Depends(get_current_user),
        model_id: UUID = Form(...),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        service: TaskService = Depends(Provide[ApplicationContainer.task_service])
):

    task_create = TaskCreate(
        user_id=current_user.id,
        task_type=TaskStatus.inference,
        model_id=model_id,
    )


    try:
        file_data = file.file.read()
        created = await service.create_inference_task(
            task=task_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
            current_user=current_user,
            session=db
        )
        return TaskRead.model_validate(created)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create inference task: {e}")


@router.post("/create/training", response_model=TaskRead, status_code=201)
@inject
async def create_training_task(
        current_user: User = Depends(get_current_user),
        dataset_id: UUID = Form(...),
        db: AsyncSession = Depends(get_db),
        service: TaskService = Depends(Provide[ApplicationContainer.task_service])
):
    task_create = TaskCreate(
        user_id=current_user.id,
        task_type=TaskStatus.training,
        dataset_id=dataset_id,
    )
    try:
        created = await service.create_training_task(db, task_create)
        return TaskRead.model_validate(created)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create training task: {e}")

@router.get("/", response_model=list[TaskRead])
@inject
async def get_tasks(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        service: TaskService = Depends(Provide[ApplicationContainer.task_service])
):
    tasks = await service.get_tasks(db, current_user, skip, limit)

    return [TaskRead.model_validate(task) for task in tasks]



@router.get("/{task_id}", response_model=TaskRead)
@inject
async def get_task(
        task_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        service: TaskService = Depends(Provide[ApplicationContainer.task_service])
):
    task = await service.get_task_by_id(db,task_id, current_user)
    return TaskRead.model_validate(task)



@router.delete("/{task_id}", status_code=204)
@inject
async def delete_task(
        task_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        service: TaskService = Depends(Provide[ApplicationContainer.task_service])
):
    await service.delete_task_by_id(db, task_id, current_user)