# Claude Code Templates

A collection of `CLAUDE.md` templates for AI-driven development with Claude Code.

## What is this?

These templates provide Claude Code with architectural guidelines, coding standards, and development workflows that produce consistent, maintainable, production-quality code. Instead of repeating the same instructions across projects, drop in a template and let Claude follow established best practices.

## Templates

| Template | Description |
|----------|-------------|
| `CLAUDE-base.md` | Language-agnostic foundation covering clean architecture, API-first design, plugin systems, testing, and quality gates |
| `CLAUDE-java-spring.md` | Java/Spring Boot specific with JPA patterns, provider architecture, and Maven workflows |
| *More coming soon* | |

## Usage

1. **Choose a template** that matches your stack or start with `CLAUDE-base.md`
2. **Give it to Claude** with your project context:
```
   Here's a CLAUDE.md template I'd like to use. Please review my project 
   structure and contextualize this template for my specific codebase, 
   then update my CLAUDE.md.
```
3. **Iterate** as your project evolves by asking Claude to update the file after learning something or making mistakes.

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
