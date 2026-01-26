# Claude Code Guidelines

A production-grade software development guide for building modular, maintainable, and extensible systems.

## Development Approach: API-First (Autonomous Mode)

When building new features, follow API-first design principles autonomously. Do not wait for approval at each step—execute the full implementation unless I intervene.

### Autonomous Workflow

1. **Design the contract first** - Define interfaces with full documentation
2. **Define data models** - Request/response shapes, validation, entities
3. **Define exceptions** - Custom exceptions for all failure modes
4. **Implement** - Build all layers top-to-bottom
5. **Write tests** - Unit tests, integration tests
6. **Run build** - Build must pass before declaring done

Execute all steps without pausing for confirmation. I trust you to make good decisions.

### When I Intervene

If I say "stop", "wait", "hold on", or express concern about direction:
- Immediately stop what you're doing
- Do not commit or continue the current approach
- Explain your current plan and reasoning
- Wait for my feedback before proceeding

### Handling Ambiguity

When requirements are unclear:
- Make a reasonable assumption and document it
- Prefer the simpler solution
- Flag the assumption in your response so I can correct if needed

### Decision Documentation

When making non-obvious architectural decisions, document the rationale:
- In code: `// Decision: Using X because Y`
- In commits: Note trade-offs considered

## Core Principles

1. **Separation of Concerns (SoC)**: Each class/module has one clear responsibility. Don't mix HTTP handling with business logic, or persistence with domain rules.

2. **Single Responsibility Principle (SRP)**: A class should have only one reason to change. Split classes that do too much.

3. **Dependency Injection (DI)**: All dependencies are injected via constructor. No `new` for services/repositories. This enables testing and swapping implementations.

4. **Interface Segregation**: Depend on abstractions (interfaces), not concretions.

5. **Clean Architecture Layers**:
   - **Domain**: Pure business objects, no framework dependencies
   - **Application**: Business logic orchestration, depends only on domain and repository interfaces
   - **Infrastructure**: Framework-specific implementations

6. **API-First Design**: Define contracts before implementation

## Architecture Guidelines

- Extract interfaces for services and repositories to allow for testability and different implementations
- Decouple from frameworks via interfaces - framework annotations should only appear on implementation classes, never on interfaces
- Business logic should be defined in interfaces; framework-specific behavior belongs in implementations
- Keep classes small and focused - if a class exceeds ~200 lines, consider splitting
- Prefer composition over inheritance

## Package Structure

Organize code by clean architecture with provider-based implementations:
```
project/
├── core/                       # Cross-cutting plugin interfaces and shared models
│   ├── ai/
│   │   ├── AiBackend
│   │   ├── AiRequest
│   │   └── AiResponse
│   └── notification/
│       └── NotificationPublisher
│
├── {component}/                # Domain-specific modules
│   ├── dto/                    # Data Transfer Objects
│   ├── exception/              # Custom exceptions
│   ├── model/                  # Domain models and enums
│   ├── repository/             # Repository INTERFACES
│   ├── service/                # Service interfaces AND implementations
│   └── mapper/                 # DTO ↔ Domain model mappers
│
└── provider/                   # Infrastructure implementations
    ├── http/{component}/
    │   └── controller/         # HTTP controllers only
    ├── database/{component}/
    │   ├── repository/         # Database entities and repository implementations
    │   └── mapper/             # Entity ↔ Domain model mappers
    └── {plugin-name}/          # Plugin implementations
        └── PluginImplementation
```

**Key principles:**

- **Core**: Cross-cutting plugin interfaces and shared domain models. No framework dependencies.
- **Domain layer** (`{component}/`): Domain-specific interfaces, models, DTOs, and service implementations. No framework dependencies except validation annotations.
- **Provider layer** (`provider/`): Framework-specific implementations. Controllers, repositories, and plugin implementations.

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
- **Services**: Business logic operating on domain models. Never import from `dto/` packages. Return domain models.
- **Repository interfaces**: Define persistence contract using domain models (not entities)
- **Repository implementations**: Handle entity ↔ domain model conversion internally

**Why this matters:**

- Services are testable without HTTP concerns
- Domain models are the single source of truth
- DTOs can evolve independently (API versioning)
- Clear separation prevents leaky abstractions

## Dependency Rules
```
Controllers → Services (via interface) → Repositories (via interface)
     ↓              ↓                           ↓
   DTOs        Domain Models              Domain Models

Repository Impl → Entities (internal only, never exposed)
```

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

### Inversion of Control (IoC) Principles

Depend on abstractions, never concretions:
```
// WRONG - coupled to implementation
class WorkflowExecutor {
    private aiClient = new OpenAiClient()
}

// RIGHT - depends on abstraction
class WorkflowExecutor {
    constructor(private aiBackend: AiBackend) {}
}
```

