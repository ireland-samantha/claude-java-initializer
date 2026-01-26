# Claude Code Guidelines: Django

> **Extends:** [CLAUDE-python.md](../CLAUDE-python.md)

## Django Patterns

### Project Structure

```
project/
├── manage.py
├── config/                   # Project configuration
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   └── users/
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── services.py       # Business logic
│       ├── selectors.py      # Query logic
│       ├── urls.py
│       ├── admin.py
│       └── tests/
└── common/                   # Shared utilities
```

### Models

- Keep models focused on data structure
- Use model managers for query logic
- Add `__str__` and `Meta` class

```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

class PostManager(models.Manager):
    def published(self):
        return self.filter(status="published")

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    objects = PostManager()
```

### Services and Selectors Pattern

```python
# services.py - Write operations
class UserService:
    @staticmethod
    def create_user(*, email: str, password: str, name: str) -> User:
        user = User(email=email, name=name)
        user.set_password(password)
        user.full_clean()
        user.save()
        return user

    @staticmethod
    def update_user(*, user: User, data: dict) -> User:
        for field, value in data.items():
            setattr(user, field, value)
        user.full_clean()
        user.save()
        return user

# selectors.py - Read operations
class UserSelector:
    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def list_active(*, filters: dict | None = None) -> QuerySet[User]:
        qs = User.objects.filter(is_active=True)
        if filters:
            qs = qs.filter(**filters)
        return qs
```

### Views (Django REST Framework)

```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = UserSelector.list_active()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.create_user(**serializer.validated_data)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
```

### Serializers

```python
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "created_at"]
        read_only_fields = ["id", "created_at"]

class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=100)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
```

### URL Configuration

```python
# apps/users/urls.py
from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("", views.UserListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
]

# config/urls.py
from django.urls import path, include

urlpatterns = [
    path("api/users/", include("apps.users.urls")),
]
```

### Settings

```python
# config/settings/base.py
from pathlib import Path
import environ

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "apps.users",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,
}
```

### Middleware

```python
import uuid
import structlog

logger = structlog.get_logger()

class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.correlation_id = correlation_id

        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id

        return response
```

### Testing

```python
import pytest
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.mark.django_db
class TestUserAPI:
    def test_list_users_requires_auth(self, api_client):
        response = api_client.get(reverse("users:list-create"))
        assert response.status_code == 401

    def test_list_users_returns_users(self, authenticated_client, user):
        response = authenticated_client.get(reverse("users:list-create"))
        assert response.status_code == 200
        assert len(response.data) >= 1
```

### Async Views (Django 4.1+)

```python
from django.http import JsonResponse
from asgiref.sync import sync_to_async

async def async_user_list(request):
    users = await sync_to_async(list)(User.objects.all()[:10])
    return JsonResponse({"users": [u.email for u in users]})
```
