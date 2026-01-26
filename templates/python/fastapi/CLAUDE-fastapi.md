# Claude Code Guidelines: FastAPI

> **Extends:** [CLAUDE-python.md](../CLAUDE-python.md)

## FastAPI Patterns

### Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── config.py             # Settings
│   ├── dependencies.py       # Dependency injection
│   ├── database.py           # Database setup
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   ├── repositories/         # Data access
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       └── endpoints/
│   └── core/
│       ├── security.py
│       └── exceptions.py
├── tests/
├── alembic/
└── pyproject.toml
```

### Application Setup

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await engine.connect()
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
```

### Configuration

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    project_name: str = "My API"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    redis_url: str
    secret_key: str
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = []

    model_config = {"env_file": ".env"}

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Schemas (Pydantic)

```python
# app/schemas/user.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserList(BaseModel):
    data: list[UserResponse]
    total: int
    page: int
    size: int
```

### Endpoints

```python
# app/api/v1/endpoints/users.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.user import UserCreate, UserResponse, UserList, UserUpdate
from app.services.user_service import UserService
from app.dependencies import get_user_service, get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=UserList)
async def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    users, total = await service.list_users(page=page, size=size)
    return UserList(data=users, total=total, page=page, size=size)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
):
    existing = await service.get_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return await service.create(user_in)

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await service.update(user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Services

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.core.security import hash_password

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.repository.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(email)

    async def list_users(self, page: int, size: int) -> tuple[list[User], int]:
        offset = (page - 1) * size
        users = await self.repository.list(offset=offset, limit=size)
        total = await self.repository.count()
        return users, total

    async def create(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            name=data.name,
            hashed_password=hash_password(data.password),
        )
        return await self.repository.create(user)

    async def update(self, user_id: int, data: UserUpdate) -> User | None:
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(user, update_data)
```

### Dependencies

```python
# app/dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> UserRepository:
    return UserRepository(session)

async def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repository)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = await service.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user
```

### Exception Handlers

```python
# app/core/exceptions.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )

# Register in main.py
app.add_exception_handler(AppException, app_exception_handler)
```

### Testing

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.main import app
from app.database import get_session

@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.fixture
async def authenticated_client(async_client, test_user):
    token = create_access_token({"sub": test_user.id})
    async_client.headers["Authorization"] = f"Bearer {token}"
    return async_client

# tests/test_users.py
@pytest.mark.asyncio
async def test_create_user(async_client):
    response = await async_client.post("/api/v1/users/", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123",
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_list_users_requires_auth(async_client):
    response = await async_client.get("/api/v1/users/")
    assert response.status_code == 401
```
