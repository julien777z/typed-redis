from __future__ import annotations

from redis.asyncio import Redis

from .redis import RedisModel

__all__ = ["Store"]

def Store(redis_client: Redis) -> type[RedisModel]: ...
