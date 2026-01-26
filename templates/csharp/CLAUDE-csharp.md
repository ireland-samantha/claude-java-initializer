# Claude Code Guidelines: C# / .NET

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **.NET 8+** with C# 12
- **Nullable reference types** enabled
- Use **file-scoped namespaces**
- Use **primary constructors** where appropriate

## Project Structure

```
src/
├── MyApp.Api/                    # Web API project
│   ├── Controllers/
│   ├── Middleware/
│   ├── Program.cs
│   └── MyApp.Api.csproj
├── MyApp.Application/            # Business logic
│   ├── Services/
│   ├── Interfaces/
│   └── DTOs/
├── MyApp.Domain/                 # Domain models
│   ├── Entities/
│   ├── ValueObjects/
│   └── Exceptions/
├── MyApp.Infrastructure/         # External concerns
│   ├── Persistence/
│   ├── ExternalServices/
│   └── DependencyInjection.cs
tests/
├── MyApp.UnitTests/
└── MyApp.IntegrationTests/
```

## Code Style

### Naming Conventions

- `PascalCase` for types, methods, properties, events
- `camelCase` for parameters and local variables
- `_camelCase` for private fields
- `IPascalCase` for interfaces
- Async methods end with `Async`

### Modern C# Features

```csharp
// File-scoped namespace
namespace MyApp.Domain.Entities;

// Primary constructor with dependency injection
public class UserService(IUserRepository repository, ILogger<UserService> logger)
{
    public async Task<User?> GetByIdAsync(string id, CancellationToken ct = default)
    {
        logger.LogInformation("Getting user {UserId}", id);
        return await repository.GetByIdAsync(id, ct);
    }
}

// Records for DTOs
public record CreateUserRequest(string Email, string Name);
public record UserResponse(string Id, string Email, string Name, DateTime CreatedAt);

// Required properties
public class User
{
    public required string Id { get; init; }
    public required string Email { get; set; }
    public string? Name { get; set; }
}

// Pattern matching
public string GetStatusMessage(OrderStatus status) => status switch
{
    OrderStatus.Pending => "Order is pending",
    OrderStatus.Shipped { TrackingNumber: var tn } => $"Shipped: {tn}",
    OrderStatus.Delivered => "Order delivered",
    _ => "Unknown status"
};
```

### Dependency Injection

```csharp
// Define interfaces
public interface IUserRepository
{
    Task<User?> GetByIdAsync(string id, CancellationToken ct = default);
    Task<User> CreateAsync(User user, CancellationToken ct = default);
}

// Register services
public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddScoped<IUserService, UserService>();
        return services;
    }

    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseNpgsql(configuration.GetConnectionString("Default")));

        services.AddScoped<IUserRepository, UserRepository>();

        return services;
    }
}

// Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);
```

### Controllers

```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController(IUserService userService) : ControllerBase
{
    [HttpGet("{id}")]
    [ProducesResponseType<UserResponse>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(string id, CancellationToken ct)
    {
        var user = await userService.GetByIdAsync(id, ct);
        if (user is null)
            return NotFound();

        return Ok(user.ToResponse());
    }

    [HttpPost]
    [ProducesResponseType<UserResponse>(StatusCodes.Status201Created)]
    [ProducesResponseType<ValidationProblemDetails>(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Create(CreateUserRequest request, CancellationToken ct)
    {
        var user = await userService.CreateAsync(request, ct);
        return CreatedAtAction(nameof(GetById), new { id = user.Id }, user.ToResponse());
    }
}
```

### Error Handling

```csharp
// Domain exceptions
public abstract class DomainException(string message) : Exception(message)
{
    public abstract string Code { get; }
}

public class NotFoundException(string resource, string id)
    : DomainException($"{resource} with ID {id} not found")
{
    public override string Code => "NOT_FOUND";
}

public class ValidationException(string message, Dictionary<string, string[]> errors)
    : DomainException(message)
{
    public override string Code => "VALIDATION_ERROR";
    public Dictionary<string, string[]> Errors { get; } = errors;
}

// Global exception handler
public class GlobalExceptionHandler : IExceptionHandler
{
    private readonly ILogger<GlobalExceptionHandler> _logger;

    public GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger)
    {
        _logger = logger;
    }

    public async ValueTask<bool> TryHandleAsync(
        HttpContext context,
        Exception exception,
        CancellationToken ct)
    {
        var (statusCode, response) = exception switch
        {
            NotFoundException ex => (StatusCodes.Status404NotFound, new ProblemDetails
            {
                Status = 404,
                Title = ex.Code,
                Detail = ex.Message
            }),
            ValidationException ex => (StatusCodes.Status400BadRequest, new ValidationProblemDetails(ex.Errors)
            {
                Status = 400,
                Title = ex.Code
            }),
            _ => (StatusCodes.Status500InternalServerError, new ProblemDetails
            {
                Status = 500,
                Title = "INTERNAL_ERROR",
                Detail = "An unexpected error occurred"
            })
        };

        if (statusCode == 500)
            _logger.LogError(exception, "Unhandled exception");

        context.Response.StatusCode = statusCode;
        await context.Response.WriteAsJsonAsync(response, ct);
        return true;
    }
}
```

### Validation

```csharp
using FluentValidation;

public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty()
            .EmailAddress();

        RuleFor(x => x.Name)
            .NotEmpty()
            .MinimumLength(2)
            .MaximumLength(100);
    }
}

// Register in DI
services.AddValidatorsFromAssemblyContaining<CreateUserRequestValidator>();
```

### Entity Framework Core

```csharp
public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}

public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Email).HasMaxLength(256).IsRequired();
        builder.HasIndex(x => x.Email).IsUnique();
    }
}

// Repository implementation
public class UserRepository(AppDbContext context) : IUserRepository
{
    public async Task<User?> GetByIdAsync(string id, CancellationToken ct = default)
    {
        return await context.Users.FindAsync([id], ct);
    }

    public async Task<User> CreateAsync(User user, CancellationToken ct = default)
    {
        context.Users.Add(user);
        await context.SaveChangesAsync(ct);
        return user;
    }
}
```

### Configuration

```csharp
public class DatabaseSettings
{
    public required string ConnectionString { get; init; }
    public int MaxRetryCount { get; init; } = 3;
}

// appsettings.json binding
services.Configure<DatabaseSettings>(configuration.GetSection("Database"));

// Usage with IOptions
public class SomeService(IOptions<DatabaseSettings> options)
{
    private readonly DatabaseSettings _settings = options.Value;
}
```

## Testing

```csharp
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _repositoryMock = new();
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _sut = new UserService(_repositoryMock.Object, NullLogger<UserService>.Instance);
    }

    [Fact]
    public async Task GetByIdAsync_ReturnsUser_WhenUserExists()
    {
        // Arrange
        var user = new User { Id = "123", Email = "test@example.com" };
        _repositoryMock
            .Setup(x => x.GetByIdAsync("123", It.IsAny<CancellationToken>()))
            .ReturnsAsync(user);

        // Act
        var result = await _sut.GetByIdAsync("123");

        // Assert
        Assert.NotNull(result);
        Assert.Equal("test@example.com", result.Email);
    }

    [Fact]
    public async Task GetByIdAsync_ReturnsNull_WhenUserDoesNotExist()
    {
        // Arrange
        _repositoryMock
            .Setup(x => x.GetByIdAsync("999", It.IsAny<CancellationToken>()))
            .ReturnsAsync((User?)null);

        // Act
        var result = await _sut.GetByIdAsync("999");

        // Assert
        Assert.Null(result);
    }
}
```
