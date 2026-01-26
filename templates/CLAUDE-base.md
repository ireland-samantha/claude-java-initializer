# Claude Code Guidelines

A production-grade software development guide for building modular, maintainable, and extensible systems.

## Core Principles

1. **Separation of Concerns (SoC)**: Each module has one clear responsibility. Don't mix HTTP handling with business logic, or persistence with domain rules.

2. **Single Responsibility Principle (SRP)**: A module should have only one reason to change. Split modules that do too much.

3. **Dependency Injection (DI)**: All dependencies are injected, not instantiated internally. This enables testing and swapping implementations.

4. **Depend on Abstractions**: Depend on contracts/interfaces, not implementations. In functional code, depend on function signatures and protocols.

5. **Clean Architecture Layers**:
   - **Domain**: Pure business objects, no framework dependencies
   - **Application**: Business logic orchestration, depends only on domain and repository interfaces
   - **Infrastructure**: Framework-specific implementations

6. **API-First Design**: Define contracts before implementation

## Architecture Guidelines

- Define clear contracts (interfaces, protocols, or function signatures) for services and data access to enable testability and alternative implementations
- Decouple from frameworks via abstractions — framework-specific code belongs in the infrastructure layer, not in business logic
- Business rules should be defined in pure functions or domain modules; framework-specific behavior belongs in adapters
- Keep modules small and focused — if a file exceeds ~200 lines, consider splitting
- Prefer composition over inheritance (or in functional code: compose small functions into larger ones)

## Package Structure

Organize code by clean architecture with provider-based implementations:

```
project/
├── core/                       # Cross-cutting plugin interfaces and shared models
├── {component}/                # Domain-specific modules
│   ├── dto/                    # Data Transfer Objects
│   ├── exception/              # Custom exceptions
│   ├── model/                  # Domain models and enums
│   ├── repository/             # Repository INTERFACES
│   ├── service/                # Service interfaces AND implementations
│   └── mapper/                 # DTO ↔ Domain model mappers
└── provider/                   # Infrastructure implementations
    ├── http/{component}/       # HTTP controllers
    ├── database/{component}/   # Database repositories and entities
    └── {plugin-name}/          # Plugin implementations
```

**Key principles:**

- **Core**: Cross-cutting plugin interfaces and shared domain models. No framework dependencies.
- **Domain layer**: Domain-specific interfaces, models, DTOs, and service implementations. No framework dependencies except validation annotations.
- **Provider layer**: Framework-specific implementations. Controllers, repositories, and plugin implementations.

## Data Flow and Layer Responsibilities

```
Controller (provider/http)       →  receives DTOs, converts to domain models
    ↓
Service ({component}/service)    →  works with domain models only
    ↓
Repository ({component}/repository) →  interface returns domain models
    ↓
Repository Impl (provider/database) →  converts entities ↔ domain models internally
```

**Layer responsibilities:**

- **Controllers**: Handle HTTP, validate DTOs, convert DTO → domain model, call service, convert domain model → response DTO
- **Services/Use Cases**: Business logic operating on domain models. Never import from `dto/` packages. Return domain models.
- **Repository contracts**: Define persistence contract using domain models (not database entities)
- **Repository implementations**: Handle database entity ↔ domain model conversion internally

## Dependency Rules

**What each layer can import:**

- **Controllers**: DTOs, domain models, service interfaces, mappers
- **Services**: Domain models, repository interfaces, other service interfaces
- **Repository interfaces**: Domain models only
- **Repository implementations**: Entities, domain models, entity mappers

**Never allowed:**

- Services importing DTOs
- Services importing entities
- Controllers importing entities
- Domain models importing anything from `provider/`

## Modular, Plugin-Oriented Architecture

All components must be designed as swappable, self-contained modules. The system should function like a plugin architecture where implementations can be replaced without modifying consumers.

### Plugin Design Guidelines

**Self-contained modules:**
- Each plugin works independently with no knowledge of other plugins
- Plugins communicate only through shared interfaces
- No plugin should import another plugin's classes

**Configuration-driven activation:**
- Plugins are enabled/disabled via configuration, not code changes
- Default implementations should exist for core functionality

**Extension points over modification:**
- Create new interfaces/plugins rather than modifying existing ones
- Use composition to combine behaviors
- Strategy pattern for varying behavior

### When to Create an Extension Point

Create a pluggable interface when:
- The implementation could reasonably vary by deployment
- The behavior is a cross-cutting concern (retry, caching, logging)
- You find yourself writing `if/else` or `switch` on a "type" field
- External integrations are involved (APIs, message queues, storage)
- The functionality could be contained and shipped as a separate independent program

### Standard Extension Points

Design these as pluggable from the start:

- Persistence: Postgres, MongoDB, etc.
- Notifications: Webhook, message queue, etc.
- Task Execution: Local, distributed, etc.
- Authentication: JWT, API key, OAuth, etc.
- Rate Limiting: In-memory, Redis, etc.
- Caching: In-memory, Redis, etc.
- File Storage: Local, S3, GCS, etc.

## Contract Design Principles

- Interfaces are the source of truth, not implementations
- Method signatures should be self-documenting
- Complete documentation on all public methods: purpose, parameters, return value, exceptions
- Explicit failure modes with custom exceptions
- Design for the consumer, not the implementation

## Error Handling

### Error Categories

Define distinct error types for each failure mode:

