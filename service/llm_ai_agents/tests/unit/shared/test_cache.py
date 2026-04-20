import threading
import pytest
from services.shared.cache import _InstanceCache


def test_set_and_get_returns_value():
    cache = _InstanceCache()
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_get_missing_key_returns_none():
    cache = _InstanceCache()
    assert cache.get("nonexistent") is None


def test_set_overwrites_existing_key():
    cache = _InstanceCache()
    cache.set("key", "first")
    cache.set("key", "second")
    assert cache.get("key") == "second"


def test_clear_removes_all_entries():
    cache = _InstanceCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_thread_safe_concurrent_writes():
    cache = _InstanceCache()
    errors = []

    def write(n):
        try:
            for i in range(50):
                cache.set(f"key-{n}-{i}", n * i)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=write, args=(n,)) for n in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors


def test_stores_arbitrary_objects():
    cache = _InstanceCache()
    obj = {"nested": [1, 2, 3]}
    cache.set("obj", obj)
    assert cache.get("obj") is obj
