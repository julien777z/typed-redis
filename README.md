# Pydantic Models for Redis

This repository allows you to create Pydantic models representing Redis objects, allowing
your models to follow a schema with validation and serialization.

The Redis models are async and have ORM-like operations.

## Example

```python

import asyncio
import json
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

async def main():
    """Main function."""

    user = User(id=1, name="Charlie")

    await user() # or: await user.create()

    print(await redis.get("user:1")) # JSON representation of the user

    # Now let's update the user:
    await user.update(name="Bob")

    json_model = json.loads(await redis.get("user:1"))

    print(json_model["name"]) # Bob



asyncio.run(main())

```

## Documentation

### Create Store

The `Store` function takes in your Redis instance and returns back a base class with the ORM operations.

Create a Store:

`store.py`
```python

from redis.asyncio import Redis
from typed_redis import Store as RedisStore

redis = Redis(...)

Store = RedisStore(redis)
```

### Create Model

Using your `Store` object created earlier, pass it into your Pydantic classes:

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

Change `redis_key` to return the string that should be used as the Redis key.

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
