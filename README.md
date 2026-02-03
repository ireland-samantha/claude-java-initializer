# Claude Code Java Initializer

## What is this?

A handful of CLAUDE.md files I give to new Java projects + a script to combine them 

## Why?

To set expectations from the start with Claude from well-known principles, and then add project context later.

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
In your codebase directory, give Claude the the CLAUDE.md file and ask it to contextualize for the project:

```
   Here's a CLAUDE.md template I'd like to use. Please review my project
   structure and contextualize this template within my specific codebase,
   then update my CLAUDE.md.
```
### 3. Evolve the file
As your project evolves, ask Claude to update the file after learning something or making mistakes.


## Templates

| Template | Description |
|----------|-------------|
| `CLAUDE-base.md` | Language-agnostic foundation: clean architecture, API-first design, plugin systems, testing, quality gates |
| `java/CLAUDE-java.md` | Java 21+, records, sealed classes, virtual threads, pattern matching |
| `java/CLAUDE-autonomous-api-first-design.md` | Autonomous execution mode — Claude works without pausing for confirmation |
| `java/spring-boot/CLAUDE-java-spring-boot.md` | Spring Boot, JPA, provider architecture, Maven workflows |

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


## License

MIT — Use this however you want (just not for evil tho)
