from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from app.core.enums import CacheKeysList, CacheKeysObject, TaskStatus
from app.core.services.task_status_service import TaskStatusService
from tests.utils import run


def test_apply_update_writes_status_and_clears_task_cache():
    task_id = uuid4()
    user_id = uuid4()
    task = SimpleNamespace(id=task_id, user_id=user_id)
    task_repo = SimpleNamespace(update_task_status=AsyncMock(return_value=task))
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())
    service = TaskStatusService(task_repo, cache_repo)

    result = run(
        service.apply_update(
            {
                "task_id": str(task_id),
                "status": TaskStatus.succeeded.value,
                "output_path": "inference/result.json",
                "error_msg": None,
            }
        )
    )

    assert result is task
    task_repo.update_task_status.assert_awaited_once_with(
        task_id=task_id,
        status=TaskStatus.succeeded.value,
        output_path="inference/result.json",
        error_msg=None,
    )
    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.task(task_id=task_id))
    cache_repo.delete_pattern.assert_awaited_once_with(f"{CacheKeysList.TASKS}:{user_id}:*")


def test_apply_update_returns_none_when_task_is_missing():
    task_repo = SimpleNamespace(update_task_status=AsyncMock(return_value=None))
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())
    service = TaskStatusService(task_repo, cache_repo)

    result = run(
        service.apply_update(
            {
                "task_id": str(uuid4()),
                "status": TaskStatus.running.value,
            }
        )
    )

    assert result is None
    cache_repo.delete.assert_not_called()
    cache_repo.delete_pattern.assert_not_called()
