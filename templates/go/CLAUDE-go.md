# Claude Code Guidelines: Go

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Go 1.21+** for modern features
- **Modules** for dependency management
- Follow [Effective Go](https://golang.org/doc/effective_go) and [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)

## Project Structure

```
project/
├── cmd/
│   └── api/
│       └── main.go           # Entry point
├── internal/                 # Private application code
│   ├── config/
│   ├── domain/               # Domain models
│   ├── handler/              # HTTP handlers
│   ├── service/              # Business logic
│   ├── repository/           # Data access
│   └── middleware/
├── pkg/                      # Public library code
├── api/                      # API definitions (OpenAPI, protobuf)
├── migrations/
├── go.mod
└── go.sum
```

## Code Style

### Naming Conventions

- `MixedCaps` or `mixedCaps` (no underscores)
- Short, concise names: `i` not `index`, `buf` not `buffer`
- Acronyms are all caps: `HTTPHandler`, `userID`
- Interfaces: single-method interfaces end in `-er` (Reader, Writer)
- Avoid stuttering: `http.Server` not `http.HTTPServer`

### Package Design

- Package names are lowercase, single word
- Avoid generic names: `util`, `common`, `misc`
- Design for the caller, not the implementer

```go
// Good - clear, specific package name
package user

type Service struct { ... }
func (s *Service) Create(ctx context.Context, u *User) error

// Usage: user.Service, user.Create

// Bad - generic name, stuttering
package models

type UserModel struct { ... }
```

### Error Handling

- Check errors immediately
- Add context when wrapping errors
- Use sentinel errors for expected conditions
- Use custom error types for rich error information

```go
// Sentinel errors
var (
    ErrNotFound = errors.New("not found")
    ErrConflict = errors.New("conflict")
)

// Custom error type
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

// Wrapping errors with context
user, err := s.repo.FindByID(ctx, id)
if err != nil {
    return nil, fmt.Errorf("find user %s: %w", id, err)
}

// Checking wrapped errors
if errors.Is(err, ErrNotFound) {
    return nil, status.Error(codes.NotFound, "user not found")
}
```

### Interfaces

- Define interfaces where they're used, not where implemented
- Keep interfaces small (1-3 methods)
- Accept interfaces, return structs

```go
// Defined in service package (consumer)
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*domain.User, error)
    Save(ctx context.Context, user *domain.User) error
}

type Service struct {
    repo UserRepository
}

func NewService(repo UserRepository) *Service {
    return &Service{repo: repo}
}
```

### Context

- First parameter for functions that do I/O
- Use for cancellation, deadlines, request-scoped values
- Don't store contexts in structs

```go
func (s *Service) CreateUser(ctx context.Context, req CreateUserRequest) (*User, error) {
    // Check for cancellation
    select {
    case <-ctx.Done():
        return nil, ctx.Err()
    default:
    }

    // Pass context to downstream calls
    return s.repo.Save(ctx, user)
}
```

### Concurrency

```go
// Use errgroup for concurrent operations
g, ctx := errgroup.WithContext(ctx)

g.Go(func() error {
    profile, err = s.fetchProfile(ctx, userID)
    return err
})

g.Go(func() error {
    settings, err = s.fetchSettings(ctx, userID)
    return err
})

if err := g.Wait(); err != nil {
    return nil, err
}

// Protect shared state with mutex
type Cache struct {
    mu    sync.RWMutex
    items map[string]Item
}

func (c *Cache) Get(key string) (Item, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    item, ok := c.items[key]
    return item, ok
}
```

### HTTP Handlers

```go
type Handler struct {
    service *Service
    logger  *slog.Logger
}

func (h *Handler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        h.respondError(w, http.StatusBadRequest, "invalid request body")
        return
    }

    user, err := h.service.Create(r.Context(), req)
    if err != nil {
        var validErr *ValidationError
        if errors.As(err, &validErr) {
            h.respondError(w, http.StatusBadRequest, validErr.Error())
            return
        }
        h.logger.Error("create user failed", "error", err)
        h.respondError(w, http.StatusInternalServerError, "internal error")
        return
    }

    h.respondJSON(w, http.StatusCreated, user)
}

func (h *Handler) respondJSON(w http.ResponseWriter, status int, data any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}
```

### Dependency Injection

```go
// Wire dependencies manually in main
func main() {
    cfg := config.Load()

    db, err := sql.Open("postgres", cfg.DatabaseURL)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    userRepo := repository.NewUserRepository(db)
    userService := service.NewUserService(userRepo)
    userHandler := handler.NewUserHandler(userService)

    router := http.NewServeMux()
    router.HandleFunc("POST /users", userHandler.Create)
    router.HandleFunc("GET /users/{id}", userHandler.GetByID)

    log.Fatal(http.ListenAndServe(":8080", router))
}
```

### Configuration

```go
type Config struct {
    Port        int    `env:"PORT" envDefault:"8080"`
    DatabaseURL string `env:"DATABASE_URL,required"`
    LogLevel    string `env:"LOG_LEVEL" envDefault:"info"`
}

func Load() (*Config, error) {
    var cfg Config
    if err := env.Parse(&cfg); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }
    return &cfg, nil
}
```

### Logging

```go
// Use slog (standard library, Go 1.21+)
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))

logger.Info("user created",
    slog.String("user_id", user.ID),
    slog.String("email", user.Email),
)

// Add context to logger
ctx = context.WithValue(ctx, loggerKey, logger.With(
    slog.String("request_id", requestID),
))
```

## Testing

```go
func TestUserService_Create(t *testing.T) {
    t.Run("creates user with valid data", func(t *testing.T) {
        repo := &mockUserRepo{
            saveFn: func(ctx context.Context, u *domain.User) error {
                return nil
            },
        }
        svc := NewService(repo)

        user, err := svc.Create(context.Background(), CreateUserRequest{
            Email: "test@example.com",
            Name:  "Test User",
        })

        if err != nil {
            t.Fatalf("unexpected error: %v", err)
        }
        if user.Email != "test@example.com" {
            t.Errorf("expected email test@example.com, got %s", user.Email)
        }
    })

    t.Run("returns error for duplicate email", func(t *testing.T) {
        repo := &mockUserRepo{
            findByEmailFn: func(ctx context.Context, email string) (*domain.User, error) {
                return &domain.User{}, nil // exists
            },
        }
        svc := NewService(repo)

        _, err := svc.Create(context.Background(), CreateUserRequest{
            Email: "existing@example.com",
        })

        if !errors.Is(err, ErrConflict) {
            t.Errorf("expected ErrConflict, got %v", err)
        }
    })
}
```

### Table-Driven Tests

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {"valid email", "test@example.com", false},
        {"missing @", "testexample.com", true},
        {"empty", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.email)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateEmail(%q) error = %v, wantErr %v", tt.email, err, tt.wantErr)
            }
        })
    }
}
```
