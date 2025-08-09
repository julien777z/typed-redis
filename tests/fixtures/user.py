import pytest
from fakeredis import FakeAsyncRedis
from typed_redis import RedisModel, Store


__all__ = ["user_class", "UserFixture"]


class UserFixture(RedisModel):
    """User fixture."""

    id: int
    name: str
    email: str

    @property
    def redis_key(self) -> str:
        return f"user:{self.id}"


@pytest.fixture(autouse=True)
def user_class(redis_mock: FakeAsyncRedis) -> type[UserFixture]:
    """Create a User with a mock Redis client."""

    class User(Store(redis_mock), UserFixture):
        """User model class bound to the mock Redis client."""

    return User
