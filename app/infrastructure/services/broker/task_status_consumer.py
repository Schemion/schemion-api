import asyncio
import json
import logging
from concurrent.futures import Future
from typing import Any

from bobber import BobberClient

from app.core.enums import QueueTypes
from app.core.services.task_status_service import TaskStatusService
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.persistence.repositories import TaskRepository
from app.infrastructure.services.cache import cache_service

logger = logging.getLogger(__name__)


class BobberTaskStatusConsumer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        self.client = BobberClient(host, port)
        self._loop = loop
        self._threads = []

    def start(self) -> None:
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError as exc:
                raise RuntimeError(
                    "BobberTaskStatusConsumer.start() must be called from an active asyncio event loop"
                ) from exc

        if not self.client.healthcheck():
            raise ConnectionError("Bobber broker unavailable")

        for topic in (
            QueueTypes.inference_queue_result.value,
            QueueTypes.training_queue_result.value,
        ):
            self._threads.append(self.client.subscribe(topic, self._on_broker_message))
            logger.info("Listening to broker topic '%s'", topic)

    def close(self) -> None:
        self.client.close()

    def _on_broker_message(self, payload: dict) -> None:
        message = self._parse_message(payload)
        if not message:
            return

        if self._loop is None or self._loop.is_closed():
            logger.error("Cannot apply task status update without an active event loop: %s", message)
            return

        future = asyncio.run_coroutine_threadsafe(self._apply_status_update(message), self._loop)
        future.add_done_callback(lambda done: self._log_status_update_result(done, message))

    @staticmethod
    def _log_status_update_result(future: Future, message: dict) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("Failed to apply task status update: %s", message)

    async def _apply_status_update(self, message: dict) -> None:
        async with AsyncSessionLocal() as session:
            service = TaskStatusService(
                task_repo=TaskRepository(session),
                cache_repo=cache_service,
            )
            task = await service.apply_update(message)
            if not task:
                logger.warning("Task status update references unknown task: %s", message.get("task_id"))
                return
            logger.info("Task %s status updated to %s", task.id, task.status)

    @staticmethod
    def _parse_message(payload: dict[str, Any]) -> dict | None:
        raw_value = payload.get("value")
        if raw_value is None:
            logger.error("Broker message missing 'value': %s", payload)
            return None
        if isinstance(raw_value, dict):
            return raw_value
        if not isinstance(raw_value, str):
            logger.error("Broker message value must be str or dict, got %s", type(raw_value))
            return None
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            logger.exception("Failed to decode broker message JSON: %s", raw_value)
            return None
