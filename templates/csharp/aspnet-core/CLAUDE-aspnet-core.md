# Claude Code Guidelines: ASP.NET Core

> **Extends:** [CLAUDE-csharp.md](../CLAUDE-csharp.md)

## ASP.NET Core Patterns

### Minimal API

```csharp
var builder = WebApplication.CreateBuilder(args);

// Configure services
builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure middleware
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseExceptionHandler();
app.UseAuthentication();
app.UseAuthorization();

// Map endpoints
app.MapUserEndpoints();

app.Run();
```

### Endpoint Groups

```csharp
public static class UserEndpoints
{
    public static void MapUserEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/users")
            .WithTags("Users")
            .RequireAuthorization();

        group.MapGet("/", GetUsers)
            .WithName("GetUsers")
            .Produces<PagedResponse<UserResponse>>();

        group.MapGet("/{id}", GetUserById)
            .WithName("GetUserById")
            .Produces<UserResponse>()
            .ProducesProblem(StatusCodes.Status404NotFound);

        group.MapPost("/", CreateUser)
            .WithName("CreateUser")
            .Produces<UserResponse>(StatusCodes.Status201Created)
            .ProducesValidationProblem()
            .AllowAnonymous();
    }

    private static async Task<IResult> GetUsers(
        [AsParameters] PaginationQuery query,
        IUserService userService,
        CancellationToken ct)
    {
        var users = await userService.GetAllAsync(query, ct);
        return Results.Ok(users);
    }

    private static async Task<IResult> GetUserById(
        string id,
        IUserService userService,
        CancellationToken ct)
    {
        var user = await userService.GetByIdAsync(id, ct);
        return user is not null
            ? Results.Ok(user)
            : Results.Problem(statusCode: 404, title: "User not found");
    }

    private static async Task<IResult> CreateUser(
        CreateUserRequest request,
        IValidator<CreateUserRequest> validator,
        IUserService userService,
        CancellationToken ct)
    {
        var validation = await validator.ValidateAsync(request, ct);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var user = await userService.CreateAsync(request, ct);
        return Results.CreatedAtRoute("GetUserById", new { id = user.Id }, user);
    }
}
```

### Middleware

```csharp
public class CorrelationIdMiddleware(RequestDelegate next)
{
    private const string CorrelationIdHeader = "X-Correlation-ID";

    public async Task InvokeAsync(HttpContext context)
    {
        var correlationId = context.Request.Headers[CorrelationIdHeader].FirstOrDefault()
            ?? Guid.NewGuid().ToString();

        context.Items["CorrelationId"] = correlationId;
        context.Response.Headers[CorrelationIdHeader] = correlationId;

        using (LogContext.PushProperty("CorrelationId", correlationId))
        {
            await next(context);
        }
    }
}

// Request logging middleware
public class RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();

        try
        {
            await next(context);
        }
        finally
        {
            stopwatch.Stop();
            logger.LogInformation(
                "{Method} {Path} responded {StatusCode} in {ElapsedMs}ms",
                context.Request.Method,
                context.Request.Path,
                context.Response.StatusCode,
                stopwatch.ElapsedMilliseconds);
        }
    }
}
```

### Authentication & Authorization

```csharp
// JWT Authentication setup
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("Admin", policy => policy.RequireRole("Admin"));
    options.AddPolicy("CanManageUsers", policy =>
        policy.RequireClaim("permission", "users:manage"));
});

// Usage in endpoints
group.MapDelete("/{id}", DeleteUser)
    .RequireAuthorization("Admin");
```

### Health Checks

```csharp
builder.Services.AddHealthChecks()
    .AddNpgSql(connectionString, name: "database")
    .AddRedis(redisConnectionString, name: "redis")
    .AddCheck<ExternalApiHealthCheck>("external-api");

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // Just check if app is running
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    ResponseWriter = UIResponseWriter.WriteHealthCheckUIResponse
});

// Custom health check
public class ExternalApiHealthCheck(IHttpClientFactory httpClientFactory) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken ct = default)
    {
        try
        {
            var client = httpClientFactory.CreateClient("ExternalApi");
            var response = await client.GetAsync("/health", ct);

            return response.IsSuccessStatusCode
                ? HealthCheckResult.Healthy()
                : HealthCheckResult.Degraded("External API returned non-success status");
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("External API is unavailable", ex);
        }
    }
}
```

### Output Caching

```csharp
builder.Services.AddOutputCache(options =>
{
    options.AddBasePolicy(builder => builder.Expire(TimeSpan.FromMinutes(5)));
    options.AddPolicy("Users", builder => builder
        .Expire(TimeSpan.FromMinutes(1))
        .Tag("users"));
});

// Usage
group.MapGet("/", GetUsers)
    .CacheOutput("Users");

// Invalidation
public async Task<User> CreateAsync(CreateUserRequest request, CancellationToken ct)
{
    var user = await repository.CreateAsync(request.ToEntity(), ct);
    await outputCacheStore.EvictByTagAsync("users", ct);
    return user;
}
```

### Rate Limiting

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

    options.AddFixedWindowLimiter("fixed", limiterOptions =>
    {
        limiterOptions.PermitLimit = 100;
        limiterOptions.Window = TimeSpan.FromMinutes(1);
    });

    options.AddSlidingWindowLimiter("sliding", limiterOptions =>
    {
        limiterOptions.PermitLimit = 100;
        limiterOptions.Window = TimeSpan.FromMinutes(1);
        limiterOptions.SegmentsPerWindow = 4;
    });
});

app.UseRateLimiter();

// Usage
group.MapPost("/", CreateUser)
    .RequireRateLimiting("fixed");
```

### Background Services

```csharp
public class OrderProcessingService(
    IServiceScopeFactory scopeFactory,
    ILogger<OrderProcessingService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                using var scope = scopeFactory.CreateScope();
                var orderService = scope.ServiceProvider.GetRequiredService<IOrderService>();

                await orderService.ProcessPendingOrdersAsync(stoppingToken);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error processing orders");
            }

            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
        }
    }
}
```

## Testing

```csharp
public class UserEndpointsTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UserEndpointsTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real services with mocks/fakes
                services.AddScoped<IUserRepository, FakeUserRepository>();
            });
        }).CreateClient();
    }

    [Fact]
    public async Task GetUsers_ReturnsOk()
    {
        var response = await _client.GetAsync("/api/users");

        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadFromJsonAsync<PagedResponse<UserResponse>>();
        Assert.NotNull(content);
    }

    [Fact]
    public async Task CreateUser_WithValidData_ReturnsCreated()
    {
        var request = new CreateUserRequest("test@example.com", "Test User");

        var response = await _client.PostAsJsonAsync("/api/users", request);

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        Assert.NotNull(response.Headers.Location);
    }

    [Fact]
    public async Task CreateUser_WithInvalidEmail_ReturnsBadRequest()
    {
        var request = new CreateUserRequest("invalid-email", "Test User");

        var response = await _client.PostAsJsonAsync("/api/users", request);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }
}
```
