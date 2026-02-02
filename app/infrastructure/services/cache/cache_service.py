import json
from typing import Any, Optional, Union

from redis.asyncio import Redis

from app.core.interfaces import ICacheRepository


class CacheService(ICacheRepository):
    def __init__(self, url: str):
        self._redis = Redis.from_url(
            url,
            decode_responses=True,
        )

    async def get(self, key: str) -> Optional[Union[dict, list]]:
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        value = json.dumps(value, default=str)
        await self._redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        async for key in self._redis.scan_iter(match=pattern):
            await self._redis.delete(key)
