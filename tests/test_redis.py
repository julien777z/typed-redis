from typing import Final, Annotated

import pytest
from pydantic import ValidationError
from fakeredis import FakeAsyncRedis
from tests.fixtures import UserFixture
from typed_redis import PrimaryRedisKey, RedisModel, Store

TEST_EMAIL: Final[str] = "john.doe@example.com"


async def _create_user(user_class: type[UserFixture], idx: int, name: str) -> UserFixture:
    """Create a test user."""

    new_user = user_class(id=idx, name=name, email=TEST_EMAIL)

    await new_user.create()

    return new_user


async def _assert_valid_user(user: UserFixture, redis_mock: FakeAsyncRedis):
    """Assert the user is valid."""

    assert user._client == redis_mock
    assert user._redis_key == f"user:{user.id}"

    assert await redis_mock.get(user._redis_key) == user.model_dump_json()


@pytest.mark.asyncio
async def test_create_redis_model(user_class: type[UserFixture], redis_mock: FakeAsyncRedis):
    """Test the Redis model create method."""

    new_user = await _create_user(user_class, idx=1, name="John Doe")

    await _assert_valid_user(new_user, redis_mock)


@pytest.mark.asyncio
async def test_create_redis_model_async_call(
    user_class: type[UserFixture], redis_mock: FakeAsyncRedis
):
    """Test the Redis model will be created when the model is called asynchronously."""

    new_user = user_class(id=2, name="John Smith", email=TEST_EMAIL)

    await new_user()

    await _assert_valid_user(new_user, redis_mock)


@pytest.mark.asyncio
async def test_redis_model_invalid_data(user_class: type[UserFixture]):
    """Test that creating a Redis model with invalid data raises a ValidationError."""

    with pytest.raises(ValidationError):
        user_class(id=1, name=True)


@pytest.mark.asyncio
async def test_redis_model_deleted(user_class: type[UserFixture]):
    """Test that a deleted Redis model raises an error when an operation is attempted."""

    await _create_user(user_class, idx=1, name="John Doe")

    user = await user_class.get(1)

    await user.delete()

    with pytest.raises(RuntimeError):
        await user.update(name="Jane Doe")

    with pytest.raises(RuntimeError):
        await user.delete()


@pytest.mark.asyncio
async def test_unbound_model_ops_raise_runtime_error():
    """Unbound client access and ops should raise RuntimeError."""

    class Unbound(RedisModel, model_name="unbound"):
        id: Annotated[int, PrimaryRedisKey]

    # Synchronous property access must raise
    obj = Unbound(id=1)

    with pytest.raises(RuntimeError):
        _ = obj._client

    # Async operations should also raise
    operations: list[tuple[str, bool]] = [
        ("create", False),  # instance method
        ("get", True),  # class method
    ]

    for method_name, is_classmethod in operations:
        with pytest.raises(RuntimeError):
            if is_classmethod:
                method = getattr(Unbound, method_name)

                await method(1)
            else:
                instance = Unbound(id=1)
                method = getattr(instance, method_name)

                await method()


def test_missing_primary_key_annotation_raises(redis_mock: FakeAsyncRedis):
    """Model without a primary key annotation should raise ValueError when key is needed."""

    class NoPk(Store(redis_mock), RedisModel, model_name="nopk"):
        id: int

    obj = NoPk(id=1)
    with pytest.raises(ValueError):
        _ = obj._redis_key


def test_multiple_primary_key_annotations_raise(redis_mock: FakeAsyncRedis):
    """Model with multiple primary keys should raise ValueError when key is computed."""

    class MultiPk(Store(redis_mock), RedisModel, model_name="mpk"):
        id: Annotated[int, PrimaryRedisKey]
        other: Annotated[int, PrimaryRedisKey]

    obj = MultiPk(id=1, other=2)
    with pytest.raises(ValueError):
        _ = obj._redis_key


@pytest.mark.asyncio
async def test_get_decodes_bytes_when_decode_responses_false():
    """Ensure bytes returned from Redis are decoded before model parsing."""

    rbytes = FakeAsyncRedis(decode_responses=False)

    class Foo(Store(rbytes), RedisModel, model_name="foo"):
        id: Annotated[int, PrimaryRedisKey]
        name: str
        email: str

    original = Foo(id=10, name="Bytes Name", email=TEST_EMAIL)
    await original.create()

    loaded = await Foo.get(10)

    assert isinstance(loaded, Foo)
    assert loaded.id == 10
    assert loaded.name == "Bytes Name"
    assert loaded.email == TEST_EMAIL


@pytest.mark.asyncio
async def test_create_with_expiry_sets_ttl(
    user_class: type[UserFixture], redis_mock: FakeAsyncRedis
):
    """Passing ex to create should set a TTL on the key."""

    user = user_class(id=3, name="TTL", email=TEST_EMAIL)
    await user.create(ex=60)

    ttl = await redis_mock.ttl(user._redis_key)
    assert ttl is not None and 0 < ttl <= 60


@pytest.mark.asyncio
async def test_update_persists_and_validates(
    user_class: type[UserFixture], redis_mock: FakeAsyncRedis
):
    """Update should validate and persist changes."""

    user = await _create_user(user_class, idx=4, name="Before")
    await user.update(name="After")

    # persisted
    assert await redis_mock.get(user._redis_key) == user.model_dump_json()
    assert user.name == "After"

    # invalid update
    with pytest.raises(ValidationError):
        await user.update(name=True)  # type: ignore[arg-type]


def test_build_redis_key_and_model_name(user_class: type[UserFixture]):
    """Class helpers should reflect model_name and build proper keys."""

    assert user_class.model_name == "user"
    assert user_class._build_redis_key(42) == "user:42"


@pytest.mark.asyncio
async def test_delete_sets_deleted_flag(user_class: type[UserFixture]):
    """Delete should mark the instance as deleted."""

    user = await _create_user(user_class, idx=5, name="ToDelete")

    await user.delete()
    assert user._deleted is True
