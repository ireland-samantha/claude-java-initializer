# Claude Code Guidelines: JavaScript/TypeScript

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **TypeScript preferred** over JavaScript for all new code
- **Strict mode** enabled: `"strict": true` in tsconfig.json
- **ES Modules** over CommonJS: use `import/export`, not `require/module.exports`
- **Node.js 18+** for modern features (native fetch, test runner)

## TypeScript Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true
  }
}
```

## Code Style

### Naming Conventions

- `camelCase` for variables, functions, methods
- `PascalCase` for classes, interfaces, types, enums
- `SCREAMING_SNAKE_CASE` for constants
- Prefix interfaces with `I` only if distinguishing from implementation class

### Type Definitions

- Prefer `interface` over `type` for object shapes (better error messages, extendable)
- Use `type` for unions, intersections, and mapped types
- Avoid `any` — use `unknown` and narrow with type guards
- Use `readonly` for immutable properties
- Use `as const` for literal types

```typescript
// Prefer
interface User {
  readonly id: string;
  name: string;
  role: 'admin' | 'user';
}

// Avoid
type User = {
  id: any;
  name: string;
  role: string;
}
```

### Functions

- Use arrow functions for callbacks and inline functions
- Use function declarations for top-level functions (hoisting, better stack traces)
- Always specify return types for public functions
- Use `async/await` over raw Promises

```typescript
// Public function - explicit return type
function createUser(data: CreateUserDto): Promise<User> {
  return userRepository.save(data);
}

// Callback - arrow function
users.filter((user) => user.isActive);
```

### Null Handling

- Use `null` for intentional absence, `undefined` for unset
- Use optional chaining: `user?.profile?.name`
- Use nullish coalescing: `value ?? defaultValue`
- Avoid non-null assertions (`!`) — narrow types properly instead

## Error Handling

- Create custom error classes extending `Error`
- Always set `Error.captureStackTrace` in custom errors
- Use discriminated unions for Result types when appropriate

```typescript
class NotFoundError extends Error {
  constructor(resource: string, id: string) {
    super(`${resource} with ID ${id} not found`);
    this.name = 'NotFoundError';
    Error.captureStackTrace(this, this.constructor);
  }
}
```

## Async Patterns

- Always handle Promise rejections
- Use `Promise.all` for concurrent independent operations
- Use `Promise.allSettled` when partial failures are acceptable
- Implement proper cancellation with AbortController

```typescript
async function fetchUserData(userId: string, signal?: AbortSignal) {
  const [profile, preferences] = await Promise.all([
    fetchProfile(userId, { signal }),
    fetchPreferences(userId, { signal }),
  ]);
  return { profile, preferences };
}
```

## Module Structure

```
src/
├── index.ts              # Public API exports
├── types/                # Shared type definitions
├── utils/                # Pure utility functions
├── services/             # Business logic
├── repositories/         # Data access
└── errors/               # Custom error classes
```

## Testing

- Use native Node.js test runner or Vitest
- Use `describe`/`it` for test organization
- Mock external dependencies, not internal modules
- Test edge cases: empty arrays, null values, boundary conditions

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('UserService', () => {
  it('should create user with valid data', async () => {
    const user = await userService.create(validUserData);
    expect(user.id).toBeDefined();
  });
});
```

## Package Management

- Use `pnpm` or `npm` with lockfile committed
- Pin exact versions for production dependencies
- Use `^` ranges for dev dependencies
- Audit dependencies regularly: `npm audit`

## Build and Bundle

- Use `esbuild` or `swc` for fast builds
- Tree-shake unused code
- Generate source maps for production debugging
- Target appropriate ES version for runtime environment
