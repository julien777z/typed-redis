from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Self, TypedDict

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
    _redis: ClassVar[Redis | None] = None

    # Whether the model has been deleted. No further operations are allowed.
    _deleted: bool = False

    def _assert_not_deleted(self) -> None:
        """Assert that the model has not been deleted."""

        if self._deleted:
            raise RuntimeError(
                f"Model {self.__class__.__name__} has been deleted. No further operations are allowed."
            )

    @property
    @abstractmethod
    def redis_key(self) -> str:
        """Return this instance's Redis key."""

    @classmethod
    def _client(cls) -> Redis:
        """Return the bound Redis client."""

        client = cls.__redis__

        if client is None:
            raise RuntimeError(
                f"No Redis client bound for {cls.__name__}. Use Store(redis_client) and inherit from the returned base."
            )

        return client

    async def _store_to_redis(self, **kwargs: RedisKwargs) -> None:
        """Store the model to Redis."""

        self._assert_not_deleted()

        data = self.model_dump_json()

        await self._client().set(self.redis_key, data, **kwargs)

    async def create(self, **kwargs: RedisKwargs) -> None:
        """Create the model in Redis. This is idempotent."""

        await self._store_to_redis(**kwargs)

    async def update(self, **changes: dict) -> None:
        """Validate and persist updates."""

        for key, value in changes.items():
            setattr(self, key, value)

        await self._store_to_redis()

    async def delete(self) -> None:
        """Delete the model from Redis."""

        self._assert_not_deleted()

        await self._client().delete(self.redis_key)

        self._deleted = True

    @classmethod
    async def get(cls, key: str) -> Self:
        """Get the model from Redis."""

        data = await cls._client().get(key)

        return cls.model_validate_json(data)

    async def __call__(self) -> None:
        """Initialize the model."""

        self._assert_not_deleted()

        await self.create()
