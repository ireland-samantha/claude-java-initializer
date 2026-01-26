# Claude Code Guidelines: Laravel

> **Extends:** [CLAUDE-php.md](../CLAUDE-php.md)

## Laravel Patterns

### Project Structure

```
app/
├── Console/
├── Exceptions/
├── Http/
│   ├── Controllers/
│   ├── Middleware/
│   ├── Requests/
│   └── Resources/
├── Models/
├── Policies/
├── Providers/
├── Services/
├── Repositories/
├── Actions/                  # Single-purpose action classes
└── DTOs/
config/
database/
├── factories/
├── migrations/
└── seeders/
routes/
tests/
├── Feature/
└── Unit/
```

### Controllers

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Http\Requests\CreateUserRequest;
use App\Http\Requests\UpdateUserRequest;
use App\Http\Resources\UserResource;
use App\Http\Resources\UserCollection;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Response;

final class UserController extends Controller
{
    public function __construct(
        private readonly UserService $userService,
    ) {}

    public function index(): UserCollection
    {
        $users = $this->userService->paginate();

        return new UserCollection($users);
    }

    public function show(string $id): UserResource
    {
        $user = $this->userService->findOrFail($id);

        return new UserResource($user);
    }

    public function store(CreateUserRequest $request): JsonResponse
    {
        $user = $this->userService->create($request->validated());

        return (new UserResource($user))
            ->response()
            ->setStatusCode(Response::HTTP_CREATED);
    }

    public function update(UpdateUserRequest $request, string $id): UserResource
    {
        $user = $this->userService->update($id, $request->validated());

        return new UserResource($user);
    }

    public function destroy(string $id): Response
    {
        $this->userService->delete($id);

        return response()->noContent();
    }
}
```

### Form Requests

```php
<?php

declare(strict_types=1);

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rules\Password;

final class CreateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    /** @return array<string, array<int, mixed>> */
    public function rules(): array
    {
        return [
            'email' => ['required', 'email', 'unique:users,email'],
            'name' => ['required', 'string', 'min:2', 'max:100'],
            'password' => ['required', Password::min(8)->mixedCase()->numbers()],
        ];
    }

    /** @return array<string, string> */
    public function messages(): array
    {
        return [
            'email.unique' => 'This email address is already registered.',
        ];
    }
}
```

### API Resources

```php
<?php

declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin \App\Models\User */
final class UserResource extends JsonResource
{
    /** @return array<string, mixed> */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'email' => $this->email,
            'name' => $this->name,
            'createdAt' => $this->created_at->toIso8601String(),
            'profile' => new ProfileResource($this->whenLoaded('profile')),
        ];
    }
}
```

### Services

```php
<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\User;
use App\Repositories\UserRepositoryInterface;
use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Support\Facades\Hash;

final class UserService
{
    public function __construct(
        private readonly UserRepositoryInterface $repository,
    ) {}

    public function paginate(int $perPage = 20): LengthAwarePaginator
    {
        return $this->repository->paginate($perPage);
    }

    public function findOrFail(string $id): User
    {
        return $this->repository->findOrFail($id);
    }

    /** @param array<string, mixed> $data */
    public function create(array $data): User
    {
        $data['password'] = Hash::make($data['password']);

        return $this->repository->create($data);
    }

    /** @param array<string, mixed> $data */
    public function update(string $id, array $data): User
    {
        $user = $this->repository->findOrFail($id);

        if (isset($data['password'])) {
            $data['password'] = Hash::make($data['password']);
        }

        return $this->repository->update($user, $data);
    }

    public function delete(string $id): void
    {
        $user = $this->repository->findOrFail($id);
        $this->repository->delete($user);
    }
}
```

### Repositories

```php
<?php

declare(strict_types=1);

namespace App\Repositories;

use App\Models\User;
use Illuminate\Pagination\LengthAwarePaginator;

interface UserRepositoryInterface
{
    public function paginate(int $perPage = 20): LengthAwarePaginator;
    public function findOrFail(string $id): User;
    public function findByEmail(string $email): ?User;
    /** @param array<string, mixed> $data */
    public function create(array $data): User;
    /** @param array<string, mixed> $data */
    public function update(User $user, array $data): User;
    public function delete(User $user): void;
}

