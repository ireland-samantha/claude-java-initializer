# Claude Code Guidelines: PHP

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **PHP 8.2+** for modern features
- Follow **PSR-12** coding style
- Use **strict types**: `declare(strict_types=1);`
- Use **Composer** for dependency management

## Project Structure

```
project/
├── composer.json
├── composer.lock
├── public/
│   └── index.php           # Entry point
├── src/
│   ├── Controller/
│   ├── Service/
│   ├── Repository/
│   ├── Entity/
│   ├── DTO/
│   ├── Exception/
│   └── Kernel.php
├── config/
├── tests/
│   ├── Unit/
│   └── Integration/
└── var/
    ├── cache/
    └── log/
```

## Code Style

### Type Declarations

```php
<?php

declare(strict_types=1);

namespace App\Service;

use App\Entity\User;
use App\Repository\UserRepositoryInterface;
use App\DTO\CreateUserDTO;
use App\Exception\UserNotFoundException;

final class UserService
{
    public function __construct(
        private readonly UserRepositoryInterface $repository,
    ) {}

    public function findById(string $id): ?User
    {
        return $this->repository->findById($id);
    }

    public function findByIdOrFail(string $id): User
    {
        return $this->repository->findById($id)
            ?? throw new UserNotFoundException($id);
    }

    /**
     * @return list<User>
     */
    public function findAll(): array
    {
        return $this->repository->findAll();
    }
}
```

### Modern PHP Features

```php
<?php

declare(strict_types=1);

// Readonly classes (PHP 8.2)
readonly class UserDTO
{
    public function __construct(
        public string $id,
        public string $email,
        public string $name,
        public \DateTimeImmutable $createdAt,
    ) {}
}

// Enums (PHP 8.1)
enum UserStatus: string
{
    case Active = 'active';
    case Inactive = 'inactive';
    case Pending = 'pending';

    public function isActive(): bool
    {
        return $this === self::Active;
    }
}

// Named arguments and constructor promotion
$user = new User(
    email: 'test@example.com',
    name: 'Test User',
    status: UserStatus::Active,
);

// Match expression
$message = match ($status) {
    UserStatus::Active => 'User is active',
    UserStatus::Inactive => 'User is inactive',
    UserStatus::Pending => 'User is pending verification',
};

// Null-safe operator
$city = $user?->address?->city;

// First-class callables
$callback = $this->processUser(...);
array_map($callback, $users);
```

### Interfaces and Traits

```php
<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\User;

interface UserRepositoryInterface
{
    public function findById(string $id): ?User;

    public function findByEmail(string $email): ?User;

    /** @return list<User> */
    public function findAll(): array;

    public function save(User $user): void;

    public function delete(string $id): void;
}

// Trait for common functionality
trait TimestampableTrait
{
    private \DateTimeImmutable $createdAt;
    private ?\DateTimeImmutable $updatedAt = null;

    public function getCreatedAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }

    public function getUpdatedAt(): ?\DateTimeImmutable
    {
        return $this->updatedAt;
    }

    public function updateTimestamp(): void
    {
        $this->updatedAt = new \DateTimeImmutable();
    }
}
```

### Exceptions

```php
<?php

declare(strict_types=1);

namespace App\Exception;

abstract class DomainException extends \Exception
{
    abstract public function getErrorCode(): string;
}

final class UserNotFoundException extends DomainException
{
    public function __construct(string $id)
    {
        parent::__construct(sprintf('User with ID %s not found', $id));
    }

    public function getErrorCode(): string
    {
        return 'USER_NOT_FOUND';
    }
}

final class ValidationException extends DomainException
{
    /** @param array<string, list<string>> $errors */
    public function __construct(
        private readonly array $errors,
    ) {
        parent::__construct('Validation failed');
    }

    public function getErrorCode(): string
    {
        return 'VALIDATION_ERROR';
    }

    /** @return array<string, list<string>> */
    public function getErrors(): array
    {
        return $this->errors;
    }
}
```

### Collections

```php
<?php

declare(strict_types=1);

// Use arrays with proper type hints
/** @param list<User> $users */
function processUsers(array $users): void
{
    foreach ($users as $user) {
        // Process user
    }
}

// Use array functions
$activeUsers = array_filter(
    $users,
    static fn(User $user): bool => $user->isActive()
);

$emails = array_map(
    static fn(User $user): string => $user->getEmail(),
    $users
);

// Or use collection libraries
use Illuminate\Support\Collection;

$result = collect($users)
    ->filter(fn(User $u) => $u->isActive())
    ->map(fn(User $u) => $u->toArray())
    ->values()
    ->all();
```

### Dependency Injection

```php
<?php

declare(strict_types=1);

// Service definition with autowiring
final class OrderService
{
    public function __construct(
        private readonly OrderRepositoryInterface $orderRepository,
        private readonly UserRepositoryInterface $userRepository,
        private readonly PaymentGatewayInterface $paymentGateway,
        private readonly LoggerInterface $logger,
    ) {}

    public function createOrder(CreateOrderDTO $dto): Order
    {
        $user = $this->userRepository->findByIdOrFail($dto->userId);

        $order = new Order(
            id: Uuid::uuid4()->toString(),
            user: $user,
            items: $dto->items,
        );

        $this->orderRepository->save($order);
        $this->logger->info('Order created', ['orderId' => $order->getId()]);

        return $order;
    }
}
```

### DTOs with Validation

```php
<?php

declare(strict_types=1);

use Symfony\Component\Validator\Constraints as Assert;

final class CreateUserDTO
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Email]
        public readonly string $email,

        #[Assert\NotBlank]
        #[Assert\Length(min: 2, max: 100)]
        public readonly string $name,

        #[Assert\NotBlank]
        #[Assert\Length(min: 8)]
        public readonly string $password,
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            email: $data['email'] ?? '',
            name: $data['name'] ?? '',
            password: $data['password'] ?? '',
        );
    }
}
```

## Testing

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Service;

use App\Entity\User;
use App\Repository\UserRepositoryInterface;
use App\Service\UserService;
use PHPUnit\Framework\TestCase;

final class UserServiceTest extends TestCase
{
    private UserRepositoryInterface $repository;
    private UserService $service;

    protected function setUp(): void
    {
        $this->repository = $this->createMock(UserRepositoryInterface::class);
        $this->service = new UserService($this->repository);
    }

    public function testFindByIdReturnsUserWhenFound(): void
    {
        $user = new User('123', 'test@example.com', 'Test');

        $this->repository
            ->expects($this->once())
            ->method('findById')
            ->with('123')
            ->willReturn($user);

        $result = $this->service->findById('123');

        $this->assertSame($user, $result);
    }

    public function testFindByIdReturnsNullWhenNotFound(): void
    {
        $this->repository
            ->expects($this->once())
            ->method('findById')
            ->with('999')
            ->willReturn(null);

        $result = $this->service->findById('999');

        $this->assertNull($result);
    }
}
```

## Composer Configuration

```json
{
    "require": {
        "php": ">=8.2"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "Tests\\": "tests/"
        }
    },
    "config": {
        "sort-packages": true
    },
    "scripts": {
        "test": "phpunit",
        "lint": "php-cs-fixer fix --dry-run",
        "analyse": "phpstan analyse"
    }
}
```
