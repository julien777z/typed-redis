import pytest
from fakeredis import FakeAsyncRedis
from tests.fixtures import *


@pytest.fixture(autouse=True)
async def redis_mock() -> FakeAsyncRedis:
    """Create a mock Redis client."""

    return FakeAsyncRedis(decode_responses=True)
