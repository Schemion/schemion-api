from uuid import UUID

from app.core.enums import CacheKeysList, CacheKeysObject, TaskStatus
from app.core.interfaces import ICacheRepository, ITaskRepository


class TaskStatusService:
    def __init__(self, task_repo: ITaskRepository, cache_repo: ICacheRepository):
        self.task_repo = task_repo
        self.cache_repo = cache_repo

    async def apply_update(self, update: dict):
        task_id = UUID(str(update["task_id"]))
        raw_status = update["status"]
        status = raw_status if isinstance(raw_status, TaskStatus) else TaskStatus(str(raw_status))

        task = await self.task_repo.update_task_status(
            task_id=task_id,
            status=status.value,
            output_path=update.get("output_path"),
            error_msg=update.get("error_msg"),
        )
        if not task:
            return None

        await self.cache_repo.delete(CacheKeysObject.task(task_id=task.id))
        await self.cache_repo.delete_pattern(f"{CacheKeysList.TASKS}:{task.user_id}:*")
        return task
