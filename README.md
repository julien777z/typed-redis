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

from typed_redis import Store
from redis.asyncio import Redis

redis = Redis(...)

class User(Store(redis)):
    """User model."""

    id: int
    name: str

    @property
    def redis_key(self) -> str:
        return f"user:{self.id}"


 user = User(id=1, name="Charlie")

 await user.create() # Store user object in Redis

# Later:
user = await user.get("user:1")
print(user.name) # "Charlie"
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
Add a `redis_key` property to return the string that should be used as the Redis key.

`user.py`
```python

from .store import Store

class User(Store):
    """User model."""

    id: int
    name: str

    @property
    def redis_key(self) -> str:
        return f"user:{self.id}"
```

### Use Your Model

Now you can use your model:

```python

from .user import User

# Get existing user
user = await user.get("user:1")
print(user.name)

# Create new user (idempotent)
new_user = User(id=2, name="Bob")
await new_user() # Same as calling await user.create(...)

print(user.name)

# Update user:
await new_user.update(name="Bob Smith")
print(user.name)
```