Interfaces define capabilities, not implementations:
```
interface AiBackend {
    /**
     * Sends a prompt to the AI backend and returns the response.
     */
    complete(request: AiRequest): AiResponse
}
```

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

- AI Backend: OpenAI, Anthropic, Ollama, etc.
- Persistence: Postgres, MongoDB, etc.
- Notifications: Webhook, message queue, etc.
- Task Execution: Local, distributed, etc.
- Authentication: JWT, API key, OAuth, etc.
- Rate Limiting: In-memory, Redis, etc.
- Caching: In-memory, Redis, etc.
- File Storage: Local, S3, GCS, etc.

### Composition Over Inheritance

Combine behaviors through composition:
```
class CompositeNotificationPublisher implements NotificationPublisher {
    constructor(private publishers: NotificationPublisher[]) {}
    
    publish(notification: Notification) {
        this.publishers.forEach(p => p.publish(notification))
    }
}

class RetryingAiBackend implements AiBackend {
    constructor(
        private delegate: AiBackend,
        private retryStrategy: RetryStrategy
    ) {}
    
    complete(request: AiRequest): AiResponse {
        return this.retryStrategy.execute(() => this.delegate.complete(request))
    }
}
```

### Registry Pattern for Dynamic Plugins

For runtime-discoverable plugins:
```
interface PluginRegistry<T> {
    register(key: string, plugin: T): void
    get(key: string): T
    getAll(): T[]
}
```

## Contract Design Principles

- Interfaces are the source of truth, not implementations
- Method signatures should be self-documenting
- Complete documentation on all public methods: purpose, parameters, return value, exceptions
- Explicit failure modes with custom exceptions
- Design for the consumer, not the implementation

## Error Handling

### Exception Hierarchy

Define a consistent exception hierarchy:
```
BaseException
├── ValidationException        # Invalid input from client (400)
├── NotFoundException          # Resource not found (404)
├── ConflictException          # State conflict, duplicate, etc. (409)
├── AuthenticationException    # Identity unknown (401)
├── AuthorizationException     # Identity known, access denied (403)
├── RateLimitException         # Too many requests (429)
├── ExternalServiceException   # Third-party failure (502)
└── InternalException          # Unexpected errors (500)
```

### Exception Guidelines

- Custom exceptions per domain in `{component}/exception/`
- Service interfaces declare exceptions in documentation
- Controllers translate to HTTP status codes via global exception handler
- Never leak implementation details in error responses
- Include correlation IDs for tracing
- Log full stack traces server-side, return safe messages client-side

### Standard Error Response
```json
{
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow with ID x not found",
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

### Validation Response
```json
{
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
        "errors": [
            { "field": "email", "message": "Invalid email format" },
            { "field": "age", "message": "Must be at least 18" }
        ]
    }
}
```

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

### Structured Log Format
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "correlationId": "abc-123-def",
    "service": "workflow-service",
    "event": "workflow.started",
    "workflowId": "xyz-789",
    "duration_ms": 150
}
```

### Metrics

Expose metrics for:
- Request rate, latency, and error rate (RED metrics)
- Resource utilization (CPU, memory, connections)
- Business metrics (workflows created, tasks completed)
- Dependency health (database, cache, external APIs)

### Health Checks

Implement health check endpoints:
- `/health/live`: Is the process running?
- `/health/ready`: Is the service ready to accept traffic?
- Include dependency checks (database, cache, message queue)

## Security

### Authentication and Authorization

- Authenticate at the edge (API gateway or controller layer)
- Authorize at the service layer
- Use principle of least privilege
- Implement proper session management
- Support API keys for service-to-service communication

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

### Security Headers