final class EloquentUserRepository implements UserRepositoryInterface
{
    public function paginate(int $perPage = 20): LengthAwarePaginator
    {
        return User::query()
            ->latest()
            ->paginate($perPage);
    }

    public function findOrFail(string $id): User
    {
        return User::findOrFail($id);
    }

    public function findByEmail(string $email): ?User
    {
        return User::where('email', $email)->first();
    }

    /** @param array<string, mixed> $data */
    public function create(array $data): User
    {
        return User::create($data);
    }

    /** @param array<string, mixed> $data */
    public function update(User $user, array $data): User
    {
        $user->update($data);
        return $user->fresh();
    }

    public function delete(User $user): void
    {
        $user->delete();
    }
}
```

### Models

```php
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

final class User extends Authenticatable
{
    use HasFactory, HasUuids, Notifiable;

    /** @var list<string> */
    protected $fillable = [
        'name',
        'email',
        'password',
    ];

    /** @var list<string> */
    protected $hidden = [
        'password',
        'remember_token',
    ];

    /** @return array<string, string> */
    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
        ];
    }

    public function profile(): HasOne
    {
        return $this->hasOne(Profile::class);
    }

    public function posts(): HasMany
    {
        return $this->hasMany(Post::class);
    }
}
```

### Actions

```php
<?php

declare(strict_types=1);

namespace App\Actions;

use App\Models\User;
use App\Notifications\WelcomeNotification;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

final class CreateUserAction
{
    /** @param array<string, mixed> $data */
    public function execute(array $data): User
    {
        return DB::transaction(function () use ($data) {
            $user = User::create([
                'name' => $data['name'],
                'email' => $data['email'],
                'password' => Hash::make($data['password']),
            ]);

            $user->profile()->create([
                'bio' => $data['bio'] ?? null,
            ]);

            $user->notify(new WelcomeNotification());

            return $user;
        });
    }
}
```

### Middleware

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Symfony\Component\HttpFoundation\Response;

final class AddCorrelationId
{
    public function handle(Request $request, Closure $next): Response
    {
        $correlationId = $request->header('X-Correlation-ID')
            ?? Str::uuid()->toString();

        $request->headers->set('X-Correlation-ID', $correlationId);

        /** @var Response $response */
        $response = $next($request);

        $response->headers->set('X-Correlation-ID', $correlationId);

        return $response;
    }
}
```

### Exception Handling

```php
<?php

declare(strict_types=1);

namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Illuminate\Http\JsonResponse;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Throwable;

final class Handler extends ExceptionHandler
{
    public function render($request, Throwable $e): JsonResponse
    {
        if ($request->expectsJson()) {
            return $this->handleApiException($e);
        }

        return parent::render($request, $e);
    }

    private function handleApiException(Throwable $e): JsonResponse
    {
        return match (true) {
            $e instanceof ValidationException => response()->json([
                'message' => 'Validation failed',
                'errors' => $e->errors(),
            ], 422),
            $e instanceof HttpException => response()->json([
                'message' => $e->getMessage(),
            ], $e->getStatusCode()),
            default => response()->json([
                'message' => 'Internal server error',
            ], 500),
        };
    }
}
```

## Testing

```php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

final class UserControllerTest extends TestCase
{
    use RefreshDatabase;

    public function test_can_list_users(): void
    {
        User::factory()->count(3)->create();
        $user = User::factory()->create();

        $response = $this->actingAs($user)
            ->getJson('/api/users');

        $response->assertOk()
            ->assertJsonCount(4, 'data');
    }

    public function test_can_create_user(): void
    {
        $admin = User::factory()->create();

        $response = $this->actingAs($admin)
            ->postJson('/api/users', [
                'name' => 'Test User',
                'email' => 'test@example.com',
                'password' => 'Password123',
            ]);

        $response->assertCreated()
            ->assertJsonPath('data.email', 'test@example.com');

        $this->assertDatabaseHas('users', [
            'email' => 'test@example.com',
        ]);
    }

    public function test_cannot_create_user_with_duplicate_email(): void
    {
        User::factory()->create(['email' => 'existing@example.com']);
        $admin = User::factory()->create();

        $response = $this->actingAs($admin)
            ->postJson('/api/users', [
                'name' => 'Test User',
                'email' => 'existing@example.com',
                'password' => 'Password123',
            ]);

        $response->assertUnprocessable()
            ->assertJsonValidationErrors(['email']);
    }
}
```
