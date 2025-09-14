# Pydantic Models for Redis

[![Coverage](https://img.shields.io/codecov/c/github/julien777z/typed-redis?branch=main&label=Coverage)](https://codecov.io/gh/julien777z/typed-redis)

Typed Redis provides strongly typed, Pydantic-based models for Redis with built-in validation and serialization.

It offers an async, ORM-like API for creating, retrieving, updating, and deleting data stored in Redis.

## Installation

Install with [pip](https://pip.pypa.io/en/stable/)
```bash
pip install typed_redis
```

## Features

- Add a schema to Redis models with validation and serialization
- Async support
- ORM-like syntax

## Example

```python
from typing import Annotated
from typed_redis import Store, RedisPrimaryKey
from redis.asyncio import Redis

redis = Redis(...)

class User(Store(redis), model_name="user"):
    """User model."""

    id: Annotated[int, RedisPrimaryKey]
    name: str


user = User(id=1, name="Charlie")

await user.create()  # Store user object in Redis

# Later:
user = await User.get(1)  # Look up by primary key value
print(user.name)  # "Charlie"
```

## Documentation

### Create Store

The `Store` function takes in your Redis instance and returns back a base class with the ORM operations.

Create a Store:

`store.py`
```python

from redis.asyncio import Redis
from typed_redis import Store as _Store

redis = Redis(...)

Store = _Store(redis)
```

### Create Model

Using your `Store` object created earlier, inherit from it and set a `model_name` class argument to prefix your Redis keys for this model.
Annotate one field as the primary key using `RedisPrimaryKey`. This field value will be used as the value for the Redis key.

> Note: The Redis key is derived using the model name and field value.

`user.py`
```python

from typed_redis import RedisPrimaryKey
from .store import Store

class User(Store, model_name="user"):
    """User model."""

    id: Annotated[int, RedisPrimaryKey]
    name: str
```

### Use Your Model

Now you can use your model:

```python

from .user import User

# Get existing user by primary key value
user = await User.get(1)

# Create new user (idempotent)
new_user = User(id=2, name="Bob")
await new_user() # Same as calling await user.create(...)

# Update user:
await new_user.update(name="Bob Smith")
```

### Supported Operations

| Operation | Method | Example | Notes |
| --- | --- | --- | --- |
| Create | `await instance.create(**kwargs)` or `await instance(**kwargs)` | `await user.create(ex=60)` or `await user(ex=60)` | Serializes with `model_dump_json()` and stores in Redis. Optional kwargs are passed to Redis. |
| Update | `await instance.update(**changes)` | `await user.update(name="Charlie Brown")` | Validates via Pydantic then persists to Redis. |
| Get | `await Model.get(primary_key)` | `user = await User.get(1)` | Key is derived as `<model_name>:<pk>`. Parses JSON using `model_validate_json(...)` and returns the model if it exists; otherwise, `None` is returned. |
| Delete | `await instance.delete()` | `await user.delete()` | Removes the model from Redis. No further operations are allowed after this is called. |

Notes
- Annotate exactly one field with `RedisPrimaryKey`.
- Bind a Redis client via `Store(redis_client)` and inherit from it; otherwise, operations raise a `RuntimeError`.
- Set the model name using the `model_name` class argument, e.g., `class User(Store, model_name="user"):`. This determines the Redis key prefix.
