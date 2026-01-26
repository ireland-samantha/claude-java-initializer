# Claude Code Guidelines: Flask

> **Extends:** [CLAUDE-python.md](../CLAUDE-python.md)

## Flask Patterns

### Project Structure

```
project/
├── app/
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration
│   ├── extensions.py         # Flask extensions
│   ├── models/               # SQLAlchemy models
│   ├── services/             # Business logic
│   ├── api/                  # API blueprints
│   │   ├── __init__.py
│   │   └── users/
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       ├── schemas.py
│   │       └── handlers.py
│   └── utils/
├── migrations/               # Alembic migrations
├── tests/
└── wsgi.py
```

### Application Factory

```python
# app/__init__.py
from flask import Flask
from app.config import Config
from app.extensions import db, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    from app.api.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix="/api/users")

    # Register error handlers
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return {"error": error.messages}, 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return {"error": "Resource not found"}, 404
```

### Configuration

```python
# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
```

### Extensions

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
```

### Models

```python
# app/models/user.py
from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    posts = db.relationship("Post", back_populates="author", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.email}>"
```

### Schemas (Marshmallow)

```python
# app/api/users/schemas.py
from marshmallow import Schema, fields, validate, post_load

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    created_at = fields.DateTime(dump_only=True)

class CreateUserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)
create_user_schema = CreateUserSchema()
```

### Routes

```python
# app/api/users/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.users.schemas import user_schema, users_schema, create_user_schema
from app.services.user_service import UserService

bp = Blueprint("users", __name__)

@bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = UserService.list_users(page=page, per_page=per_page)

    return jsonify({
        "data": users_schema.dump(pagination.items),
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    })

@bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = UserService.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_schema.dump(user))

@bp.route("/", methods=["POST"])
def create_user():
    data = create_user_schema.load(request.json)
    user = UserService.create_user(**data)
    return jsonify(user_schema.dump(user)), 201
```

### Services

```python
# app/services/user_service.py
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.user import User

class UserService:
    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    @staticmethod
    def list_users(page: int = 1, per_page: int = 20):
        return User.query.filter_by(is_active=True).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def create_user(email: str, name: str, password: str) -> User:
        if UserService.get_by_email(email):
            raise ValueError("Email already registered")

        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return user
```

### Decorators

```python
# app/utils/decorators.py
from functools import wraps
from flask import request
from marshmallow import ValidationError

def validate_json(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = schema.load(request.json)
                request.validated_data = data
            except ValidationError as e:
                return {"errors": e.messages}, 400
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

### Testing

```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db
from app.config import TestingConfig

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client, user):
    response = client.post("/api/auth/login", json={
        "email": user.email,
        "password": "password123",
    })
    token = response.json["access_token"]
    return {"Authorization": f"Bearer {token}"}

# tests/test_users.py
def test_create_user(client):
    response = client.post("/api/users/", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123",
    })
    assert response.status_code == 201
    assert response.json["email"] == "test@example.com"

def test_list_users_requires_auth(client):
    response = client.get("/api/users/")
    assert response.status_code == 401
```
