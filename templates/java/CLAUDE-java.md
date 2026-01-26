# Claude Code Guidelines: Java

> **Extends:** [CLAUDE-base.md](../CLAUDE-base.md)

## Language Standards

- **Java 21+** for modern features (virtual threads, pattern matching, records)
- Use **Maven** or **Gradle** for build
- Follow **Google Java Style Guide**
- Use **Checkstyle** and **SpotBugs** for code quality

## Project Structure

```
project/
├── pom.xml (or build.gradle)
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/
│   │   │       ├── Application.java
│   │   │       ├── config/
│   │   │       ├── domain/
│   │   │       ├── service/
│   │   │       ├── repository/
│   │   │       ├── controller/
│   │   │       ├── dto/
│   │   │       └── exception/
│   │   └── resources/
│   └── test/
│       └── java/
└── target/ (or build/)
```

## Code Style

### Naming Conventions

- `PascalCase` for classes, interfaces, enums, records
- `camelCase` for methods, fields, local variables
- `SCREAMING_SNAKE_CASE` for constants
- `lowercase` for packages

### Modern Java Features (Java 21+)

```java
// Records for immutable data
public record User(
    String id,
    String email,
    String name,
    Instant createdAt
) {
    public User {
        Objects.requireNonNull(id);
        Objects.requireNonNull(email);
    }

    public static User create(String email, String name) {
        return new User(UUID.randomUUID().toString(), email, name, Instant.now());
    }
}

// Sealed classes for restricted hierarchies
public sealed interface Result<T> permits Success, Failure {
    <R> Result<R> map(Function<T, R> mapper);
    <R> Result<R> flatMap(Function<T, Result<R>> mapper);
}

public record Success<T>(T value) implements Result<T> {
    @Override
    public <R> Result<R> map(Function<T, R> mapper) {
        return new Success<>(mapper.apply(value));
    }

    @Override
    public <R> Result<R> flatMap(Function<T, Result<R>> mapper) {
        return mapper.apply(value);
    }
}

public record Failure<T>(AppError error) implements Result<T> {
    @Override
    public <R> Result<R> map(Function<T, R> mapper) {
        return new Failure<>(error);
    }

    @Override
    public <R> Result<R> flatMap(Function<T, Result<R>> mapper) {
        return new Failure<>(error);
    }
}

// Pattern matching with switch
public String formatUser(Object obj) {
    return switch (obj) {
        case User user when user.name() != null -> user.name();
        case User user -> user.email();
        case String s -> s;
        case null -> "Unknown";
        default -> obj.toString();
    };
}

// Virtual threads (Project Loom)
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    var futures = userIds.stream()
        .map(id -> executor.submit(() -> fetchUser(id)))
        .toList();

    var users = futures.stream()
        .map(this::getResult)
        .toList();
}
```

### Optional Usage

```java
// Use Optional for nullable returns
public Optional<User> findById(String id) {
    return Optional.ofNullable(userMap.get(id));
}

// Chain operations
public String getUserEmail(String id) {
    return findById(id)
        .map(User::email)
        .orElse("unknown@example.com");
}

// OrElseThrow for required values
public User getById(String id) {
    return findById(id)
        .orElseThrow(() -> new NotFoundException("User", id));
}

// Never use Optional as field or parameter
// Bad
private Optional<String> name;
public void setUser(Optional<User> user);

// Good
private String name; // nullable
public void setUser(User user); // can be null
```

### Streams

```java
// Filter, map, collect
var activeEmails = users.stream()
    .filter(User::isActive)
    .map(User::email)
    .collect(Collectors.toList());

// Grouping
var usersByRole = users.stream()
    .collect(Collectors.groupingBy(User::role));

// FlatMap for nested collections
var allTags = posts.stream()
    .flatMap(post -> post.tags().stream())
    .distinct()
    .toList();

// Reduce
var totalAmount = orders.stream()
    .map(Order::amount)
    .reduce(BigDecimal.ZERO, BigDecimal::add);
```

### Interfaces and Implementations

```java
// Interface with documentation
public interface UserRepository {
    /**
     * Find user by ID.
     *
     * @param id the user ID
     * @return the user if found, empty otherwise
     */
    Optional<User> findById(String id);

    /**
     * Find all users.
     *
     * @return list of all users
     */
    List<User> findAll();

    /**
     * Save a user.
     *
     * @param user the user to save
     * @return the saved user
     */
    User save(User user);

    /**
     * Delete a user by ID.
     *
     * @param id the user ID
     */
    void deleteById(String id);
}

// Implementation
public class PostgresUserRepository implements UserRepository {
    private final DataSource dataSource;

    public PostgresUserRepository(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Optional<User> findById(String id) {
        try (var conn = dataSource.getConnection();
             var stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?")) {
            stmt.setString(1, id);
            try (var rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return Optional.of(mapRow(rs));
                }
                return Optional.empty();
            }
        } catch (SQLException e) {
            throw new RepositoryException("Failed to find user", e);
        }
    }
}
```

