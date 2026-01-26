# Claude Code Guidelines: Autonomous API-First Extension

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)
>
> This extension adds autonomous operating mode for API-first development. All principles from the base guidelines apply.

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

## Additional Extension Points

In addition to the standard extension points from the base guidelines, always design these as pluggable:

- **AI Backend**: OpenAI, Anthropic, Ollama, etc.

## Additional Patterns

### Inversion of Control Examples

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
