from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Generic, TypedDict, TypeVar

from redis.asyncio import Redis
from super_model import SuperModel

__all__ = ["RedisPrimaryKey", "RedisModel"]


class RedisKwargs(TypedDict, total=False):
    """Kwargs for the Redis operations."""

    ex: int
    px: int
    nx: bool


class _RedisPrimaryKeyAnnotation:  # pylint: disable=too-few-public-methods
    """Annotation for the primary key of the model."""


RedisPrimaryKey = _RedisPrimaryKeyAnnotation()

T = TypeVar("T")


class ModelWithParameter:
    """Model with a parameter."""

    model_name: str

    def __init_subclass__(cls, model_name: str | None = None, **kwargs: Any) -> None:
        """Initialize the subclass."""

        cls.model_name = model_name

        super().__init_subclass__(**kwargs)


class RedisModel(SuperModel, ABC, ModelWithParameter, Generic[T]):
    """Base class for Redis-backed Pydantic models."""

    # Class-level Redis client. Set by the `Store` factory on the base class.
    _redis: ClassVar[Redis | None] = None

    # Whether the model has been deleted. No further operations are allowed if this is True.
    _deleted: bool = False

    # The name of the model. Passed by using the `model_name` Class argument.
    model_name: ClassVar[str | None] = None

    def _assert_not_deleted(self) -> None:
        """Assert that the model has not been deleted."""

        if self._deleted:
            raise RuntimeError(
                f"Model {self.__class__.__name__} has been deleted. No further operations are allowed."
            )

    @classmethod
    def _assert_redis_client(cls) -> None:
        """Assert that the model has a Redis client bound."""

        if cls._redis is None:
            raise RuntimeError(
                f"No Redis client bound for {cls.__name__}. Use Store(redis_client) and inherit from the returned base."
            )

    @property
    def _primary_key_field_name(self) -> str:
        """Return the field name annotated as the primary key."""

        primary_key_fields = self.get_annotated_fields(RedisPrimaryKey)

        if len(primary_key_fields) > 1:
            raise ValueError("Only one primary key is allowed.")

        if len(primary_key_fields) == 0:
            raise ValueError("Primary key cannot be empty.")

        return next(iter(primary_key_fields.keys()))

    @classmethod
    def _build_redis_key(cls, primary_key: T) -> str:
        """Build a Redis key from a primary key value."""

        return f"{cls.model_name}:{primary_key}"

    @property
    def _redis_key(self) -> str:
        """Return this instance's Redis key."""

        field_name = self._primary_key_field_name
        pk_value: T = getattr(self, field_name)

        return self._build_redis_key(pk_value)

    @property
    def _client(self) -> Redis:
        """Return the bound Redis client."""

        self._assert_not_deleted()
        self._assert_redis_client()

        client = self._redis

        return client

    async def _store_to_redis(self, **kwargs: RedisKwargs) -> None:
        """Store the model to Redis."""

        data = self.model_dump_json()

        await self._client.set(self._redis_key, data, **kwargs)

    async def create(self, **kwargs: RedisKwargs) -> None:
        """Create the model in Redis. This is idempotent."""

        await self._store_to_redis(**kwargs)

    async def update(self, **changes: dict) -> None:
        """Validate and persist updates into Redis."""

        self.model_validate({**self.model_dump(), **changes})

        for key, value in changes.items():
            setattr(self, key, value)

        await self._store_to_redis()

    async def delete(self) -> None:
        """Delete the model from Redis. No further operations are allowed after this is called."""

        await self._client.delete(self._redis_key)

        self._deleted = True

    @classmethod
    async def get(cls, primary_key: T) -> RedisModel[T]:
        """Get the model from Redis and parse it into the Pydantic model."""

        cls._assert_redis_client()

        client = cls._redis

        data = await client.get(cls._build_redis_key(primary_key))

        if isinstance(data, bytes):
            data = data.decode("utf-8")

        return cls.model_validate_json(data)

    async def __call__(self) -> None:
        """Initialize the model."""

        await self.create()
