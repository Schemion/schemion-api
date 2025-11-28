import json
from typing import Any, Optional

import redis

from app.core.interfaces import ICacheRepository

class CacheService(ICacheRepository):
    def __init__(self, url: str):
        self._redis = redis.from_url(url, decode_responses=True)


    def get(self, key: str) -> Optional[Any]:
        data = self._redis.get(key)
        return json.loads(data) if data else None

    def set(self, key: str, value: Any, expire: int | None = None) -> None:
        if not isinstance(value, str):
            value = json.dumps(value)
        self._redis.set(key, value, ex=expire)

    def delete(self, key: str) -> None:
        self._redis.delete(key)