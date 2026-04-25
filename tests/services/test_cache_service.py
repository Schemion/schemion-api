import time

from app.infrastructure.services.cache.cache_service import CacheService
from tests.utils import run


def test_cache_set_get_delete_roundtrip():
    cache = CacheService(base_ttl=10, jitter_ratio=0)

    run(cache.set("k1", {"a": 1}))
    assert run(cache.get("k1")) == {"a": 1}

    run(cache.delete("k1"))
    assert run(cache.get("k1")) is None


def test_cache_delete_pattern_removes_only_matching_keys():
    cache = CacheService(base_ttl=10, jitter_ratio=0)

    run(cache.set("p:1", "v1"))
    run(cache.set("p:2", "v2"))
    run(cache.set("other", "v3"))

    run(cache.delete_pattern("p:*"))

    assert run(cache.get("p:1")) is None
    assert run(cache.get("p:2")) is None
    assert run(cache.get("other")) == "v3"


def test_cache_value_expires_with_explicit_ttl():
    cache = CacheService(base_ttl=100, jitter_ratio=0)

    run(cache.set("temp", "value", expire=1))
    assert run(cache.get("temp")) == "value"

    time.sleep(1.1)
    assert run(cache.get("temp")) is None
