from typing import Final

import pytest
from pydantic import ValidationError
from fakeredis import FakeAsyncRedis
from tests.fixtures import UserFixture

TEST_EMAIL: Final[str] = "john.doe@example.com"


async def _create_user(user_class: type[UserFixture], idx: int, name: str) -> UserFixture:
    """Create a test user."""

    new_user = user_class(id=idx, name=name, email=TEST_EMAIL)

    await new_user.create()

    return new_user


async def _assert_valid_user(user: UserFixture, redis_mock: FakeAsyncRedis):
    """Assert the user is valid."""

    assert user._client() == redis_mock
    assert user.redis_key == f"user:{user.id}"

    assert await redis_mock.get(user.redis_key) == user.model_dump_json()


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
