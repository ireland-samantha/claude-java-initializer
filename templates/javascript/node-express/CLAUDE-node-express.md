# Claude Code Guidelines: Node.js Express

> **Extends:** [CLAUDE-javascript.md](../CLAUDE-javascript.md)

## Express Patterns

### Application Structure

```
src/
├── index.ts              # Entry point
├── app.ts                # Express app setup
├── config/               # Configuration
├── routes/               # Route definitions
├── controllers/          # Request handlers
├── services/             # Business logic
├── repositories/         # Data access
├── middleware/           # Custom middleware
├── models/               # Domain models
├── dto/                  # Request/response DTOs
├── errors/               # Custom errors
├── utils/                # Utilities
└── types/                # TypeScript types
```

### Route Organization

- Group routes by resource
- Use Router for modular routing
- Keep route files thin — delegate to controllers

```typescript
// routes/users.ts
import { Router } from 'express';
import { UserController } from '../controllers/user.controller';

const router = Router();
const controller = new UserController();

router.get('/', controller.list);
router.get('/:id', controller.getById);
router.post('/', controller.create);
router.put('/:id', controller.update);
router.delete('/:id', controller.delete);

export default router;
```

### Controllers

- Handle HTTP concerns only
- Validate request, call service, format response
- Use async handlers with error wrapper

```typescript
export class UserController {
  constructor(private userService = new UserService()) {}

  list = asyncHandler(async (req: Request, res: Response) => {
    const { page, limit } = req.query;
    const users = await this.userService.list({ page: Number(page), limit: Number(limit) });
    res.json(users);
  });

  getById = asyncHandler(async (req: Request, res: Response) => {
    const user = await this.userService.getById(req.params.id);
    res.json(user);
  });

  create = asyncHandler(async (req: Request, res: Response) => {
    const dto = plainToInstance(CreateUserDto, req.body);
    await validateOrReject(dto);
    const user = await this.userService.create(dto);
    res.status(201).json(user);
  });
}
```

### Async Handler Wrapper

```typescript
type AsyncHandler = (req: Request, res: Response, next: NextFunction) => Promise<void>;

export function asyncHandler(fn: AsyncHandler) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
```

### Middleware

- Use middleware for cross-cutting concerns
- Order matters: auth before validation before handler
- Keep middleware focused and composable

```typescript
// Authentication middleware
export function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    throw new UnauthorizedError('No token provided');
  }

  try {
    const payload = jwt.verify(token, config.jwtSecret);
    req.user = payload as AuthUser;
    next();
  } catch {
    throw new UnauthorizedError('Invalid token');
  }
}

// Request logging middleware
export function requestLogger(req: Request, res: Response, next: NextFunction) {
  const start = Date.now();

  res.on('finish', () => {
    logger.info({
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration: Date.now() - start,
      correlationId: req.correlationId,
    });
  });

  next();
}
```

### Error Handling

- Create custom error classes with status codes
- Use global error handler middleware
- Never expose stack traces in production

```typescript
// Custom errors
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code: string,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} with ID ${id} not found`, 404, 'NOT_FOUND');
  }
}

// Global error handler (must be last middleware)
export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  const correlationId = req.correlationId;

  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      code: err.code,
      message: err.message,
      correlationId,
    });
  }

  logger.error({ err, correlationId });

  res.status(500).json({
    code: 'INTERNAL_ERROR',
    message: 'An unexpected error occurred',
    correlationId,
  });
}
```

### Validation

- Use class-validator and class-transformer
- Validate DTOs at controller level
- Return all validation errors at once

```typescript
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(2)
  name: string;

  @IsString()
  @MinLength(8)
  password: string;
}
```

### Configuration

- Use environment variables
- Validate config at startup
- Type configuration object

```typescript
interface Config {
  port: number;
  nodeEnv: 'development' | 'production' | 'test';
  database: {
    url: string;
    poolSize: number;
  };
  jwt: {
    secret: string;
    expiresIn: string;
  };
}

export const config: Config = {
  port: parseInt(process.env.PORT || '3000', 10),
  nodeEnv: process.env.NODE_ENV as Config['nodeEnv'] || 'development',
  database: {
    url: requireEnv('DATABASE_URL'),
    poolSize: parseInt(process.env.DB_POOL_SIZE || '10', 10),
  },
  jwt: {
    secret: requireEnv('JWT_SECRET'),
    expiresIn: process.env.JWT_EXPIRES_IN || '1d',
  },
};

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var: ${name}`);
  return value;
}
```

### Security

- Use helmet for security headers
- Implement rate limiting
- Sanitize user input
- Use CORS appropriately

```typescript
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import cors from 'cors';

app.use(helmet());
app.use(cors({ origin: config.corsOrigins }));
app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  standardHeaders: true,
}));
```

## Testing

```typescript
import request from 'supertest';
import { app } from '../app';

describe('GET /api/users/:id', () => {
  it('should return user when found', async () => {
    const response = await request(app)
      .get('/api/users/123')
      .set('Authorization', `Bearer ${validToken}`)
      .expect(200);

    expect(response.body).toMatchObject({ id: '123' });
  });

  it('should return 404 when not found', async () => {
    await request(app)
      .get('/api/users/nonexistent')
      .set('Authorization', `Bearer ${validToken}`)
      .expect(404);
  });
});
```
