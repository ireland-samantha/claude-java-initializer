# Claude Code Templates

## What is this?
tl;dr A generator for customizable CLAUDE.md templates to encourage Claude to produce higher-quality code.

These templates provide Claude Code with architectural guidelines, coding standards, and development workflows that produce consistent, maintainable, production-quality code. Instead of repeating the same instructions across projects, generate a custom template, ask Claude to contextualize it, and let then let it follow established best practices.

## Templates

### Base
| Template | Description |
|----------|-------------|
| `CLAUDE-base.md` | Language-agnostic foundation: clean architecture, API-first design, plugin systems, testing, quality gates |

### JavaScript / TypeScript
| Template | Description |
|----------|-------------|
| `javascript/CLAUDE-javascript.md` | TypeScript-first patterns, async/await, error handling, ES modules |
| `javascript/react/CLAUDE-react.md` | Functional components, hooks, React Query, Testing Library |
| `javascript/vue/CLAUDE-vue.md` | Composition API, Pinia, Vue Router, Vue Test Utils |
| `javascript/angular/CLAUDE-angular.md` | Standalone components, signals, RxJS, dependency injection |
| `javascript/nextjs/CLAUDE-nextjs.md` | App Router, Server Components, Server Actions, middleware |
| `javascript/nestjs/CLAUDE-nestjs.md` | Modules, decorators, guards, interceptors, TypeORM |
| `javascript/node-express/CLAUDE-node-express.md` | Express patterns, middleware, async handlers, validation |

### Python
| Template | Description |
|----------|-------------|
| `python/CLAUDE-python.md` | Type hints, dataclasses, Pydantic, async patterns, pytest |
| `python/django/CLAUDE-django.md` | DRF, services/selectors pattern, ORM, serializers |
| `python/flask/CLAUDE-flask.md` | Blueprints, SQLAlchemy, Marshmallow, application factory |
| `python/fastapi/CLAUDE-fastapi.md` | Async endpoints, Pydantic v2, dependency injection, OpenAPI |

### Java
| Template | Description |
|----------|-------------|
| `java/CLAUDE-java.md` | Java 21+, records, sealed classes, virtual threads, pattern matching |
| `java/CLAUDE-autonomous-api-first-design.md` | Autonomous execution mode — Claude works without pausing for confirmation |
| `java/spring-boot/CLAUDE-java-spring-boot.md` | Spring Boot, JPA, provider architecture, Maven workflows |

### C# / .NET
| Template | Description |
|----------|-------------|
| `csharp/CLAUDE-csharp.md` | .NET 8+, C# 12, records, nullable reference types, EF Core |
| `csharp/aspnet-core/CLAUDE-aspnet-core.md` | Minimal APIs, middleware, health checks, output caching |

### Go
| Template | Description |
|----------|-------------|
| `go/CLAUDE-go.md` | Interfaces, error handling, concurrency, context, testing |

### Rust
| Template | Description |
|----------|-------------|
| `rust/CLAUDE-rust.md` | Ownership, traits, async/await, Axum, error handling with thiserror |

### C++
| Template | Description |
|----------|-------------|
| `cpp/CLAUDE-cpp.md` | C++20, RAII, smart pointers, concepts, ranges, CMake |

### PHP
| Template | Description |
|----------|-------------|
| `php/CLAUDE-php.md` | PHP 8.2+, strict types, enums, readonly classes, Composer |
| `php/laravel/CLAUDE-laravel.md` | Eloquent, service classes, form requests, policies, jobs |

### Ruby
| Template | Description |
|----------|-------------|
| `ruby/CLAUDE-ruby.md` | Ruby 3.2+, pattern matching, Data class, RSpec |
| `ruby/rails/CLAUDE-rails.md` | Services, query objects, serializers, Pundit, RSpec |

### Swift
| Template | Description |
|----------|-------------|
| `swift/CLAUDE-swift.md` | Swift 5.9+, actors, async/await, SwiftUI, Codable |

### Kotlin
| Template | Description |
|----------|-------------|
| `kotlin/CLAUDE-kotlin.md` | Coroutines, Flow, sealed classes, extension functions, Kotest |

---

Templates extend each other (e.g., `react` extends `javascript` extends `base`). Use `prompt-merge.py` to combine templates into a single file.

## Quick Start

### 1. Create template with prompt-merge.py

The `prompt-merge.py` script lets you interactively select and combine templates:

```bash
# Interactive selection — merge multiple templates into one CLAUDE.md
./prompt-merge.py

# List all available templates
./prompt-merge.py --list

# Output to a custom path
./prompt-merge.py -o /path/to/your/project/CLAUDE.md
```

The interactive mode uses arrow keys or j/k to navigate, SPACE to toggle selection, and ENTER to confirm.

### 2. Contextualize with Claude
```
   Here's a CLAUDE.md template I'd like to use. Please review my project
   structure and contextualize this template within my specific codebase,
   then update my CLAUDE.md.
```
### 3. **Iterate** as your project evolves by asking Claude to update the file after learning something or making mistakes.

## What's Inside

These templates encode practices for:

- **API-first development** — Design contracts before implementation
- **Clean architecture** — Separation of concerns, dependency rules, layer responsibilities
- **Plugin systems** — IoC, extension points, composition over inheritance
- **Error handling** — Exception hierarchies, validation layers, structured error responses
- **Observability** — Structured logging, health checks, metrics
- **Security** — Input validation, authentication patterns, data protection
- **Resilience** — Retry strategies, circuit breakers, graceful degradation
- **Testing** — Test pyramid, integration testing, quality gates
- **Autonomous workflows** — Let Claude execute without hand-holding, intervene when needed

## Philosophy

These templates optimize for:

1. **Autonomous execution** — Claude works independently, you intervene only when needed
2. **Production quality** — Code that's ready for real users, not just demos
3. **Maintainability** — Clean architecture that scales with your team
4. **Extensibility** — Plugin-oriented design that adapts to changing requirements

## Contributing

Found something that makes Claude produce better code? PRs welcome.

## License

MIT — Use these however you like (just not for evil tho)
