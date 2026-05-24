import json
from typing import Any

from redis.asyncio import Redis


class Cache:
    def __init__(self, redis: Redis) -> None:
        self._r = redis

    async def get(self, key: str) -> Any | None:
        raw = await self._r.get(key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        await self._r.set(key, json.dumps(value, default=str), ex=ttl)

    async def delete(self, *keys: str) -> None:
        if keys:
            await self._r.delete(*keys)
