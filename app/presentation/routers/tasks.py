from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile,status

from app.common.security.dependencies import get_current_user
from app.core.enums import TaskStatus
from app.core.services import TaskService
from app.presentation.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"], route_class=DishkaRoute)


@router.post("/create/inference", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_inference_task(service: Annotated[TaskService, FromDishka()],
                                current_user: dict = Depends(get_current_user), model_id: UUID = Form(...),
                                file: UploadFile = File(...)):
    task_create = TaskCreate(
        user_id=UUID(current_user.get("id")),
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
            user_id=UUID(current_user.get("id"))
        )
        return TaskRead.model_validate(created)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create inference task: {e}")


@router.post("/create/training", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_training_task(service: Annotated[TaskService, FromDishka()],
                               current_user: dict = Depends(get_current_user), model_id: UUID = Form(...),
                               dataset_id: UUID = Form(...)):
    task_create = TaskCreate(
        user_id=UUID(current_user.get("id")),
        task_type=TaskStatus.training,
        model_id=model_id,
        dataset_id=dataset_id,
    )
    try:
        created = await service.create_training_task(task_create)
        return TaskRead.model_validate(created)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create training task: {e}")


@router.get("/", response_model=list[TaskRead])
async def get_tasks(service: Annotated[TaskService, FromDishka()], skip: int = 0, limit: int = 100,
                    current_user: dict = Depends(get_current_user)):
    tasks = await service.get_tasks(skip=skip, limit=limit, user_id=UUID(current_user.get("id")))

    return [TaskRead.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(service: Annotated[TaskService, FromDishka()], task_id: UUID,
                   current_user: dict = Depends(get_current_user)):
    task = await service.get_task_by_id(task_id=task_id, user_id=UUID(current_user.get("id")))
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(service: Annotated[TaskService, FromDishka()], task_id: UUID,
                      current_user: dict = Depends(get_current_user)):
    await service.delete_task_by_id(task_id=task_id, user_id=UUID(current_user.get("id")))
