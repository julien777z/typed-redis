from __future__ import annotations
from redis.asyncio import Redis
from .redis import RedisModel

__all__ = ["Store"]


class Store:
    """Factory that binds a Redis client to a new base model class."""

    def __init__(self, redis_client: Redis) -> None:
        """Initialize the store with a Redis client."""

        self.redis_client = redis_client

    def __mro_entries__(self, _bases: tuple[type, ...]) -> tuple[type[RedisModel], ...]:
        """Return the actual base class when used as a base in a class definition."""

        class StoreBase(RedisModel):
            """Base model class bound to the provided Redis client."""

            __redis__ = self.redis_client

        StoreBase.__name__ = "StoreBase"

        return (StoreBase,)
