# Claude Code Templates

## What is this?
A generator for CLAUDE.md templates. These templates provide Claude Code with architectural guidelines, coding standards, and development workflows that produce consistent, maintainable, production-quality code. Instead of repeating the same instructions across projects, generate a custom template, ask Claude to contextualize it, and let then let it follow established best practices.

## Templates

| Template | Description |
|----------|-------------|
| `templates/CLAUDE-base.md` | Language-agnostic foundation covering clean architecture, API-first design, plugin systems, testing, and quality gates |
| `templates/java/CLAUDE-autonomous-api-first-design.md` | Extends base with autonomous execution mode — Claude works without pausing for confirmation |
| `templates/java/spring-boot/CLAUDE-java-spring-boot.md` | Java/Spring Boot specific with JPA patterns, provider architecture, and Maven workflows |

Templates can extend each other. Use `prompt-merge.py go` to combine a base template with extensions into a single file.

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
