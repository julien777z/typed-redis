# Typed Redis for Python

This repository allows you to create Pydantic models representing Redis objects.

The Redis models are async and follow an ORM-like syntax.

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