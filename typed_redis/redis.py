from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self, TypedDict

from pydantic import BaseModel
from redis.asyncio import Redis

__all__ = ["RedisModel"]


class RedisKwargs(TypedDict, total=False):
    """Kwargs for the Redis operations."""

    ex: int
    px: int
    nx: bool


class RedisModel(BaseModel, ABC):
    """Base class for Redis-backed Pydantic models."""

    # Class-level Redis client. Set by the `Store` factory on the base class.
    __redis__: ClassVar[Any | None] = None

    @property
    @abstractmethod
    def redis_key(self) -> str:
        """Return this instance's Redis key."""

    @classmethod
    def client(cls) -> Redis:
        """Return the bound Redis client."""

        client = cls.__redis__

        if client is None:
            raise RuntimeError(
                f"No Redis client bound for {cls.__name__}. Use Store(redis_client) and inherit from the returned base."
            )

        return client

    async def _store_to_redis(self, **kwargs: RedisKwargs) -> None:
        """Store the model to Redis."""

        data = self.model_dump_json()

        await self.client().set(self.redis_key, data, **kwargs)

    async def create(self, **kwargs: RedisKwargs) -> Self:
        """Create this model only if it doesn't exist (NX)."""

        await self._store_to_redis(**kwargs)

        return self

    async def update(self, **changes: Any) -> Self:
        """Validate and persist updates using Pydantic copy(update=...)."""

        updated: Self = self.model_copy(update=changes)

        await self._store_to_redis()

        return updated

    @classmethod
    async def get(cls, key: str) -> Self:
        """Get the model from Redis."""

        data = await cls.client().get(key)

        return cls.model_validate_json(data)

    async def __call__(self) -> None:
        """Initialize the model."""

        await self.create()
