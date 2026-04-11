import random
from typing import Any, Optional, Union

from aiocache import Cache
from app.core.interfaces import ICacheRepository


class CacheService(ICacheRepository):
    def __init__(self, base_ttl: int = 5, jitter_ratio: float = 0.3,):
        self._cache = Cache(Cache.MEMORY)
        self._base_ttl = base_ttl
        self._jitter_ratio = jitter_ratio

    async def get(self, key: str) -> Optional[Union[dict, list]]:
        return await self._cache.get(key)

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        ttl = self._calculate_ttl(expire)
        await self._cache.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        await self._cache.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        keys = await self._cache.keys(pattern)
        for key in keys:
            await self._cache.delete(key)
            
    def _calculate_ttl(self, expire: int | None = None) -> int:
        base_ttl = expire if expire is not None else self._base_ttl
        if not base_ttl:
            return 0
        jitter = base_ttl + random.uniform(0, self._jitter_ratio)
        return int(base_ttl +  jitter)
