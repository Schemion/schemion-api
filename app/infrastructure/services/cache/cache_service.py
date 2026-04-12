import random
import re
import time
import threading
from typing import Any, Optional, Union

from app.core.interfaces import ICacheRepository


class AsyncMemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()

    async def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._store:
                value, expiry = self._store[key]
                if time.time() < expiry:
                    return value
                del self._store[key]
            return None

    async def set(self, key: str, value: Any, ttl: int = 0) -> None:
        with self._lock:
            if ttl > 0:
                expiry = time.time() + ttl
            else:
                expiry = float('inf')
            self._store[key] = (value, expiry)

    async def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def keys(self, pattern: str = "*") -> list[str]:
        regex = "^" + re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".") + "$"
        compiled = re.compile(regex)

        now = time.time()
        matched = []
        expired_keys = []

        with self._lock:
            for key in self._store:
                if compiled.match(key):
                    _, expiry = self._store[key]
                    if now < expiry:
                        matched.append(key)
                    else:
                        expired_keys.append(key)

            for k in expired_keys:
                del self._store[k]

        return matched

    async def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        now = time.time()
        with self._lock:
            return sum(1 for _, exp in self._store.values() if now < exp)

class CacheService(ICacheRepository):
    def __init__(self, base_ttl: int = 5, jitter_ratio: float = 0.3):
        self._cache = AsyncMemoryCache()
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
        jitter = base_ttl * random.uniform(0, self._jitter_ratio)
        return int(base_ttl + jitter)