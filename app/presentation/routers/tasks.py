from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile,status
from fastapi.sse import EventSourceResponse
import asyncio

from app.common.security.dependencies import get_current_user
from app.core.enums import TaskType
from app.core.services import TaskService
from app.presentation.schemas import TaskCreate, TaskRead
from app.infrastructure.rate_limiter import limiter

router = APIRouter(prefix="/tasks", tags=["tasks"], route_class=DishkaRoute)


@router.post("/create/inference", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_inference_task(request: Request, service: Annotated[TaskService, FromDishka()],
                                current_user: dict = Depends(get_current_user), model_id: UUID = Form(...),
                                file: UploadFile = File(...)):
    task_create = TaskCreate(
        user_id=UUID(current_user.get("id")),
        task_type=TaskType.inference,
        model_id=model_id,
    )
    try:
        file_data = await asyncio.wait_for(file.read(), timeout=10)
        created = await service.create_inference_task(
            task=task_create,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
            user_id=UUID(current_user.get("id"))
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="File read operation timed out")
    finally:
        await file.close()
    return TaskRead.model_validate(created)

@router.post("/create/training", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("2/hour")
async def create_training_task(
    request: Request,
    service: Annotated[TaskService, FromDishka()], model_id: UUID = Form(...), 
    dataset_id: UUID = Form(...), image_size: int = Form(...), 
    num_epochs: int = Form(...), name: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    task_create = TaskCreate(
        user_id=UUID(current_user.get("id")),
        task_type=TaskType.training,
        model_id=model_id,
        dataset_id=dataset_id,
        image_size=image_size,
        epochs=num_epochs,
        name=name,
    )
    try:
        created = await asyncio.wait_for(service.create_training_task(task_create), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Task creation timed out")
    return TaskRead.model_validate(created)

@router.get("/", response_model=list[TaskRead])
async def get_tasks(service: Annotated[TaskService, FromDishka()], skip: int = 0, limit: int = 100,
                    current_user: dict = Depends(get_current_user)):
    tasks = await service.get_tasks(skip=skip, limit=limit, user_id=UUID(current_user.get("id")))

    return [TaskRead.model_validate(task) for task in tasks]

@router.get("/subscribe/{task_id}", response_class=EventSourceResponse, response_model=None)
async def subscribe_to_task_updates(service: Annotated[TaskService, FromDishka()], task_id: UUID,
                                    current_user: dict = Depends(get_current_user)):
    user_id = UUID(current_user.get("id"))
    async def event_generator():
        while True:
            task = await service.get_task_by_id(task_id=task_id, user_id=user_id)
            # SSE expects text or dict with "data"/"event"
            yield {"event": "task_update", "data": TaskRead.model_validate(task).model_dump()}
            if task.status in ("succeeded", "failed"):
                    break
            await asyncio.sleep(1)
    return EventSourceResponse(event_generator())

@router.get("/{task_id}", response_model=TaskRead)
async def get_task(service: Annotated[TaskService, FromDishka()], task_id: UUID,
                   current_user: dict = Depends(get_current_user)):
    task = await service.get_task_by_id(task_id=task_id, user_id=UUID(current_user.get("id")))
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(service: Annotated[TaskService, FromDishka()], task_id: UUID,
                      current_user: dict = Depends(get_current_user)):
    await service.delete_task_by_id(task_id=task_id, user_id=UUID(current_user.get("id")))
