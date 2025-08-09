---
alwaysApply: true
---

# Cursor Project Rules — Python 3.12 + Poetry (PEP 621)

_These rules tell Cursor how to scaffold and edit this project. Stick to them unless I explicitly say otherwise._

## High-priority rules
- Target **Python 3.12**.
- Use **Poetry 2.x** with **PEP 621** `[project]` metadata in `pyproject.toml` (no legacy `[tool.poetry]` for metadata/deps).
- Prefer **separate modules/files** over giant files.
- Use **modern typing**: `str | None`, `list[str]`, `dict[str, Any]`, etc. (no `Optional[T]`, no `List[T]`).
- Add a **one-line docstring** after every `def`/`class`. Then **one blank line** after the docstring.
- Keep comments minimal. Don’t generate extra Markdown files beyond this rules doc and the separate **Project Layout** file.
- Use **Black** for formatting (not Ruff). Black can infer target versions from `[project.requires-python]`.
- Use **pytest** (and `pytest-asyncio`) for tests.
- Prefer **Pydantic v2** models when objects are needed (validation/serialization). Avoid `dataclasses` unless asked.
- Prefer **`aiohttp`** for HTTP I/O and async patterns.
- **No module-level globals**. Pass dependencies explicitly.
- Services can be **plain functions**; inject the client/session and config via parameters.

---

## `pyproject.toml` (Poetry 2.x + PEP 621)

```toml
[project]
name = "app"
version = "0.0.1"
description = "App"
readme = "README.md"
requires-python = ">=3.12"
authors = [{ name = "Me", email = "me@example.com" }]

# Runtime dependencies per PEP 621
dependencies = [
  "aiohttp>=3.9",
  "pydantic>=2.8",
  "SQLAlchemy>=2.0",
  "asyncpg>=0.29",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "black>=24.0",
  "pyright>=1.1.380",
  "coverage>=7.6",
]

[project.scripts]
app = "app.__main__:main"

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"

[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 100
target-version = ["py312"]

# Keep build system details at the end.
[build-system]
requires = ["poetry-core>=2.0.0"]
build-backend = "poetry.core.masonry.api"
```

**Commands**
- `poetry install`
- `poetry run black .`
- `poetry run pyright`
- `poetry run pytest`

---

## Coding style
- **Docstrings**: one sentence, imperative, then a blank line.
  ```python
  def fetch_user(user_id: int) -> "UserOut":
      """Fetch a user by id."""

      ...
  ```
- **Newlines**: keep the rhythm—blank line after the docstring and between logical sections.
- **Types**: `str | None`, `list[str]`, `dict[str, Any]`, `Callable[[T], R]`; prefer PEP-695 generics when useful.
- **Data models**: prefer **Pydantic v2** (`BaseModel`) for input/output schemas and validation. Keep them small and colocated under `models/`.

---

## Errors & logging
- Put HTTP-style errors in `core/errors.py` (e.g., `ErrorResponse` or `Error`).
- **Generation rule for Cursor**: when writing service modules, **import** `ErrorResponse` **or** `Error` from `app.core.errors` and alias to `HttpError`. **Do not** add runtime `try/except` fallbacks; if neither exists, **Cursor should create** one in `core/errors.py` instead of adding runtime logic to the service.
- Configure `logging` once in `core/logging.py`; avoid prints.

---

## I/O (HTTP) — `aiohttp`
- Accept an injected `aiohttp.ClientSession` with a sensible `ClientTimeout`.
- Prefer creating the session at app startup and passing it down.
- Use `raise_for_status=True` on the session if convenient; parse with `await resp.json()` or `await resp.text()`.

---

## Example modules (function-based service, async SQLAlchemy, Pydantic)

`src/app/core/errors.py`
```python
from http import HTTPStatus

class ErrorResponse(Exception):
    """HTTP-like error with status."""

    def __init__(self, message: str, status: HTTPStatus) -> None:
        """Initialize the error."""

        super().__init__(message)
        self.status = status


class Error(Exception):
    """Generic application error."""
```

`src/app/models/domain.py`
```python
from typing import Annotated
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


intpk = Annotated[int, mapped_column(primary_key=True)]

class User(Base):
    """User table."""

    __tablename__ = "users"

    id: Mapped[intpk]
    email: Mapped[str]
    full_name: Mapped[str | None]
```

`src/app/clients/db.py`
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

def make_sessionmaker(dsn: str) -> async_sessionmaker[AsyncSession]:
    """Create an async SQLAlchemy sessionmaker."""

    engine = create_async_engine(dsn, echo=False, future=True)
    return async_sessionmaker(engine, expire_on_commit=False)
```

`src/app/services/user_service.py`
```python
from http import HTTPStatus
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorResponse
from app.models.domain import User


class UserOut(BaseModel):
    """Public user fields."""

    id: int
    email: str
    full_name: str | None = None


async def get_user(session: AsyncSession, user_id: int) -> UserOut:
    """Return a user by id."""

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()

    if obj is None:
        raise ErrorResponse("User not found.", status_code=HTTPStatus.NOT_FOUND)

    return UserOut.model_validate(obj, from_attributes=True)
```

---

## Tests
- Use `pytest` with small, readable tests.
- For async, mark tests with `@pytest.mark.asyncio`.
- Prefer dependency injection or fakes over heavy patching.

---

## Keep it lean
- No extra tutorial markdowns or design essays.
- No monolith files—split into `clients/`, `services/`, `models/`, `core/`.
- Minimal comments; clear names + types should be enough.