Include appropriate security headers:
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security`

## Performance and Scalability

### Database Performance

- Use connection pooling with appropriate limits
- Add indexes for frequently queried fields
- Use pagination for list endpoints (cursor-based preferred)
- Avoid N+1 queries
- Use read replicas for read-heavy workloads
- Consider caching for frequently accessed, rarely changed data

### Caching Strategy

- Cache at the appropriate layer (HTTP, application, database)
- Use cache-aside pattern for application caching
- Set appropriate TTLs
- Implement cache invalidation strategy
- Monitor cache hit rates

### Async Processing

- Use message queues for long-running operations
- Implement idempotency for message handlers
- Use dead letter queues for failed messages
- Design for at-least-once delivery
- Include correlation IDs in messages

### Resource Limits

- Set timeouts on all external calls
- Implement circuit breakers for external dependencies
- Use bulkheads to isolate failures
- Configure appropriate thread pool sizes
- Set memory limits and monitor usage

## Resilience

### Retry Strategy

- Use exponential backoff with jitter
- Set maximum retry attempts
- Only retry idempotent operations
- Only retry transient failures (network, timeout, 5xx)
- Don't retry client errors (4xx)

### Circuit Breaker

Implement circuit breakers for external dependencies:
- **Closed**: Normal operation, requests flow through
- **Open**: Dependency unhealthy, fail fast
- **Half-open**: Testing if dependency recovered

### Graceful Degradation

- Design fallback behaviors for non-critical features
- Return cached data when source unavailable
- Disable features rather than fail entirely
- Communicate degraded state to users

### Idempotency

- Make write operations idempotent where possible
- Use idempotency keys for critical operations
- Store operation results for deduplication
- Handle duplicate requests gracefully

## API Design

### REST Guidelines

- Use nouns for resources, verbs come from HTTP methods
- Use plural names for collections (`/workflows`, not `/workflow`)
- Use kebab-case for URLs (`/workflow-runs`)
- Use camelCase for JSON properties
- Return appropriate HTTP status codes
- Use `Location` header for created resources
- Support `ETag` and `If-None-Match` for caching

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
- `502 Bad Gateway`: Upstream service error
- `503 Service Unavailable`: Temporary unavailability

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

### Versioning

- Use URL path versioning (`/v1/workflows`)
- Maintain backward compatibility within a version
- Document breaking changes clearly
- Support at most two versions simultaneously

### Rate Limiting

Return rate limit headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Window reset timestamp

## Configuration Management

### Configuration Hierarchy

1. Defaults in code
2. Configuration files
3. Environment variables (override files)
4. Runtime configuration (feature flags)

### Configuration Guidelines

- Never commit secrets to version control
- Use environment-specific configuration files
- Validate configuration at startup
- Fail fast on invalid configuration
- Document all configuration options
- Use typed configuration objects

### Feature Flags

- Use feature flags for gradual rollouts
- Clean up flags after full rollout
- Log flag evaluations for debugging
- Support user/tenant-specific flags

## Testing

### Test Pyramid

- **Unit tests** (70%): Test individual classes in isolation
- **Integration tests** (20%): Test layer interactions with real dependencies
- **End-to-end tests** (10%): Test complete user flows

### Unit Testing Guidelines

- Test one behavior per test
- Use descriptive test names that explain the scenario
- Follow Arrange-Act-Assert pattern
- Mock external dependencies
- Test edge cases and error conditions
- Aim for high coverage of business logic

### Integration Testing Guidelines

- Use test containers for databases, message queues
- Test repository implementations against real database
- Test API endpoints with real HTTP
- Test message handlers with real queues
- Reset state between tests

### Test Data Management

- Use factories or builders for test data
- Don't share mutable state between tests
- Use realistic but anonymized data
- Clean up test data after tests

## Documentation

### Code Documentation

- Document public interfaces thoroughly
- Explain "why" not "what" in comments
- Keep comments up to date with code
- Use self-documenting code where possible

### API Documentation

- Generate API docs from code (OpenAPI/Swagger)
- Include request/response examples
- Document error responses
- Provide authentication instructions
- Keep documentation versioned with code

### Architecture Documentation

- Maintain high-level architecture diagrams
- Document key design decisions (ADRs)
- Keep README current with setup instructions
- Document operational runbooks

## Quality Gates (Self-Enforced)

Before declaring a feature complete, verify:

- [ ] Interface has complete documentation
- [ ] DTOs have validation
- [ ] Custom exceptions for all failure cases
- [ ] All layers implemented (controller → service → repository)
- [ ] New extension points are interface-based and pluggable
- [ ] Input validation at DTO and domain layers
- [ ] Error handling with appropriate status codes
- [ ] Logging with correlation IDs
- [ ] Unit tests for all classes (>80% coverage)
- [ ] Integration tests for persistence and API layers
- [ ] End-to-end test exists
- [ ] No security vulnerabilities (secrets, SQL injection, etc.)
- [ ] Performance considered (pagination, indexes, caching)
- [ ] Build passes
- [ ] Documentation updated

## Code Quality Philosophy

- **Quality over speed**: Prioritize quality and thoughtful design over speed of iteration
- **No deprecation**: Never deprecate methods or fields. Apply the full migration/fix even if it's breaking.
- **Complete refactoring**: When making architectural changes, update ALL affected code across all layers. Don't leave partial migrations or compatibility shims.
- **Clean breaks**: If an API or interface needs to change, change it completely. Don't add backwards-compatibility hacks.
- **Boy scout rule**: Leave code better than you found it.
- **YAGNI**: Don't build features you don't need yet. Build for today's requirements with tomorrow's extensibility.

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
- `release/*`: Release preparation

### Pull Request Guidelines

- Keep PRs small and focused
- Include description of changes and testing done
- Reference related issues
- Require passing CI and code review
- Squash commits on merge

## API Evolution

- Prefer additive changes over modifications
- When breaking changes are necessary, update all consumers in the same change
- No deprecation—apply the full migration
- Communicate breaking changes clearly in release notes
