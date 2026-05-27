import os
import pytest
import redis as redis_lib

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

FENWICK_UPDATE_LUA = """
local key = KEYS[1]
local delta = tonumber(ARGV[1])
local i = tonumber(ARGV[2])
local n = tonumber(ARGV[3])
while i <= n do
    redis.call('HINCRBY', key, tostring(i), delta)
    i = i + bit.band(i, -i)
end
return 1
"""

FENWICK_QUERY_LUA = """
local key = KEYS[1]
local i = tonumber(ARGV[1])
local sum = 0
while i > 0 do
    sum = sum + tonumber(redis.call('HGET', key, tostring(i)) or '0')
    i = i - bit.band(i, -i)
end
return sum
"""

TOKEN_BUCKET_DEDUCT_LUA = """
local key = KEYS[1]
local delta = tonumber(ARGV[1])
local current = tonumber(redis.call('GET', key) or '0')
local new_val = current - delta
redis.call('SET', key, tostring(new_val))
return new_val
"""


def _redis_available() -> bool:
    try:
        client = redis_lib.from_url(REDIS_URL)
        client.ping()
        client.close()
        return True
    except Exception:
        return False


@pytest.fixture
def redis_client():
    client = redis_lib.from_url(REDIS_URL)
    yield client
    client.flushdb()
    client.close()


@pytest.mark.skipif(not _redis_available(), reason="Redis not available")
class TestFenwickLuaScript:
    def test_single_update_and_query(self, redis_client: redis_lib.Redis) -> None:
        update_script = redis_client.register_script(FENWICK_UPDATE_LUA)
        query_script = redis_client.register_script(FENWICK_QUERY_LUA)

        update_script(keys=["fenwick:test"], args=["100", "1", "8"])
        result = query_script(keys=["fenwick:test"], args=["1"])
        assert int(result) == 100

    def test_multiple_updates_accumulate(self, redis_client: redis_lib.Redis) -> None:
        update_script = redis_client.register_script(FENWICK_UPDATE_LUA)
        query_script = redis_client.register_script(FENWICK_QUERY_LUA)

        update_script(keys=["fenwick:acc"], args=["50", "1", "8"])
        update_script(keys=["fenwick:acc"], args=["30", "1", "8"])
        result = query_script(keys=["fenwick:acc"], args=["1"])
        assert int(result) == 80

    def test_pipeline_execution(self, redis_client: redis_lib.Redis) -> None:
        update_script = redis_client.register_script(FENWICK_UPDATE_LUA)
        query_script = redis_client.register_script(FENWICK_QUERY_LUA)

        pipe = redis_client.pipeline(transaction=False)
        for i in range(5):
            pipe.evalsha(update_script.sha, 1, f"fenwick:pipe:{i}", "10", "1", "8")
        pipe.execute()

        for i in range(5):
            result = query_script(keys=[f"fenwick:pipe:{i}"], args=["1"])
            assert int(result) == 10


@pytest.mark.skipif(not _redis_available(), reason="Redis not available")
class TestTokenBucketLuaScript:
    def test_deduct_from_zero_goes_negative(self, redis_client: redis_lib.Redis) -> None:
        script = redis_client.register_script(TOKEN_BUCKET_DEDUCT_LUA)
        result = script(keys=["bucket:test"], args=["100"])
        assert int(result) == -100

    def test_deduct_from_positive(self, redis_client: redis_lib.Redis) -> None:
        redis_client.set("bucket:pos", "500")
        script = redis_client.register_script(TOKEN_BUCKET_DEDUCT_LUA)
        result = script(keys=["bucket:pos"], args=["200"])
        assert int(result) == 300

    def test_multiple_deductions(self, redis_client: redis_lib.Redis) -> None:
        redis_client.set("bucket:multi", "1000")
        script = redis_client.register_script(TOKEN_BUCKET_DEDUCT_LUA)
        script(keys=["bucket:multi"], args=["300"])
        result = script(keys=["bucket:multi"], args=["400"])
        assert int(result) == 300
