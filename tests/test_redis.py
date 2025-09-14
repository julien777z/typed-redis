from typing import Annotated

import pytest
from pydantic import ValidationError
from fakeredis import FakeAsyncRedis
from tests.fixtures import UserFixture
from typed_redis import RedisPrimaryKey, RedisModel, Store


async def _create_user(user_class: type[UserFixture], idx: int, name: str) -> UserFixture:
    """Create a test user."""

    new_user = user_class(id=idx, name=name)

    await new_user.create()

    return new_user


async def _assert_valid_user(user: UserFixture, redis_mock: FakeAsyncRedis):
    """Assert the user is valid."""

    assert user._client == redis_mock
    assert user._redis_key == f"user:{user.id}"

    assert await redis_mock.get(user._redis_key) == user.model_dump_json()


class TestModelCreation:
    """Group creation-related Redis model tests."""

    def test_build_redis_key_and_model_name(self, user_class: type[UserFixture]):
        """Class helpers should reflect model_name and build proper keys."""

        assert user_class.model_name == "user"
        assert user_class._build_redis_key(42) == "user:42"

    @pytest.mark.asyncio
    async def test_create_redis_model(self, user_class: type[UserFixture], redis_mock: FakeAsyncRedis):
        """Test the Redis model create method."""

        new_user = await _create_user(user_class, idx=1, name="John Doe")

        await _assert_valid_user(new_user, redis_mock)

    @pytest.mark.asyncio
    async def test_create_redis_model_async_call(
        self, user_class: type[UserFixture], redis_mock: FakeAsyncRedis
    ):
        """Test the Redis model will be created when the model is called asynchronously."""

        new_user = user_class(id=2, name="John Smith")

        await new_user()

        await _assert_valid_user(new_user, redis_mock)

    @pytest.mark.asyncio
    async def test_create_with_expiry_sets_ttl(
        self, user_class: type[UserFixture], redis_mock: FakeAsyncRedis
    ):
        """Passing ex to create should set a TTL on the key."""

        user = user_class(id=3, name="TTL")

        await user.create(ex=60)

        ttl = await redis_mock.ttl(user._redis_key)

        assert ttl is not None and 0 < ttl <= 60


class TestModelValidation:
    """Group validation-related Redis model tests."""

    @pytest.mark.asyncio
    async def test_redis_model_invalid_data(self, user_class: type[UserFixture]):
        """Creating a Redis model with invalid data should raise ValidationError."""

        with pytest.raises(ValidationError):
            user_class(id=1, name=True)

    @pytest.mark.asyncio
    async def test_update_persists_and_validates(
        self, user_class: type[UserFixture], redis_mock: FakeAsyncRedis
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


class TestModelGet:
    """Group get-related Redis model tests."""

    @pytest.mark.asyncio
    async def test_redis_model_get_none(self, user_class: type[UserFixture]):
        """Get should return None if the model does not exist."""

        assert await user_class.get(1) is None

    @pytest.mark.asyncio
    async def test_redis_model_get_valid(self, user_class: type[UserFixture], redis_mock: FakeAsyncRedis):
        """Get should return a valid model."""

        user = await _create_user(user_class, idx=4, name="Before")

        assert await user_class.get(4) == user

        # persisted model is the same as the one returned by get
        assert await redis_mock.get(user._redis_key) == user.model_dump_json()


class TestModelDeletion:
    """Group deletion-related Redis model tests."""

    @pytest.mark.asyncio
    async def test_redis_model_deleted(self, user_class: type[UserFixture]):
        """Deleted Redis model should error when operations are attempted."""

        await _create_user(user_class, idx=1, name="John Doe")

        user = await user_class.get(1)

        await user.delete()

        with pytest.raises(RuntimeError):
            await user.update(name="Jane Doe")

        with pytest.raises(RuntimeError):
            await user.delete()

    @pytest.mark.asyncio
    async def test_delete_sets_deleted_flag(self, user_class: type[UserFixture]):
        """Delete should mark the instance as deleted."""

        user = await _create_user(user_class, idx=5, name="ToDelete")

        await user.delete()

        assert user._deleted is True


class TestModelUnbound:
    """Group unbound-client Redis model tests."""

    @pytest.mark.asyncio
    async def test_unbound_model_ops_raise_runtime_error(self):
        """Unbound client access and ops should raise RuntimeError."""

        class Unbound(RedisModel, model_name="unbound"):
            id: Annotated[int, RedisPrimaryKey]

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


class TestModelPrimaryKeyAnnotations:
    """Group primary-key annotation Redis model tests."""

    def test_missing_primary_key_annotation_raises(self, redis_mock: FakeAsyncRedis):
        """Model without a primary key annotation should raise ValueError when key is needed."""

        class NoPk(Store(redis_mock), RedisModel, model_name="nopk"):
            id: int

        obj = NoPk(id=1)

        with pytest.raises(ValueError):
            _ = obj._redis_key

    def test_multiple_primary_key_annotations_raise(self, redis_mock: FakeAsyncRedis):
        """Model with multiple primary keys should raise ValueError when key is computed."""

        class MultiPk(Store(redis_mock), RedisModel, model_name="mpk"):
            id: Annotated[int, RedisPrimaryKey]
            other: Annotated[int, RedisPrimaryKey]

        obj = MultiPk(id=1, other=2)

        with pytest.raises(ValueError):
            _ = obj._redis_key


class TestModelDecoding:
    """Group response-decoding Redis model tests."""

    @pytest.mark.asyncio
    async def test_get_decodes_bytes_when_decode_responses_false(self):
        """Ensure bytes returned from Redis are decoded before model parsing."""

        rbytes = FakeAsyncRedis(decode_responses=False)

        class Foo(Store(rbytes), RedisModel, model_name="foo"):
            id: Annotated[int, RedisPrimaryKey]
            name: str

        original = Foo(id=10, name="Bytes Name")

        await original.create()

        loaded = await Foo.get(10)

        assert isinstance(loaded, Foo)
        assert loaded.id == 10
        assert loaded.name == "Bytes Name"
