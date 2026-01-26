# Claude Code Guidelines: Rust

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Rust 2021 edition**
- Use `rustfmt` for formatting
- Use `clippy` with pedantic lints
- Prefer safe Rust; document and minimize `unsafe` usage

## Project Structure

```
project/
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── main.rs               # Binary entry point
│   ├── lib.rs                # Library root
│   ├── config.rs
│   ├── domain/
│   │   ├── mod.rs
│   │   └── user.rs
│   ├── services/
│   ├── repositories/
│   ├── handlers/
│   └── error.rs
├── tests/                    # Integration tests
└── benches/                  # Benchmarks
```

## Code Style

### Naming Conventions

- `snake_case` for functions, variables, modules, files
- `PascalCase` for types, traits, enums
- `SCREAMING_SNAKE_CASE` for constants and statics
- Prefix unused variables with `_`

### Ownership and Borrowing

```rust
// Prefer borrowing over ownership when possible
fn process_user(user: &User) -> Result<(), Error> {
    // ...
}

// Take ownership only when needed
fn consume_user(user: User) -> UserResult {
    // user is consumed here
}

// Use Cow for flexibility
fn normalize_name(name: &str) -> Cow<'_, str> {
    if name.contains(' ') {
        Cow::Owned(name.trim().to_lowercase())
    } else {
        Cow::Borrowed(name)
    }
}
```

### Error Handling

```rust
// Define domain errors with thiserror
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("user not found: {0}")]
    NotFound(String),

    #[error("validation error: {0}")]
    Validation(String),

    #[error("database error")]
    Database(#[from] sqlx::Error),

    #[error("internal error")]
    Internal(#[source] anyhow::Error),
}

// Use Result type alias
pub type Result<T> = std::result::Result<T, AppError>;

// Propagate errors with ?
async fn get_user(&self, id: &str) -> Result<User> {
    let user = self.repo
        .find_by_id(id)
        .await?
        .ok_or_else(|| AppError::NotFound(id.to_string()))?;
    Ok(user)
}
```

### Structs and Enums

```rust
// Use builder pattern for complex structs
#[derive(Debug, Clone)]
pub struct User {
    id: String,
    email: String,
    name: String,
    created_at: DateTime<Utc>,
}

impl User {
    pub fn builder() -> UserBuilder {
        UserBuilder::default()
    }
}

#[derive(Default)]
pub struct UserBuilder {
    email: Option<String>,
    name: Option<String>,
}

impl UserBuilder {
    pub fn email(mut self, email: impl Into<String>) -> Self {
        self.email = Some(email.into());
        self
    }

    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    pub fn build(self) -> Result<User> {
        Ok(User {
            id: Uuid::new_v4().to_string(),
            email: self.email.ok_or(AppError::Validation("email required".into()))?,
            name: self.name.ok_or(AppError::Validation("name required".into()))?,
            created_at: Utc::now(),
        })
    }
}

// Use enums for state machines
#[derive(Debug, Clone)]
pub enum OrderStatus {
    Pending,
    Confirmed { confirmed_at: DateTime<Utc> },
    Shipped { tracking_number: String },
    Delivered { delivered_at: DateTime<Utc> },
    Cancelled { reason: String },
}
```

### Traits

```rust
// Define traits for abstractions
#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: &str) -> Result<Option<User>>;
    async fn find_by_email(&self, email: &str) -> Result<Option<User>>;
    async fn save(&self, user: &User) -> Result<()>;
    async fn delete(&self, id: &str) -> Result<()>;
}

// Implement for concrete types
pub struct PostgresUserRepository {
    pool: PgPool,
}

#[async_trait]
impl UserRepository for PostgresUserRepository {
    async fn find_by_id(&self, id: &str) -> Result<Option<User>> {
        let user = sqlx::query_as!(
            User,
            "SELECT * FROM users WHERE id = $1",
            id
        )
        .fetch_optional(&self.pool)
        .await?;
        Ok(user)
    }
    // ...
}
```

### Async/Await

```rust
use tokio::try_join;

// Concurrent execution
async fn fetch_user_data(&self, user_id: &str) -> Result<UserData> {
    let (profile, settings) = try_join!(
        self.fetch_profile(user_id),
        self.fetch_settings(user_id),
    )?;
    Ok(UserData { profile, settings })
}

// Proper cancellation handling
async fn fetch_with_timeout(&self, id: &str) -> Result<Data> {
    tokio::time::timeout(
        Duration::from_secs(30),
        self.fetch(id)
    )
    .await
    .map_err(|_| AppError::Timeout)?
}
```

### HTTP with Axum

```rust
use axum::{
    extract::{Path, State, Json},
    http::StatusCode,
    routing::{get, post},
    Router,
};

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/users", post(create_user))
        .route("/users/:id", get(get_user))
        .with_state(state)
}

async fn create_user(
    State(state): State<AppState>,
    Json(req): Json<CreateUserRequest>,
) -> Result<(StatusCode, Json<User>), AppError> {
    let user = state.user_service.create(req).await?;
    Ok((StatusCode::CREATED, Json(user)))
}

async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<User>, AppError> {
    let user = state.user_service
        .get_by_id(&id)
        .await?;
    Ok(Json(user))
}

// Error response conversion
impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            AppError::NotFound(_) => (StatusCode::NOT_FOUND, self.to_string()),
            AppError::Validation(_) => (StatusCode::BAD_REQUEST, self.to_string()),
            _ => (StatusCode::INTERNAL_SERVER_ERROR, "Internal error".to_string()),
        };

        let body = Json(json!({ "error": message }));
        (status, body).into_response()
    }
}
```

### Configuration

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Config {
    #[serde(default = "default_port")]
    pub port: u16,
    pub database_url: String,
    pub redis_url: Option<String>,
}

fn default_port() -> u16 {
    8080
}

impl Config {
    pub fn from_env() -> Result<Self> {
        envy::from_env()
            .map_err(|e| AppError::Config(e.to_string()))
    }
}
```

## Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_create_user() {
        let repo = MockUserRepository::new();
        let service = UserService::new(Arc::new(repo));

        let result = service.create(CreateUserRequest {
            email: "test@example.com".to_string(),
            name: "Test User".to_string(),
        }).await;

        assert!(result.is_ok());
        let user = result.unwrap();
        assert_eq!(user.email, "test@example.com");
    }

    #[tokio::test]
    async fn test_get_user_not_found() {
        let repo = MockUserRepository::new();
        let service = UserService::new(Arc::new(repo));

        let result = service.get_by_id("nonexistent").await;

        assert!(matches!(result, Err(AppError::NotFound(_))));
    }
}

// Use proptest for property-based testing
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_email_validation(email in "[a-z]+@[a-z]+\\.[a-z]+") {
        let result = validate_email(&email);
        prop_assert!(result.is_ok());
    }
}
```

## Dependencies (Cargo.toml)

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
axum = "0.7"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres"] }
thiserror = "1"
anyhow = "1"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["json"] }
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }

[dev-dependencies]
tokio-test = "0.4"
proptest = "1"
```
