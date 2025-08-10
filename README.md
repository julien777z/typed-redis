# Pydantic Models for Redis

This repository allows you to create Pydantic models representing Redis objects, allowing
your models to follow a schema with validation and serialization.

The Redis models are async and have ORM-like operations.

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
from typed_redis import Store, PrimaryRedisKey
from redis.asyncio import Redis

redis = Redis(...)

class User(Store(redis)):
    """User model."""

    id: Annotated[int, PrimaryRedisKey]
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

Using your `Store` object created earlier, pass it into your Pydantic classes by inheritting from it.
Annotate one field as the primary key using `PrimaryRedisKey`. The Redis key is derived as `<model_name>:<primary_key_value>`.

`user.py`
```python

from .store import Store

class User(Store):
    """User model."""

    id: Annotated[int, PrimaryRedisKey]
    name: str
```

### Use Your Model

Now you can use your model:

```python

from .user import User

# Get existing user by primary key value
user = await User.get(1)
print(user.name)

# Create new user (idempotent)
new_user = User(id=2, name="Bob")
await new_user() # Same as calling await user.create(...)

print(user.name)

# Update user:
await new_user.update(name="Bob Smith")
print(user.name)
```

### Supported Operations

| Operation | Method | Example | Notes |
| --- | --- | --- | --- |
| Create | `await instance.create(**kwargs)` | `await user.create(ex=60)` | Serializes with `model_dump_json()` and stores at `redis_key`. Optional `ex`, `px`, `nx` are forwarded. |
| Upsert (call) | `await instance()` | `await user()` | Same as `create()` with default options. |
| Update | `await instance.update(**changes)` | `await user.update(name="Charlie Brown")` | Validates via Pydantic `model_copy(update=...)`, then persists. Returns the updated model. |
| Get | `await Model.get(primary_key)` | `user = await User.get(1)` | Key is derived as `<model>:<pk>`. Parses JSON using `model_validate_json(...)`. |
| Delete | `await instance.delete()` | `await user.delete()` | Removes the key at `redis_key`. |

Notes
- Annotate exactly one field with `PrimaryRedisKey`.
- Bind a Redis client via `Store(redis_client)` and inherit from it; otherwise, operations raise a `RuntimeError`.
