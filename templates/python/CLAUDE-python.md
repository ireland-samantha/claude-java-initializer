# Claude Code Guidelines: Python

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Python 3.11+** for modern features
- **Type hints** on all function signatures
- **Strict typing** with mypy or pyright
- Use `pyproject.toml` for project configuration

## Code Style

### PEP 8 Compliance

- Use `ruff` for linting and formatting
- 88 character line length (Black default)
- 4 spaces for indentation
- Two blank lines between top-level definitions

### Naming Conventions

- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `SCREAMING_SNAKE_CASE` for constants
- `_private` prefix for internal use

### Type Hints

```python
from typing import Optional, TypeVar, Generic
from collections.abc import Sequence, Mapping

T = TypeVar('T')

def get_user(user_id: str) -> User | None:
    """Fetch user by ID."""
    ...

def process_items(items: Sequence[Item]) -> list[Result]:
    """Process a sequence of items."""
    ...

class Repository(Generic[T]):
    def find_by_id(self, id: str) -> T | None:
        ...
```

### Dataclasses and Pydantic

```python
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, EmailStr

# Dataclass for internal domain models
@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)

# Pydantic for DTOs with validation
class CreateUserRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)

    model_config = {"str_strip_whitespace": True}
```

## Project Structure

```
project/
├── pyproject.toml        # Project configuration
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── main.py       # Entry point
│       ├── config.py     # Configuration
│       ├── domain/       # Domain models
│       ├── services/     # Business logic
│       ├── repositories/ # Data access
│       ├── api/          # HTTP layer
│       └── utils/        # Utilities
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

## Error Handling

```python
class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} with ID {id} not found", "NOT_FOUND")

class ValidationError(AppError):
    def __init__(self, message: str, errors: dict[str, list[str]]):
        super().__init__(message, "VALIDATION_ERROR")
        self.errors = errors
```

## Async Patterns

```python
import asyncio
from contextlib import asynccontextmanager

async def fetch_user_data(user_id: str) -> UserData:
    # Concurrent requests
    profile, preferences = await asyncio.gather(
        fetch_profile(user_id),
        fetch_preferences(user_id),
    )
    return UserData(profile=profile, preferences=preferences)

@asynccontextmanager
async def database_transaction():
    async with db.begin() as conn:
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
```

## Dependency Injection

```python
from functools import lru_cache
from typing import Annotated
from fastapi import Depends

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

@lru_cache
def get_user_repository() -> UserRepository:
    return UserRepository(get_database())

def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repository)
```

## Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()
```

## Logging

```python
import logging
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

async def process_order(order_id: str):
    log = logger.bind(order_id=order_id)
    log.info("processing_order_started")
    try:
        result = await do_process(order_id)
        log.info("processing_order_completed", result=result)
    except Exception as e:
        log.error("processing_order_failed", error=str(e))
        raise
```

## Testing

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def user_repository():
    return Mock(spec=UserRepository)

@pytest.fixture
def user_service(user_repository):
    return UserService(user_repository)

class TestUserService:
    async def test_get_user_returns_user_when_found(self, user_service, user_repository):
        user_repository.find_by_id.return_value = User(id="1", name="John")

        result = await user_service.get_user("1")

        assert result.name == "John"
        user_repository.find_by_id.assert_called_once_with("1")

    async def test_get_user_raises_not_found(self, user_service, user_repository):
        user_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await user_service.get_user("999")
```

## Package Management

- Use `uv` or `pip-tools` for dependency management
- Pin all dependencies in `requirements.lock`
- Separate dev dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.100",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
```
