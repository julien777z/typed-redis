from typing import Annotated
import pytest
from fakeredis import FakeAsyncRedis
from typed_redis import PrimaryRedisKey, RedisModel, Store


__all__ = ["user_class", "UserFixture"]


class UserFixture(RedisModel):
    """User fixture."""

    id: Annotated[int, PrimaryRedisKey]
    name: str
    email: str


@pytest.fixture(autouse=True)
def user_class(redis_mock: FakeAsyncRedis) -> type[UserFixture]:
    """Create a User with a mock Redis client."""

    class User(
        Store(redis_mock), UserFixture, model_name="user"
    ):  # pylint: disable=inherit-non-class
        """User model class bound to the mock Redis client."""

    return User
