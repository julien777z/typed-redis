from __future__ import annotations

from redis.asyncio import Redis

from .redis import RedisModel

__all__ = ["Store"]


def Store(redis_client: Redis) -> type[RedisModel]:  # pylint: disable=invalid-name
    """Return a base model class bound to the given Redis client."""

    class StoreBase(RedisModel):
        """Base model class bound to the provided Redis client."""

        _redis = redis_client

    StoreBase.__name__ = "StoreBase"

    return StoreBase