```
Application Errors
├── ValidationError           # Invalid input from client (400)
├── NotFoundError             # Resource not found (404)
├── ConflictError             # State conflict, duplicate, etc. (409)
├── AuthenticationError       # Identity unknown (401)
├── AuthorizationError        # Identity known, access denied (403)
├── RateLimitError            # Too many requests (429)
├── ExternalServiceError      # Third-party failure (502)
└── InternalError             # Unexpected errors (500)
```

Use exceptions, error types, Result types, or sum types depending on language idioms.

### Error Handling Guidelines

- Define domain-specific errors in `{component}/errors/` or equivalent
- Document possible errors in function/method signatures or contracts
- HTTP handlers translate domain errors to appropriate status codes
- Never leak implementation details in error responses
- Include correlation IDs for tracing
- Log full stack traces server-side, return safe messages client-side

### Standard Error Response

```json
{
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource with ID x not found",
    "timestamp": "2024-01-15T10:30:00Z",
    "correlationId": "abc-123-def",
    "details": {}
}
```

## Input Validation

### Validation Layers

1. **DTO validation**: Structural validation (required fields, formats, ranges)
2. **Domain validation**: Business rule validation (state transitions, invariants)
3. **Database constraints**: Final safety net (unique, foreign keys, not null)

### Validation Guidelines

- Validate early, fail fast
- Return all validation errors at once, not one at a time
- Use declarative validation annotations where possible
- Custom validators for complex business rules
- Sanitize all user input before processing

## Logging and Observability

### Logging Guidelines

- Use structured logging (JSON format)
- Include correlation IDs in all log entries
- Log at appropriate levels:
  - `ERROR`: Unexpected failures requiring attention
  - `WARN`: Recoverable issues, degraded functionality
  - `INFO`: Significant business events, state changes
  - `DEBUG`: Detailed diagnostic information
- Never log sensitive data (passwords, tokens, PII)
- Log entry and exit of significant operations with timing

### Health Checks

Implement health check endpoints:
- `/health/live`: Is the process running?
- `/health/ready`: Is the service ready to accept traffic?
- Include dependency checks (database, cache, message queue)

## Security

### Input Security

- Validate and sanitize all input
- Use parameterized queries (never string concatenation for SQL)
- Implement rate limiting
- Set appropriate request size limits
- Validate content types

### Data Security

- Encrypt sensitive data at rest
- Use TLS for data in transit
- Never log sensitive data
- Implement proper secret management (environment variables, vault)
- Sanitize data in error messages

## Performance and Scalability

### Database Performance

- Use connection pooling with appropriate limits
- Add indexes for frequently queried fields
- Use pagination for list endpoints (cursor-based preferred)
- Avoid N+1 queries
- Consider caching for frequently accessed, rarely changed data

### Async Processing

- Use message queues for long-running operations
- Implement idempotency for message handlers
- Design for at-least-once delivery
- Include correlation IDs in messages

### Resource Limits

- Set timeouts on all external calls
- Implement circuit breakers for external dependencies
- Configure appropriate thread pool sizes

## Resilience

### Retry Strategy

- Use exponential backoff with jitter
- Set maximum retry attempts
- Only retry idempotent operations
- Only retry transient failures (network, timeout, 5xx)
- Don't retry client errors (4xx)

### Circuit Breaker

- **Closed**: Normal operation, requests flow through
- **Open**: Dependency unhealthy, fail fast
- **Half-open**: Testing if dependency recovered

### Idempotency

- Make write operations idempotent where possible
- Use idempotency keys for critical operations
- Handle duplicate requests gracefully

## API Design

### REST Guidelines

- Use nouns for resources, verbs come from HTTP methods
- Use plural names for collections (`/workflows`, not `/workflow`)
- Use kebab-case for URLs (`/workflow-runs`)
- Use camelCase for JSON properties
- Return appropriate HTTP status codes

### HTTP Status Codes

- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST that creates
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: State conflict
- `429 Too Many Requests`: Rate limited
- `500 Internal Server Error`: Unexpected error

### Pagination

Use cursor-based pagination for stability:

```json
{
    "data": [...],
    "pagination": {
        "cursor": "eyJpZCI6MTIzfQ==",
        "hasMore": true,
        "limit": 20
    }
}
```

## Configuration Management

- Never commit secrets to version control
- Use environment-specific configuration files
- Validate configuration at startup
- Fail fast on invalid configuration
- Use typed configuration objects

## Testing

### Test Pyramid

- **Unit tests** (70%): Test individual classes in isolation
- **Integration tests** (20%): Test layer interactions with real dependencies
- **End-to-end tests** (10%): Test complete user flows

### Testing Guidelines

- Test one behavior per test
- Use descriptive test names that explain the scenario
- Follow Arrange-Act-Assert pattern
- Mock external dependencies
- Test edge cases and error conditions

## Documentation

- Document public interfaces thoroughly
- Explain "why" not "what" in comments
- Keep comments up to date with code
- Generate API docs from code (OpenAPI/Swagger)
- Document key design decisions (ADRs)

## Git and Version Control

### Commit Messages

Use conventional commits:

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branch Strategy

- `main`: Production-ready code
- `feature/*`: New features
- `fix/*`: Bug fixes

## Code Quality Philosophy

- **Quality over speed**: Prioritize quality and thoughtful design over speed of iteration
- **No deprecation**: Never deprecate methods or fields. Apply the full migration/fix even if it's breaking.
- **Complete refactoring**: When making architectural changes, update ALL affected code across all layers.
- **Clean breaks**: If an API or interface needs to change, change it completely.
- **Boy scout rule**: Leave code better than you found it.
- **YAGNI**: Don't build features you don't need yet.

