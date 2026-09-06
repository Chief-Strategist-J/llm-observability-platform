import redis
from shared.ports.redis_port import RedisPort


class RedisAdapter(RedisPort):
    def __init__(self, url: str):
        self.client = redis.from_url(url)

    def get_ewma(self, service: str, model: str, hour_of_week: int) -> float | None:
        key = f"ewma:cost:{service}:{model}:{hour_of_week}"
        val = self.client.get(key)
        if val is not None:
            if isinstance(val, (str, bytes)):
                return float(val)
        return None

    def set_ewma(
        self, service: str, model: str, hour_of_week: int, value: float
    ) -> None:
        key = f"ewma:cost:{service}:{model}:{hour_of_week}"
        self.client.set(key, str(value))

    def get_fenwick_sum(self, dimension: str, window: str, key: str) -> int:
        lua = """
        local key = KEYS[1]
        local i = tonumber(ARGV[1])
        local sum = 0
        while i > 0 do
            sum = sum + tonumber(redis.call('HGET', key, tostring(i)) or '0')
            i = i - bit.band(i, -i)
        end
        return sum
        """
        redis_key = f"fenwick:{dimension}:{window}:{key}"
        script = self.client.register_script(lua)
        res = script(keys=[redis_key], args=["1024"])
        if res is None or res == b"" or res == "":
            return 0
        return int(res)

