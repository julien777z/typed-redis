from typing import Annotated
import pytest
from fakeredis import FakeAsyncRedis
from typed_redis import RedisPrimaryKey, RedisModel, Store


__all__ = ["user_class", "UserFixture"]


class UserFixture(RedisModel):
    """User fixture."""

    id: Annotated[int, RedisPrimaryKey]
    name: str


@pytest.fixture(autouse=True)
def user_class(redis_mock: FakeAsyncRedis) -> type[UserFixture]:
    """Create a User with a mock Redis client."""

    class User(
        Store(redis_mock), UserFixture, model_name="user"
    ):  # pylint: disable=inherit-non-class
        """User model class bound to the mock Redis client."""

    return User
