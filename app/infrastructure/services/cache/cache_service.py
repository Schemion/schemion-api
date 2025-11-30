import json
from typing import Any, Optional

from redis.asyncio import Redis

from app.config import settings
from app.core.interfaces import ICacheRepository

class CacheService(ICacheRepository):
    def __init__(self, url: str):
        self._redis = Redis.from_url(
            url,
            decode_responses=True,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
        )


    async def get(self, key: str) -> Optional[Any]:
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        if not isinstance(value, str):
            value = json.dumps(value)
        await self._redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)