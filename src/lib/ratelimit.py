import time
import uuid

from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis: Redis) -> None:
        self._r = redis

    async def check(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        now = int(time.time())
        rk = f"rl:{key}"
        await self._r.zremrangebyscore(rk, 0, now - window)
        count = await self._r.zcard(rk)
        if count >= limit:
            return False, 0, now + window
        await self._r.zadd(rk, {f"{now}:{uuid.uuid4().hex}": now})
        await self._r.expire(rk, window)
        return True, limit - count - 1, now + window
