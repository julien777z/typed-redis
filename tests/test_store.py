from __future__ import annotations

from typing import Annotated

import pytest
from fakeredis import FakeAsyncRedis

from typed_redis import RedisPrimaryKey, RedisModel, Store


def test_store_binds_client_and_is_subclass(redis_mock: FakeAsyncRedis) -> None:
    """Ensure Store binds the Redis client and produces a RedisModel subclass."""

    class Foo(Store(redis_mock), RedisModel, model_name="foo"):
        id: Annotated[int, RedisPrimaryKey]

    assert issubclass(Foo, RedisModel)
    assert Foo._redis is redis_mock


@pytest.mark.asyncio
async def test_store_class_uses_bound_client_in_ops(redis_mock: FakeAsyncRedis) -> None:
    """Ensure the bound client is used by model operations."""

    class Foo(Store(redis_mock), RedisModel, model_name="foo"):
        id: Annotated[int, RedisPrimaryKey]

    obj = Foo(id=1)
    await obj.create()

    assert await redis_mock.get("foo:1") == obj.model_dump_json()


def test_store_multiple_clients_isolated() -> None:
    """Ensure different Store instances bind different clients without leakage."""

    r1 = FakeAsyncRedis(decode_responses=True)
    r2 = FakeAsyncRedis(decode_responses=True)

    class A(Store(r1), RedisModel, model_name="a"):
        id: Annotated[int, RedisPrimaryKey]

    class B(Store(r2), RedisModel, model_name="b"):
        id: Annotated[int, RedisPrimaryKey]

    assert A._redis is r1
    assert B._redis is r2
    assert A._redis is not B._redis
