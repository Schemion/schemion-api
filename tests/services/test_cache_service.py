import json

from app.infrastructure.services.cache.cache_service import CacheService
from tests.utils import run


class _FakeRedis:
    def __init__(self):
        self.data = {}
        self.deleted = []
        self.set_calls = []

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.set_calls.append((key, value, ex))
        self.data[key] = value

    async def delete(self, key):
        self.deleted.append(key)
        self.data.pop(key, None)

    async def scan_iter(self, match=None):
        for key in list(self.data.keys()):
            if match is None or key.startswith(match.replace("*", "")):
                yield key


def test_cache_get_set_delete(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr("app.infrastructure.services.cache.cache_service.Redis.from_url", lambda *_args, **_kwargs: fake)

    cache = CacheService("redis://local")

    run(cache.set("k1", {"a": 1}, expire=10))
    assert json.loads(fake.data["k1"]) == {"a": 1}

    value = run(cache.get("k1"))
    assert value == {"a": 1}

    run(cache.delete("k1"))
    assert "k1" in fake.deleted


def test_cache_delete_pattern(monkeypatch):
    fake = _FakeRedis()
    fake.data = {"p:1": "1", "p:2": "2", "other": "3"}
    monkeypatch.setattr("app.infrastructure.services.cache.cache_service.Redis.from_url", lambda *_args, **_kwargs: fake)

    cache = CacheService("redis://local")
    run(cache.delete_pattern("p:*"))

    assert "p:1" in fake.deleted
    assert "p:2" in fake.deleted
    assert "other" not in fake.deleted