### Exception Handling

```java
// Custom exception hierarchy
public abstract class AppException extends RuntimeException {
    protected AppException(String message) {
        super(message);
    }

    protected AppException(String message, Throwable cause) {
        super(message, cause);
    }

    public abstract String getCode();
}

public class NotFoundException extends AppException {
    private final String resource;
    private final String id;

    public NotFoundException(String resource, String id) {
        super(String.format("%s with ID %s not found", resource, id));
        this.resource = resource;
        this.id = id;
    }

    @Override
    public String getCode() {
        return "NOT_FOUND";
    }
}

public class ValidationException extends AppException {
    private final Map<String, List<String>> errors;

    public ValidationException(Map<String, List<String>> errors) {
        super("Validation failed");
        this.errors = errors;
    }

    @Override
    public String getCode() {
        return "VALIDATION_ERROR";
    }

    public Map<String, List<String>> getErrors() {
        return errors;
    }
}
```

### Dependency Injection (manual)

```java
public class Container {
    private static Container instance;

    private DataSource dataSource;
    private UserRepository userRepository;
    private UserService userService;

    private Container() {}

    public static synchronized Container getInstance() {
        if (instance == null) {
            instance = new Container();
            instance.initialize();
        }
        return instance;
    }

    private void initialize() {
        dataSource = createDataSource();
        userRepository = new PostgresUserRepository(dataSource);
        userService = new UserService(userRepository);
    }

    public UserService getUserService() {
        return userService;
    }

    private DataSource createDataSource() {
        var config = new HikariConfig();
        config.setJdbcUrl(System.getenv("DATABASE_URL"));
        config.setMaximumPoolSize(10);
        return new HikariDataSource(config);
    }
}
```

### Builder Pattern

```java
public class UserBuilder {
    private String email;
    private String name;
    private String password;
    private UserRole role = UserRole.USER;

    public UserBuilder email(String email) {
        this.email = email;
        return this;
    }

    public UserBuilder name(String name) {
        this.name = name;
        return this;
    }

    public UserBuilder password(String password) {
        this.password = password;
        return this;
    }

    public UserBuilder role(UserRole role) {
        this.role = role;
        return this;
    }

    public User build() {
        Objects.requireNonNull(email, "Email is required");
        Objects.requireNonNull(name, "Name is required");

        return new User(
            UUID.randomUUID().toString(),
            email,
            name,
            password,
            role,
            Instant.now()
        );
    }
}

// Usage
var user = new UserBuilder()
    .email("test@example.com")
    .name("Test User")
    .password("secret")
    .role(UserRole.ADMIN)
    .build();
```

## Testing (JUnit 5)

```java
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class UserServiceTest {
    private UserRepository repository;
    private UserService service;

    @BeforeEach
    void setUp() {
        repository = mock(UserRepository.class);
        service = new UserService(repository);
    }

    @Test
    @DisplayName("getById returns user when found")
    void getById_ReturnsUser_WhenFound() {
        // Given
        var user = new User("123", "test@example.com", "Test", Instant.now());
        when(repository.findById("123")).thenReturn(Optional.of(user));

        // When
        var result = service.getById("123");

        // Then
        assertEquals("test@example.com", result.email());
        verify(repository).findById("123");
    }

    @Test
    @DisplayName("getById throws NotFoundException when not found")
    void getById_ThrowsNotFound_WhenNotFound() {
        // Given
        when(repository.findById("999")).thenReturn(Optional.empty());

        // When/Then
        var exception = assertThrows(
            NotFoundException.class,
            () -> service.getById("999")
        );

        assertEquals("User with ID 999 not found", exception.getMessage());
    }

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "invalid-email"})
    @DisplayName("createUser throws validation error for invalid emails")
    void createUser_ThrowsValidation_ForInvalidEmail(String email) {
        var request = new CreateUserRequest(email, "Test");

        assertThrows(
            ValidationException.class,
            () -> service.create(request)
        );
    }

    @Nested
    @DisplayName("when user exists")
    class WhenUserExists {
        private User existingUser;

        @BeforeEach
        void setUp() {
            existingUser = new User("123", "existing@example.com", "Existing", Instant.now());
            when(repository.findById("123")).thenReturn(Optional.of(existingUser));
        }

        @Test
        @DisplayName("update modifies user")
        void update_ModifiesUser() {
            var request = new UpdateUserRequest("New Name");

            var result = service.update("123", request);

            assertEquals("New Name", result.name());
        }
    }
}
```

## Maven Configuration

```xml
<project>
    <properties>
        <java.version>21</java.version>
        <maven.compiler.source>${java.version}</maven.compiler.source>
        <maven.compiler.target>${java.version}</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.1</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <version>5.8.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```
