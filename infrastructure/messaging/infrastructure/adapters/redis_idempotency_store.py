import asyncio
import re
from typing import Optional
import redis.asyncio as aioredis
from domain.ports.idempotency_port import IdempotencyPort


class RedisIdempotencyStore(IdempotencyPort):
    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._client: Optional[aioredis.Redis] = None
        self._id_pattern = re.compile(r'^[a-zA-Z0-9\-_:]{1,256}$')

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = await aioredis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _validate_event_id(self, event_id: str) -> bool:
        if not event_id or not isinstance(event_id, str):
            return False
        return bool(self._id_pattern.match(event_id))

    async def check_and_store(self, event_id: str) -> bool:
        if not self._validate_event_id(event_id):
            raise ValueError(f"Invalid event_id format: {event_id}")

        client = await self._get_client()
        key = f"idempotency:{event_id}"

        existing = await client.get(key)
        if existing is not None:
            return False

        await client.setex(key, self.ttl_seconds, "1")
        return True

    async def exists(self, event_id: str) -> bool:
        if not self._validate_event_id(event_id):
            return False

        client = await self._get_client()
        key = f"idempotency:{event_id}"
        return await client.exists(key) > 0

    async def close(self) -> None:
        if self._client:
            await self._client.close()
